"""
Kometizarr Web UI - FastAPI Backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add kometizarr to path
sys.path.insert(0, '/app/kometizarr')

from src.rating_overlay.plex_poster_manager import PlexPosterManager
from src.collection_manager.manager import CollectionManager
from src.utils.logger import setup_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kometizarr API", version="1.2.1")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections for live progress
active_connections: List[WebSocket] = []

# Processing state (sent over WebSocket - must be JSON serializable)
processing_state = {
    "is_processing": False,
    "current_library": None,
    "progress": 0,
    "total": 0,
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "current_item": None,
    "stop_requested": False,
    "force_mode": False,
}

# Processing start time (stored separately - not sent over WebSocket)
processing_start_time = None

# Webhook item queue — serializes single-item processing requests
webhook_queue: asyncio.Queue = asyncio.Queue()

# Restore state (sent over WebSocket - must be JSON serializable)
restore_state = {
    "is_restoring": False,
    "current_library": None,
    "progress": 0,
    "total": 0,
    "restored": 0,
    "failed": 0,
    "skipped": 0,
    "current_item": None,
    "stop_requested": False,
}

# Restore start time (stored separately - not sent over WebSocket)
restore_start_time = None


class ProcessRequest(BaseModel):
    library_name: str
    position: str = "northwest"  # Legacy unified badge mode
    badge_position: Optional[Dict[str, float]] = None  # Legacy: free positioning for unified badge {x: %, y: %}
    badge_positions: Optional[Dict[str, Dict[str, float]]] = None  # New: individual badge positions {'tmdb': {'x': 5, 'y': 5}, ...}
    force: bool = False
    limit: Optional[int] = None
    rating_sources: Optional[Dict[str, bool]] = None  # Which ratings to show
    badge_style: Optional[Dict[str, Any]] = None  # Badge styling options
    rating_key: Optional[str] = None  # If set, process only this specific Plex item


class ProcessBatchRequest(BaseModel):
    library_names: List[str]
    position: str = "northwest"
    badge_positions: Optional[Dict[str, Dict[str, float]]] = None
    force: bool = False
    rating_sources: Optional[Dict[str, bool]] = None
    badge_style: Optional[Dict[str, Any]] = None


class LibraryStats(BaseModel):
    library_name: str
    total_items: int
    processed_items: int
    success_rate: float


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "app": "Kometizarr API", "version": "1.2.1"}


@app.get("/api/libraries")
async def get_libraries():
    """Get all Plex libraries - optimized for speed"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL', 'http://192.168.1.20:32400')
        plex_token = os.getenv('PLEX_TOKEN')

        if not plex_token:
            return {"error": "PLEX_TOKEN not configured"}

        server = PlexServer(plex_url, plex_token)
        libraries = []

        for lib in server.library.sections():
            libraries.append({
                "name": lib.title,
                "type": lib.type,
                # Use totalSize instead of len(all()) - avoids fetching all items
                "count": lib.totalSize if hasattr(lib, 'totalSize') else 0
            })

        return {"libraries": libraries}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/library/{library_name}/stats")
