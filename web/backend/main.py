"""
Kometizarr Web UI - FastAPI Backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
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

app = FastAPI(title="Kometizarr API", version="1.0.3")

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
    position: str = "northwest"
    force: bool = False
    limit: Optional[int] = None
    rating_sources: Optional[Dict[str, bool]] = None  # Which ratings to show


class LibraryStats(BaseModel):
    library_name: str
    total_items: int
    processed_items: int
    success_rate: float


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "app": "Kometizarr API", "version": "1.0.3"}


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
            rating_sources=request.rating_sources
        )

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

            result = manager.process_movie(item, position=request.position, force=request.force)

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
        processing_state["is_processing"] = False
        processing_state["stop_requested"] = False
        processing_state["error"] = str(e)
        logger.error(f"❌ Processing failed: {request.library_name} - Error: {e}")
        await broadcast_progress()


@app.get("/api/status")
async def get_status():
    """Get current processing status"""
    return processing_state


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
