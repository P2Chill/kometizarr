# Kometizarr Web UI

Beautiful web interface for managing Plex rating overlays with real-time progress tracking.

## Features

- 🎨 **Visual Dashboard** - See your libraries and stats at a glance
- 📊 **Live Progress** - Real-time WebSocket updates as processing happens
- ⚙️ **Easy Configuration** - Select libraries and options with a clean UI
- 🚀 **Fast & Responsive** - Built with React and FastAPI
- 🐳 **Docker Ready** - Deploy with one command

## Quick Start

### 1. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your Plex and API credentials:
```env
PLEX_URL=http://YOUR_PLEX_IP:32400
PLEX_TOKEN=YOUR_PLEX_TOKEN
TMDB_API_KEY=YOUR_TMDB_KEY
OMDB_API_KEY=YOUR_OMDB_KEY  # Optional
MDBLIST_API_KEY=YOUR_MDBLIST_KEY  # Optional
```

**How to get your Plex token:** https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### 2. Start with Docker Compose

From the root `kometizarr/` directory:
```bash
docker-compose up -d
```

This will:
- Build the backend API (FastAPI)
- Build the frontend UI (React + Nginx)
- Start both services

### 3. Access the Web UI

Open your browser to:
```
http://localhost:3001
```

## Architecture

```
┌─────────────────┐
│  React Frontend │  ←  Port 3000
│   (Nginx)       │
└────────┬────────┘
         │
         ↓ API calls + WebSocket
┌────────┴────────┐
│  FastAPI Backend│  ←  Port 8000
│   (Python)      │
└────────┬────────┘
         │
         ↓
┌────────┴────────┐
│  Plex Server    │
└─────────────────┘
```

## Development

### Backend Development

```bash
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

API docs at `http://localhost:8000/docs`

### Frontend Development

```bash
cd web/frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3001`

### API Endpoints

- `GET /` - Health check
- `GET /api/libraries` - List all Plex libraries
- `GET /api/library/{name}/stats` - Get library statistics
- `POST /api/process` - Start overlay processing
- `GET /api/status` - Get current processing status
- `WS /ws/progress` - WebSocket for live progress updates

## How It Works

1. **Select Library** - Choose Movies or TV Shows library
2. **Configure Options** - Select badge position and processing options
3. **Start Processing** - Click "Start Processing" button
4. **Watch Live Progress** - See real-time updates via WebSocket
   - Progress bar shows completion percentage
   - Success/Failed/Skipped counts update live
   - Current item being processed is displayed
5. **Complete** - Automatic redirect to dashboard when done

## Features Explained

### Live Progress Tracking

The Web UI uses WebSocket connections to stream live progress updates:
- **No page refreshes needed** - Updates happen automatically
- **Real-time stats** - Success rate, failures, and remaining items
- **Current item display** - See exactly what's being processed
- **Automatic completion** - Redirects to dashboard when done

### Badge Position Options

- **Northwest** (Top Left) - Default, most visible
- **Northeast** (Top Right)
- **Southwest** (Bottom Left)
- **Southeast** (Bottom Right)

### Processing Options

- **Force Reprocess** - Reprocess items that already have overlays
  - ⚠️ Warning: This will create double overlays!
  - Use only when you want to update existing overlays

## Integration with Arr Stack

Since Kometizarr uses Docker, you can add it to your existing Arr stack network:

```yaml
networks:
  arr-network:
    external: true
```

Then in `docker-compose.yml`:
```yaml
networks:
  kometizarr:
    external:
      name: arr-network
```

## Troubleshooting

### Backend won't start
- Check `.env` file has correct Plex credentials
- Verify Plex server is accessible from Docker container
- Check logs: `docker logs kometizarr-backend`

### Frontend shows connection error
- Verify backend is running: `docker ps`
- Check backend logs for errors
- Try accessing backend directly: `http://localhost:8000/`

### WebSocket disconnects
- Check nginx proxy configuration in `frontend/nginx.conf`
- Verify WebSocket upgrade headers are set
- Check browser console for WebSocket errors

## Performance

- **Processing Speed**: ~1-2 items/second (limited by Plex API)
- **Memory Usage**: ~200MB backend, ~50MB frontend
- **Network**: Minimal - WebSocket updates are small JSON messages

## Security

⚠️ **Important Security Notes:**

- The Web UI should **NOT** be exposed to the internet without authentication
- Plex tokens are powerful - keep your `.env` file secure
- In production, use HTTPS and add authentication middleware
- Consider using Nginx Proxy Manager or Traefik for SSL

## Roadmap

- [ ] **Authentication** - User login and session management
- [ ] **Collection Manager** - Visual collection creation/editing
- [ ] **Restore Function** - One-click restore original posters
- [ ] **Scheduling** - Auto-process new content
- [ ] **Statistics Dashboard** - Charts and analytics
- [ ] **Per-Item Controls** - Process/skip individual items
- [ ] **Badge Preview** - See overlay before applying

## Contributing

Contributions welcome! The Web UI is built with:
- **Backend**: FastAPI (Python 3.12)
- **Frontend**: React 18 + Vite + Tailwind CSS
- **WebSocket**: Native WebSocket API
- **Deployment**: Docker + Nginx

## License

MIT License - Same as Kometizarr core