async def get_library_stats(library_name: str):
    """Get statistics for a library"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)

        # Use totalSize for fast count instead of fetching all items
        total = library.totalSize

        # Check how many have backups (processed) - use fast glob count
        backup_dir = f"/backups/{library_name}"
        processed = 0
        if os.path.exists(backup_dir):
            import glob
            processed = len(glob.glob(f"{backup_dir}/*"))

        success_rate = (processed / total * 100) if total > 0 else 0

        return {
            "library_name": library_name,
            "total_items": total,
            "processed_items": processed,
            "success_rate": round(success_rate, 1)
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/process")
async def start_processing(request: ProcessRequest):
    """Start overlay processing"""
    global processing_state

    if processing_state["is_processing"]:
        return {"error": "Processing already in progress"}

    # Start background task
    asyncio.create_task(process_library_background(request))

    return {"status": "started", "library": request.library_name}


@app.post("/api/process-batch")
async def start_processing_batch(request: ProcessBatchRequest):
    """Process multiple libraries sequentially."""
    if processing_state["is_processing"]:
        return {"error": "Processing already in progress"}
    if not request.library_names:
        return {"error": "No libraries specified"}

    async def run_batch():
        for lib_name in request.library_names:
            single = ProcessRequest(
                library_name=lib_name,
                position=request.position,
                badge_positions=request.badge_positions,
                force=request.force,
                rating_sources=request.rating_sources,
                badge_style=request.badge_style,
            )
            await process_library_background(single)

    asyncio.create_task(run_batch())
    return {"status": "started", "libraries": request.library_names}


@app.post("/api/restore")
async def restore_originals(request: ProcessRequest):
    """Start restoring original posters from backups"""
    global restore_state

    if restore_state["is_restoring"]:
        return {"error": "Restore already in progress"}

    # Start background task
    asyncio.create_task(restore_library_background(request))

    return {"status": "started", "library": request.library_name}


@app.post("/api/stop")
async def stop_processing():
    """Request graceful stop of current processing operation"""
    global processing_state

    if processing_state["is_processing"]:
        processing_state["stop_requested"] = True
        return {"status": "stopping", "message": "Processing will stop after current item"}

    return {"status": "idle", "message": "No processing in progress"}


@app.post("/api/restore/stop")
async def stop_restore():
    """Request graceful stop of current restore operation"""
    global restore_state

    if restore_state["is_restoring"]:
        restore_state["stop_requested"] = True
        return {"status": "stopping", "message": "Restore will stop after current item"}

    return {"status": "idle", "message": "No restore in progress"}


async def restore_library_background(request: ProcessRequest):
    """Background task for restoring library"""
    global restore_state, restore_start_time

    try:
        # Reset restore state for new run
        restore_state["is_restoring"] = True
        restore_state["current_library"] = request.library_name
        restore_state["progress"] = 0
        restore_state["total"] = 0
        restore_state["restored"] = 0
        restore_state["failed"] = 0
        restore_state["skipped"] = 0
        restore_state["current_item"] = None
        restore_start_time = datetime.now()

        from plexapi.server import PlexServer
        from src.rating_overlay.backup_manager import PosterBackupManager

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(request.library_name)

        backup_manager = PosterBackupManager(backup_dir='/backups')

        # Get all items
        all_items = library.all()
        if request.limit:
            all_items = all_items[:request.limit]

        restore_state["total"] = len(all_items)

        logger.info(f"🔄 Restore started: {request.library_name} ({len(all_items)} items)")

        # Restore each item
        for i, item in enumerate(all_items, 1):
            # Check if stop was requested
            if restore_state["stop_requested"]:
                logger.info(f"Stop requested - stopping restore at item {i}/{restore_state['total']}")
                break

            restore_state["progress"] = i
            restore_state["current_item"] = item.title

            # Skip if no backup exists
            if not backup_manager.has_backup(request.library_name, item.title):
                restore_state["skipped"] += 1
            # Skip if already showing original (no overlay applied)
            elif not backup_manager.has_overlay(request.library_name, item.title):
                restore_state["skipped"] += 1
            # Has backup AND has overlay, proceed with restore
            else:
                if backup_manager.restore_original(request.library_name, item.title, item):
                    restore_state["restored"] += 1
                else:
                    restore_state["failed"] += 1

            # Broadcast progress to all WebSocket connections
            await broadcast_restore_progress()

            # Rate limiting
            await asyncio.sleep(0.1)

        restore_state["is_restoring"] = False
        restore_state["stop_requested"] = False

        # Calculate duration and stats
        duration = datetime.now() - restore_start_time
        duration_seconds = duration.total_seconds()
        duration_str = f"{int(duration_seconds // 3600)}h {int((duration_seconds % 3600) // 60)}m {int(duration_seconds % 60)}s" if duration_seconds >= 3600 else f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"

        total = restore_state["total"]
        restored = restore_state["restored"]
        failed = restore_state["failed"]
        skipped = restore_state["skipped"]

        restored_rate = (restored / total * 100) if total > 0 else 0
        failed_rate = (failed / total * 100) if total > 0 else 0
        skipped_rate = (skipped / total * 100) if total > 0 else 0
        rate_per_min = (total / (duration_seconds / 60)) if duration_seconds > 0 else 0

        # Log fancy summary
        logger.info("=" * 60)
        logger.info(f"✅ Restore Completed: {request.library_name}")
        logger.info("-" * 60)
        logger.info(f"Total Items:     {total}")
        logger.info(f"Restored:        {restored} ({restored_rate:.1f}%)")
        logger.info(f"Failed:          {failed} ({failed_rate:.1f}%)")
        logger.info(f"Skipped:         {skipped} ({skipped_rate:.1f}%)")
        logger.info(f"Duration:        {duration_str}")
        logger.info(f"Rate:            {rate_per_min:.1f} items/min")
        logger.info("=" * 60)

        await broadcast_restore_progress()  # Final update

    except Exception as e:
        restore_state["is_restoring"] = False
        restore_state["stop_requested"] = False
        restore_state["error"] = str(e)
        logger.error(f"❌ Restore failed: {request.library_name} - Error: {e}")
        await broadcast_restore_progress()


async def process_library_background(request: ProcessRequest):
    """Background task for processing library"""
    global processing_state, processing_start_time

    try:
        # Reset processing state for new run
        processing_state["is_processing"] = True
        processing_state["current_library"] = request.library_name
        processing_state["progress"] = 0
        processing_state["total"] = 0
        processing_state["success"] = 0
        processing_state["failed"] = 0
        processing_state["skipped"] = 0
        processing_state["current_item"] = None
        processing_state["force_mode"] = request.force
        processing_start_time = datetime.now()

        # Initialize manager
        manager = PlexPosterManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            tmdb_api_key=os.getenv('TMDB_API_KEY'),
            omdb_api_key=os.getenv('OMDB_API_KEY'),
            mdblist_api_key=os.getenv('MDBLIST_API_KEY'),
            backup_dir='/backups',
            dry_run=False,
            rating_sources=request.rating_sources,
            badge_style=request.badge_style  # Pass badge styling options
        )

        if request.rating_key:
            all_items = [manager.library.fetchItem(int(request.rating_key))]
        else:
            all_items = manager.library.all()
            if request.limit:
                all_items = all_items[:request.limit]

        processing_state["total"] = len(all_items)

        logger.info(f"🎬 Processing started: {request.library_name} ({len(all_items)} items)")

        # Process each item
        for i, item in enumerate(all_items, 1):
            # Check if stop was requested
            if processing_state["stop_requested"]:
                logger.info(f"Stop requested - stopping processing at item {i}/{processing_state['total']}")
                break

            processing_state["progress"] = i
            processing_state["current_item"] = item.title

            # Determine positioning mode
            # 1. If badge_positions provided, use 4-badge mode
            # 2. Otherwise, use legacy unified badge with position (string or dict)
            if request.badge_positions:
                result = manager.process_movie(
                    item,
                    position=request.position,  # Not used in 4-badge mode, but kept for compat
                    force=request.force,
                    badge_positions=request.badge_positions
                )
            else:
                # Legacy unified badge mode
                position_param = request.badge_position if request.badge_position else request.position
                result = manager.process_movie(item, position=position_param, force=request.force)

            # Handle three-state return: True=success, None=skip, False=fail
            if result is None:
                processing_state["skipped"] += 1
            elif result:
                processing_state["success"] += 1
            else:
                processing_state["failed"] += 1

            # Broadcast progress to all WebSocket connections
            await broadcast_progress()

            # Rate limiting
            await asyncio.sleep(0.3)

        processing_state["is_processing"] = False
        processing_state["stop_requested"] = False

        # Calculate duration and stats
        duration = datetime.now() - processing_start_time
        duration_seconds = duration.total_seconds()
        duration_str = f"{int(duration_seconds // 3600)}h {int((duration_seconds % 3600) // 60)}m {int(duration_seconds % 60)}s" if duration_seconds >= 3600 else f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"

        total = processing_state["total"]
        success = processing_state["success"]
        failed = processing_state["failed"]
        skipped = processing_state["skipped"]

        success_rate = (success / total * 100) if total > 0 else 0
        failed_rate = (failed / total * 100) if total > 0 else 0
        skipped_rate = (skipped / total * 100) if total > 0 else 0
        rate_per_min = (total / (duration_seconds / 60)) if duration_seconds > 0 else 0

        # Log fancy summary
        logger.info("=" * 60)
        logger.info(f"✅ Processing Completed: {request.library_name}")
        logger.info("-" * 60)
        logger.info(f"Total Items:     {total}")
        logger.info(f"Success:         {success} ({success_rate:.1f}%)")
        logger.info(f"Failed:          {failed} ({failed_rate:.1f}%)")
        logger.info(f"Skipped:         {skipped} ({skipped_rate:.1f}%)")
        logger.info(f"Duration:        {duration_str}")
        logger.info(f"Rate:            {rate_per_min:.1f} items/min")
        logger.info("=" * 60)

        await broadcast_progress()  # Final update

    except Exception as e:
        import traceback
        processing_state["is_processing"] = False
        processing_state["stop_requested"] = False
        processing_state["error"] = str(e)
        logger.error(f"❌ Processing failed: {request.library_name} - Error: {e}")
        logger.error(traceback.format_exc())  # Print full traceback
        await broadcast_progress()


@app.get("/api/status")
async def get_status():
    """Get current processing status"""
    return processing_state


class PreviewRequest(BaseModel):
    library_name: str
    badge_positions: Optional[Dict[str, Dict[str, float]]] = None
    rating_sources: Optional[Dict[str, bool]] = None
    badge_style: Optional[Dict[str, Any]] = None
    count: int = 3


@app.post("/api/preview")
async def preview_posters(request: PreviewRequest):
    """
    Render overlaid posters for a random sample of library items.
    Returns base64 images — no Plex upload, no backup.
    """
    import random
    import base64
    import requests as req
    from pathlib import Path

    try:
        manager = PlexPosterManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            tmdb_api_key=os.getenv('TMDB_API_KEY'),
            omdb_api_key=os.getenv('OMDB_API_KEY'),
            mdblist_api_key=os.getenv('MDBLIST_API_KEY'),
            backup_dir='/backups',
            dry_run=False,
            rating_sources=request.rating_sources,
            badge_style=request.badge_style,
        )

        all_items = manager.library.all()
        sample = random.sample(all_items, min(request.count, len(all_items)))

        results = []
        for item in sample:
            try:
                # Fetch ratings using same priority order as process_movie
                plex_ratings = manager._extract_plex_ratings(item)
                ratings = {}
                for key in ('tmdb', 'imdb', 'rt_critic', 'rt_audience'):
                    if key in plex_ratings:
                        ratings[key] = plex_ratings[key]

                if request.rating_sources:
                    ratings = {k: v for k, v in ratings.items() if request.rating_sources.get(k, True)}

                if not ratings or all(v == 0 for v in ratings.values()):
                    continue

                # Use existing backup poster if available, otherwise download
                poster_path = manager.backup_manager.get_original_poster(manager.library_name, item.title)

                if not poster_path:
                    poster_url = item.posterUrl
                    if not poster_url:
                        continue
                    response = req.get(
                        poster_url,
                        headers={'X-Plex-Token': manager.plex_token},
                        timeout=15
                    )
                    if response.status_code != 200:
                        continue
                    tmp_src = Path(f'/tmp/kometizarr_prev_src_{item.ratingKey}.jpg')
                    tmp_src.write_bytes(response.content)
                    poster_path = str(tmp_src)

                # Apply overlay (no upload)
                output_path = f'/tmp/kometizarr_prev_{item.ratingKey}.jpg'
                manager.multi_rating_badge.apply_to_poster(
                    poster_path=str(poster_path),
                    ratings=ratings,
                    output_path=output_path,
                    badge_style=manager.badge_style,
                    badge_positions=request.badge_positions,
                )

                with open(output_path, 'rb') as f:
                    image_b64 = base64.b64encode(f.read()).decode()

                results.append({
                    'title': item.title,
                    'year': getattr(item, 'year', None),
                    'ratings': ratings,
                    'image': image_b64,
                })

            except Exception as e:
                logger.warning(f"Preview skipped for {item.title}: {e}")
                continue

        return {'previews': results}

    except Exception as e:
        logger.error(f"Preview failed: {e}")
        return {'error': str(e), 'previews': []}


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for live progress updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial state
        await websocket.send_json(processing_state)

        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            # Client can send ping to keep alive
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_progress():
    """Broadcast progress to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(processing_state)
        except:
            active_connections.remove(connection)


