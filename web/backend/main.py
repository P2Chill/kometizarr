"""
Kometizarr Web UI - FastAPI Backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import json
import os
import sys

# Add kometizarr to path
sys.path.insert(0, '/app/kometizarr')

from src.rating_overlay.plex_poster_manager import PlexPosterManager
from src.utils.logger import setup_logger

app = FastAPI(title="Kometizarr API", version="1.0.0")

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

# Processing state
processing_state = {
    "is_processing": False,
    "current_library": None,
    "progress": 0,
    "total": 0,
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "current_item": None
}


class ProcessRequest(BaseModel):
    library_name: str
    position: str = "northwest"
    force: bool = False
    limit: Optional[int] = None


class LibraryStats(BaseModel):
    library_name: str
    total_items: int
    processed_items: int
    success_rate: float


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "app": "Kometizarr API", "version": "1.0.0"}


@app.get("/api/libraries")
async def get_libraries():
    """Get all Plex libraries"""
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
                "count": len(lib.all())
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

        all_items = library.all()
        total = len(all_items)

        # Check how many have backups (processed)
        backup_dir = f"/backups/{library_name}"
        processed = 0
        if os.path.exists(backup_dir):
            processed = len(os.listdir(backup_dir))

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


async def process_library_background(request: ProcessRequest):
    """Background task for processing library"""
    global processing_state

    try:
        processing_state["is_processing"] = True
        processing_state["current_library"] = request.library_name

        # Initialize manager
        manager = PlexPosterManager(
            plex_url=os.getenv('PLEX_URL'),
            plex_token=os.getenv('PLEX_TOKEN'),
            library_name=request.library_name,
            tmdb_api_key=os.getenv('TMDB_API_KEY'),
            omdb_api_key=os.getenv('OMDB_API_KEY'),
            mdblist_api_key=os.getenv('MDBLIST_API_KEY'),
            backup_dir='/backups',
            dry_run=False
        )

        all_items = manager.library.all()
        if request.limit:
            all_items = all_items[:request.limit]

        processing_state["total"] = len(all_items)

        # Process each item
        for i, item in enumerate(all_items, 1):
            processing_state["progress"] = i
            processing_state["current_item"] = item.title

            result = manager.process_movie(item, position=request.position, force=request.force)

            if result:
                processing_state["success"] += 1
            else:
                processing_state["failed"] += 1

            # Broadcast progress to all WebSocket connections
            await broadcast_progress()

            # Rate limiting
            await asyncio.sleep(0.3)

        processing_state["is_processing"] = False
        await broadcast_progress()  # Final update

    except Exception as e:
        processing_state["is_processing"] = False
        processing_state["error"] = str(e)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