async def broadcast_restore_progress():
    """Broadcast restore progress to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(restore_state)
        except:
            active_connections.remove(connection)


@app.get("/api/restore/status")
async def get_restore_status():
    """Get current restore status"""
    return restore_state


# Collection Management Endpoints

@app.get("/api/collections")
async def get_collections(library_name: str):
    """Get all collections in a library - optimized for speed"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)

        collections = []
        # Use search() instead of collections() - much faster as it doesn't load full metadata
        for collection in library.search(libtype='collection'):
            collections.append({
                "title": collection.title,
                # Use childCount instead of len(items()) - avoids fetching all items
                "count": collection.childCount if hasattr(collection, 'childCount') else 0,
                "summary": collection.summary if hasattr(collection, 'summary') else ""
            })

        return {"collections": collections}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/collections/{collection_title}/items")
async def get_collection_items(collection_title: str, library_name: str):
    """Get first 10 items in a collection for preview"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)

        # Get the collection
        collection = library.collection(collection_title)

        # Get total count
        total_count = collection.childCount if hasattr(collection, 'childCount') else 0

        # Get just first 10 items for preview
        items = []
        limit = 10

        for i, item in enumerate(collection.items()):
            if i >= limit:
                break
            items.append({
                "title": item.title,
                "year": item.year if hasattr(item, 'year') else None,
                "rating": round(item.rating, 1) if hasattr(item, 'rating') and item.rating else None
            })

        return {
            "items": items,
            "total": total_count,
            "showing": len(items),
            "has_more": total_count > len(items)
        }
    except Exception as e:
        return {"error": str(e)}


class DecadeCollectionRequest(BaseModel):
    library_name: str
    decades: List[Dict]  # [{"title": "1980s Movies", "start": 1980, "end": 1989}, ...]


class StudioCollectionRequest(BaseModel):
    library_name: str
    studios: List[Dict]  # [{"title": "Marvel", "studios": ["Marvel Studios"]}, ...]


class KeywordCollectionRequest(BaseModel):
    library_name: str
    keywords: List[Dict]  # [{"title": "DC Universe", "keywords": ["dc comics", "batman"]}, ...]


@app.post("/api/collections/decade")
async def create_decade_collections(request: DecadeCollectionRequest):
    """Create decade collections"""
    try:
        manager = CollectionManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            dry_run=False
        )

        collections = manager.create_decade_collections(request.decades)

        return {
            "status": "success",
            "created": len(collections),
            "collections": [c.title for c in collections]
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/collections/studio")
async def create_studio_collections(request: StudioCollectionRequest):
    """Create studio collections"""
    try:
        manager = CollectionManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            dry_run=False
        )

        collections = manager.create_studio_collections(request.studios)

        return {
            "status": "success",
            "created": len(collections),
            "collections": [c.title for c in collections]
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/collections/keyword")
async def create_keyword_collections(request: KeywordCollectionRequest):
    """Create keyword collections"""
    try:
        manager = CollectionManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            tmdb_api_key=os.getenv('TMDB_API_KEY'),
            dry_run=False
        )

        collections = manager.create_keyword_collections(request.keywords)

        return {
            "status": "success",
            "created": len(collections),
            "collections": [c.title for c in collections]
        }
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/collections/{collection_title}")
async def delete_collection(collection_title: str, library_name: str):
    """Delete a collection"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)

        # Get the collection
        collection = library.collection(collection_title)

        # Delete it
        collection.delete()

        return {"status": "success", "message": f"Deleted collection: {collection_title}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/library/{library_name}/studios")
async def get_library_studios(library_name: str):
    """Get all unique studios/networks in a library (for debugging)"""
    try:
        from plexapi.server import PlexServer

        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')

        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)

        # Get all items
        all_items = library.all()

        # For TV shows, use 'network' field; for movies, use 'studio' field
        is_tv = library.type == 'show'
        field_name = 'network' if is_tv else 'studio'

        # Collect all unique studios/networks
        studios = {}
        for item in all_items:
            if is_tv:
                # TV shows - check network field
                if hasattr(item, 'network') and item.network:
                    value = item.network
                    if value not in studios:
                        studios[value] = 0
                    studios[value] += 1
            else:
                # Movies - check studio field
                if hasattr(item, 'studio') and item.studio:
                    value = item.studio
                    if value not in studios:
                        studios[value] = 0
                    studios[value] += 1

        # Sort by count descending
        sorted_studios = sorted(studios.items(), key=lambda x: x[1], reverse=True)

        return {
            "library": library_name,
            "field": field_name,
            "total_items": len(all_items),
            "studios": [{"name": name, "count": count} for name, count in sorted_studios]
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Settings, Fresh Posters, Delete Backups, Cron, Webhook
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

SETTINGS_PATH = Path('/app/kometizarr/data/settings.json')

scheduler = AsyncIOScheduler()

fresh_posters_state = {
    "is_running": False,
    "library": None,
    "progress": 0,
    "total": 0,
    "restored": 0,
    "failed": 0,
    "current_item": None,
}


def _load_settings() -> dict:
    defaults = {
        "cron_normal": {"enabled": False, "libraries": [], "schedule": "0 3 * * *"},
        "cron_force":  {"enabled": False, "libraries": [], "schedule": "0 3 * * 0"},
        "webhook": {"enabled": False, "libraries": []},
    }
    if not SETTINGS_PATH.exists():
        return defaults
    data = json.loads(SETTINGS_PATH.read_text())
    # Migrate old single-library format
    for key in ("cron_normal", "cron_force"):
        block = data.get(key, {})
        if "library" in block and "libraries" not in block:
            old = block.pop("library")
            block["libraries"] = [] if not old or old == "__all__" else [old]
    if "webhook" in data and "library" in data["webhook"] and "libraries" not in data["webhook"]:
        old = data["webhook"].pop("library")
        data["webhook"]["enabled"] = bool(old)
        data["webhook"]["libraries"] = [] if not old or old == "__all__" else [old]
    return data


def _save_settings(settings: dict):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))


def _add_cron_job(scheduler, job_id: str, schedule: str, libraries: list, force: bool):
    parts = schedule.split()
    if len(parts) != 5:
        return
    trigger = CronTrigger(
        minute=parts[0], hour=parts[1],
        day=parts[2], month=parts[3], day_of_week=parts[4]
    )
    scheduler.add_job(
        _cron_run_libraries,
        trigger=trigger,
        args=[libraries, force],
        id=job_id,
        replace_existing=True,
    )
    label = ", ".join(libraries) if libraries else "all"
    logger.info(f"Cron [{job_id}] scheduled: {schedule} for [{label}] (force={force})")


def _reschedule_cron(settings: dict):
    """Apply both cron configs to the scheduler."""
    scheduler.remove_all_jobs()
    for key, force in [("cron_normal", False), ("cron_force", True)]:
        cron = settings.get(key, {})
        if cron.get("enabled") and cron.get("schedule"):
            try:
                _add_cron_job(scheduler, key, cron["schedule"], cron.get("libraries", []), force)
            except Exception as e:
                logger.error(f"Failed to schedule {key}: {e}")


async def _run_libraries_sequentially(libraries: list, force: bool):
    """Fetch all Plex library names if list is empty, then process each sequentially."""
    if not libraries:
        try:
            from plexapi.server import PlexServer
            server = PlexServer(os.getenv('PLEX_URL'), os.getenv('PLEX_TOKEN'))
            libraries = [lib.title for lib in server.library.sections()]
        except Exception as e:
            logger.error(f"Cron: failed to fetch library list: {e}")
            return
    settings = _load_settings()
    badge_style = settings.get("badge_style")
    badge_positions = settings.get("badge_positions")
    rating_sources = settings.get("rating_sources")
    label = "force" if force else "normal"
    for lib_name in libraries:
        logger.info(f"Cron ({label}): processing {lib_name}")
        await process_library_background(ProcessRequest(
            library_name=lib_name,
            force=force,
            badge_style=badge_style,
            badge_positions=badge_positions,
            rating_sources=rating_sources,
        ))


async def _cron_run_libraries(libraries: list, force: bool = False):
    """Called by APScheduler — starts processing if not already running."""
    if processing_state["is_processing"]:
        logger.info("Cron: skipping, processing already in progress")
        return
    asyncio.create_task(_run_libraries_sequentially(libraries, force))


async def _webhook_queue_worker():
    """Processes webhook-queued items one at a time, waiting if processing is busy."""
    while True:
        library_name, rating_key, item_title = await webhook_queue.get()
        try:
            # Wait if processing is already running (e.g. cron or manual run)
            while processing_state["is_processing"]:
                await asyncio.sleep(2)
            # Load current badge settings so webhook uses same styling as the UI
            settings = _load_settings()
            badge_style = settings.get("badge_style")
            badge_positions = settings.get("badge_positions")
            rating_sources = settings.get("rating_sources")
            logger.info(f"Webhook queue: processing {library_name} / {item_title} (key={rating_key})")
            await process_library_background(ProcessRequest(
                library_name=library_name,
                rating_key=rating_key,
                badge_style=badge_style,
                badge_positions=badge_positions,
                rating_sources=rating_sources,
            ))
        except Exception as e:
            logger.error(f"Webhook queue worker error: {e}")
        finally:
            webhook_queue.task_done()


DEFAULT_BADGE_POSITIONS = {
    "tmdb":        {"x": 2,  "y": 2},
    "imdb":        {"x": 70, "y": 2},
    "rt_critic":   {"x": 2,  "y": 78},
    "rt_audience": {"x": 70, "y": 78},
}

DEFAULT_BADGE_STYLE = {
    "individual_badge_size": 12,
    "font_size_multiplier": 1.0,
    "logo_size_multiplier": 1.0,
    "rating_color": "#FFD700",
    "background_opacity": 128,
    "font_family": "DejaVu Sans Bold",
}

DEFAULT_RATING_SOURCES = {
    "tmdb": True, "imdb": True, "rt_critic": True, "rt_audience": True,
}


@app.on_event("startup")
async def startup_event():
    scheduler.start()
    settings = _load_settings()
    # Seed badge defaults so webhook/cron work out of the box without UI interaction
    changed = False
    if "badge_positions" not in settings:
        settings["badge_positions"] = DEFAULT_BADGE_POSITIONS
        changed = True
    if "badge_style" not in settings:
        settings["badge_style"] = DEFAULT_BADGE_STYLE
        changed = True
    if "rating_sources" not in settings:
        settings["rating_sources"] = DEFAULT_RATING_SOURCES
        changed = True
    if changed:
        _save_settings(settings)
    _reschedule_cron(settings)
    asyncio.create_task(_webhook_queue_worker())


@app.get("/api/settings")
async def get_settings():
    settings = _load_settings()
    for key in ("cron_normal", "cron_force"):
        job = scheduler.get_job(key)
        settings.setdefault(key, {})["next_run"] = job.next_run_time.isoformat() if job and job.next_run_time else None
    return settings


@app.put("/api/settings")
async def update_settings(settings: dict):
    _save_settings(settings)
    _reschedule_cron(settings)
    result = {"status": "saved"}
    for key in ("cron_normal", "cron_force"):
        job = scheduler.get_job(key)
        result[f"{key}_next_run"] = job.next_run_time.isoformat() if job and job.next_run_time else None
    return result


# ── Fresh Posters ─────────────────────────────────────────────────────────────

class FreshPostersRequest(BaseModel):
    library_name: str


@app.post("/api/fetch-fresh-posters")
async def start_fetch_fresh_posters(request: FreshPostersRequest):
    global fresh_posters_state
    if fresh_posters_state["is_running"]:
        return {"error": "Already running"}
    asyncio.create_task(_fetch_fresh_posters_task(request.library_name))
    return {"status": "started"}


@app.get("/api/fetch-fresh-posters/status")
async def get_fresh_posters_status():
    return fresh_posters_state


async def _fetch_fresh_posters_task(library_name: str):
    global fresh_posters_state
    fresh_posters_state.update({
        "is_running": True, "library": library_name,
        "progress": 0, "total": 0,
        "restored": 0, "failed": 0, "current_item": None,
    })
    try:
        from plexapi.server import PlexServer
        plex_url = os.getenv('PLEX_URL')
        plex_token = os.getenv('PLEX_TOKEN')
        server = PlexServer(plex_url, plex_token)
        library = server.library.section(library_name)
        all_items = library.all()
        fresh_posters_state["total"] = len(all_items)
        logger.info(f"Fetch Fresh Posters: {library_name} ({len(all_items)} items)")

        for i, item in enumerate(all_items, 1):
            fresh_posters_state["progress"] = i
            fresh_posters_state["current_item"] = item.title
            try:
                posters = item.posters()
                original = next((p for p in posters if 'upload' not in p.ratingKey), None)
                if original:
                    original.select()
                    fresh_posters_state["restored"] += 1
                    logger.debug(f"✓ {item.title}: reset to original poster")
                else:
                    fresh_posters_state["failed"] += 1
            except Exception as e:
                fresh_posters_state["failed"] += 1
                logger.warning(f"Failed for {item.title}: {e}")
            await asyncio.sleep(0.05)

        logger.info(f"Fresh Posters done: {fresh_posters_state['restored']} restored, {fresh_posters_state['failed']} failed")
    except Exception as e:
        logger.error(f"Fetch Fresh Posters failed: {e}")
    finally:
        fresh_posters_state["is_running"] = False
        fresh_posters_state["current_item"] = None


# ── Delete Backups ────────────────────────────────────────────────────────────

@app.delete("/api/backups")
async def delete_backups(library_name: str, confirm: str = ""):
    if confirm != "DELETE":
        return {"error": "Must pass confirm=DELETE"}
    import shutil
    backup_dir = Path("/backups") / library_name
    if not backup_dir.exists():
        return {"error": f"No backups found for {library_name}"}
    try:
        item_count = sum(1 for _ in backup_dir.iterdir())
        shutil.rmtree(backup_dir)
        logger.info(f"Deleted backups for {library_name} ({item_count} items)")
        return {"status": "deleted", "items": item_count}
    except Exception as e:
        return {"error": str(e)}


# ── Plex Webhook ──────────────────────────────────────────────────────────────

from fastapi import Form as FastAPIForm


@app.post("/webhook/plex")
async def plex_webhook(payload: str = FastAPIForm(...)):
    """Receive Plex webhooks — triggers processing on library.new events."""
    try:
        data = json.loads(payload)
        event = data.get("event", "")
        logger.info(f"Plex webhook: {event}")

        if event == "library.new":
            settings = _load_settings()
            webhook = settings.get("webhook", {})
            if not webhook.get("enabled"):
                return {"status": "ignored", "reason": "webhook disabled"}

            metadata = data.get("Metadata", {})
            target_library = metadata.get("librarySectionTitle")
            if not target_library:
                return {"status": "ignored", "reason": "could not determine library from event"}

            # If libraries list is non-empty, only process the listed libraries
            allowed = webhook.get("libraries", [])
            if allowed and target_library not in allowed:
                return {"status": "ignored", "reason": f"library {target_library!r} not in webhook scope"}

            rating_key = str(metadata.get("ratingKey", "")) or None
            item_title = metadata.get("title", "unknown")

            # Enqueue — worker processes items sequentially, no drops on bulk imports
            await webhook_queue.put((target_library, rating_key, item_title))
            queue_size = webhook_queue.qsize()
            logger.info(f"Webhook queued: {target_library} / {item_title} (key={rating_key}, queue={queue_size})")
            return {"status": "queued", "library": target_library, "item": item_title, "queue_size": queue_size}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
