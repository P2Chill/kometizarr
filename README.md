# Kometizarr

**Automated rating overlays and collection management for Plex - Simple, fast, and powerful.**

Kometizarr automatically adds gorgeous multi-source rating badges to your Plex movie and TV show posters. No more messy YAML configs, no database risks, just clean Python that works.

![Kometizarr Demo](docs/12_monkeys.jpg)

## ✨ Features

### 🎯 Multi-Source Rating Overlays
- **4 independent rating badges** (NEW in v1.1.1):
  - 🎬 **TMDB** ratings (movies and TV shows)
  - ⭐ **IMDb** ratings (via OMDb API)
  - 🍅 **Rotten Tomatoes Critic** scores (via MDBList)
  - 🍿 **Rotten Tomatoes Audience** scores (via MDBList)
- **NEW: Independent positioning** - Place each badge separately anywhere on the poster
- **NEW: Visual alignment guides** - Live grid overlay for precise badge placement
- **NEW: 11 font options** - Sans/Serif/Mono in Bold, Regular, and Italic variants
- **NEW: Per-badge customization** - Font, color, opacity, and size per badge
- **Backward compatible** - Legacy unified badge still supported

### 🎨 Beautiful Design
- **Dynamic RT logos:** Fresh tomato/rotten splat for critic scores, fresh/spilled popcorn for audience scores
- **Smart sizing:** Logos scale proportionally, popcorn icons enlarged for visibility
- **Perfect alignment:** All ratings and logos line up beautifully
- **50% opacity background:** Semi-transparent black rounded rectangle
- **Color-coded text:** Gold ratings, white symbols (/10, %)
- **Drop shadows:** Crisp text on any poster background

### 🚀 Fast & Safe
- **Atomic operations:** Each poster processed independently
- **Automatic backups:** Original posters saved before modification
- **Easy restoration:** Restore originals with one command
- **Rate limited:** Respects API limits (TMDB, MDBList)
- **Batch processing:** Process entire libraries efficiently
- **Resume support:** Skip already-processed items

### 📦 Smart Collection Management
- **Decade collections:** Automatically organize by era
- **Keyword collections:** DC Universe, Zombies, Time Travel, etc.
- **Studio collections:** Marvel, Disney, Warner Bros
- **Custom collections:** Define your own criteria
- **Dry-run mode:** Preview before applying
- **Safe operations:** No database modifications, uses official Plex API

## 🖼️ Screenshots

### NEW: 4-Badge Independent Positioning (v1.1.1)

**High Rated Classic** - 12 Monkeys (IMDb 8.0, TMDB 7.6, RT 88%/88%)
![12 Monkeys](docs/12_monkeys.jpg)

**Mixed Ratings** - 2 Guns (IMDb 6.7, TMDB 6.5, RT 66%/64%)
![2 Guns](docs/2_guns.jpg)

**High Audience Score** - #Alive (IMDb 6.3, TMDB 7.2, RT 63%/88%)
![#Alive](docs/numberalive.jpg)

> **4-Badge System:** Each rating source positioned independently with custom styling
> - **Independent positioning** - Place each badge anywhere on the poster
> - **Visual alignment guides** - Grid overlay for precise placement
> - **11 font options** - DejaVu Sans/Serif/Mono in Bold/Regular/Italic
> - **Dynamic RT logos:** Fresh tomato (≥60%) / Rotten splat (<60%) for critics, Fresh popcorn (≥60%) / Spilled (< 60%) for audience

## 🚀 Quick Start

**📦 Pre-built Docker Images Available:**
- **Docker Hub:** `p2chill/kometizarr-backend:latest` & `p2chill/kometizarr-frontend:latest`
- **GitHub Container Registry:** `ghcr.io/p2chill/kometizarr-backend:latest` & `ghcr.io/p2chill/kometizarr-frontend:latest`

No build required - just pull and run! ⚡

### Method 1: Web UI (Recommended) 🌐

The easiest way to use Kometizarr is with the Web UI - a beautiful dashboard with live progress tracking!

#### Option A: Direct Pull (No Clone Required) ⚡

Create a `docker-compose.yml` file:

```yaml
services:
  backend:
    image: ghcr.io/p2chill/kometizarr-backend:latest
    container_name: kometizarr-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data/backups:/backups  # Poster backups (PERSISTENT)
      - ./data/temp:/temp  # Temp processing
    environment:
      - PLEX_URL=http://YOUR_PLEX_IP:32400
      - PLEX_TOKEN=YOUR_PLEX_TOKEN
      - TMDB_API_KEY=YOUR_TMDB_KEY
      - OMDB_API_KEY=YOUR_OMDB_KEY  # Optional
      - MDBLIST_API_KEY=YOUR_MDBLIST_KEY
    restart: unless-stopped
    networks:
      - kometizarr

  frontend:
    image: ghcr.io/p2chill/kometizarr-frontend:latest
    container_name: kometizarr-frontend
    ports:
      - "3001:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - kometizarr

networks:
  kometizarr:
    driver: bridge
```

Then run:
```bash
docker compose up -d
```

Open `http://localhost:3001` - done in 5 seconds! 🎉

**Alternative registries:**
- **Docker Hub:** Replace `ghcr.io/p2chill/` with `p2chill/`
- **Version pinning:** Replace `:latest` with `:v1.1.1` for stable releases

#### Option B: Clone Repository (For Development)

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr
cp .env.example .env
# Edit .env with your Plex credentials and API keys
docker compose up -d
```

<details>
<summary>📄 View docker compose.yml</summary>

```yaml
services:
  backend:
    build: ./web/backend
    container_name: kometizarr-backend
    ports:
      - "8000:8000"
    volumes:
      - ./:/app/kometizarr  # Mount entire project
      - ./web/backend:/app/backend  # Mount backend source for hot-reload (no rebuild needed)
      - ./data/backups:/backups  # Poster backups (PERSISTENT - survives reboots)
      - ./data/temp:/temp  # Temp processing
    environment:
      - PLEX_URL=${PLEX_URL:-http://192.168.1.20:32400}
      - PLEX_TOKEN=${PLEX_TOKEN}
      - TMDB_API_KEY=${TMDB_API_KEY}
      - OMDB_API_KEY=${OMDB_API_KEY}
      - MDBLIST_API_KEY=${MDBLIST_API_KEY}
    restart: unless-stopped
    networks:
      - kometizarr

  frontend:
    build: ./web/frontend
    container_name: kometizarr-frontend
    ports:
      - "3001:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - kometizarr

networks:
  kometizarr:
    driver: bridge
```

</details>

Then open `http://localhost:3001` in your browser! 🎉

**Features:**
- 📊 Visual dashboard with library stats
- ⚡ Real-time progress with WebSocket updates (auto-reconnect on disconnection)
- 🎯 One-click processing with live progress tracking
- 📈 Live success/failure/skipped counts
- 🎨 Rating source filtering (choose TMDB, IMDb, RT Critic, RT Audience)
- 🔄 Browser refresh resilience (resumes monitoring active operations)
- ⏱️ 10-second countdown on completion with skip option
- 🛑 Cancel/stop button to abort processing mid-run

See [Web UI Documentation](web/README.md) for details.

### Method 2: CLI/Python Script

For advanced users or automation:

**Prerequisites:**
- Python 3.8+
- Plex Media Server
- **TMDB API key** (free) - https://www.themoviedb.org/settings/api
- **MDBList API key** (free) - https://mdblist.com/
- Optional: **OMDb API key** for IMDb ratings - http://www.omdbapi.com/

**Installation:**

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr
pip install -r requirements.txt
```

### Configuration

1. Copy example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your details:
```json
{
  "plex": {
    "url": "http://YOUR_PLEX_IP:32400",
    "token": "YOUR_PLEX_TOKEN",
    "library": "Movies"
  },
  "apis": {
    "tmdb": {
      "api_key": "YOUR_TMDB_KEY"
    },
    "omdb": {
      "api_key": "YOUR_OMDB_KEY",
      "enabled": true
    },
    "mdblist": {
      "api_key": "YOUR_MDBLIST_KEY"
    }
  },
  "rating_overlay": {
    "enabled": true,
    "badge": {
      "position": "northwest",
      "style": "default"
    }
  }
}
```

**How to get your Plex token:** https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### Usage

**Process entire movie library:**
```python
from src.rating_overlay.plex_poster_manager import PlexPosterManager
import json

with open('config.json') as f:
    config = json.load(f)

manager = PlexPosterManager(
    plex_url=config['plex']['url'],
    plex_token=config['plex']['token'],
    library_name='Movies',
    tmdb_api_key=config['apis']['tmdb']['api_key'],
    omdb_api_key=config['apis']['omdb']['api_key'],
    mdblist_api_key=config['apis']['mdblist']['api_key'],
    backup_dir='./data/kometizarr_backups'
)

# Process all movies (skips already processed)
manager.process_library(position='northwest', force=False)
```

**Process single movie:**
```python
movie = plex.library.section('Movies').get('The Dark Knight')
manager.process_movie(movie, position='northwest')
```

**Restore original posters:**
```python
# Restore single movie
manager.restore_movie('The Dark Knight')

# Restore entire library
manager.restore_library()
```

**TV Shows:**
Same API, just use `library_name='TV Shows'` - works identically!

## 📊 Performance

**Tested on 2,363 movie library:**
- **Processing speed:** ~0.7-1.1 movies/second
- **Total time:** ~35-55 minutes for full library
- **API limits:** Respects TMDB (40 req/10s) and MDBList limits
- **Memory usage:** Minimal (processes one at a time)

**Rate limiting:**
- 0.3s delay between movies (default)
- Adjustable in `process_library(rate_limit=0.3)`

## 🎯 Why Kometizarr?

Kometizarr is designed to be a lightweight, focused alternative for rating overlays:

- **Simple Configuration:** Single JSON config file, no complex YAML hierarchy
- **Fast Processing:** Direct API calls with efficient rate limiting (~1 item/second)
- **Safe Operations:** Official Plex API, automatic backups, atomic operations
- **Flexible Workflows:** Easy restoration, dry-run mode, skip processed items
- **Beautiful Design:** Multi-source ratings (TMDB, IMDb, RT), dynamic RT logos that change based on score
- **Modern Stack:** Clean Python code with optional Web UI (React + FastAPI)
- **Plex-First Ratings:** Extracts ratings from Plex metadata before hitting external APIs (97%+ success rate)

## 📁 Project Structure

```
kometizarr/
├── src/
│   ├── rating_overlay/
│   │   ├── multi_rating_badge.py    # Badge generation with dynamic logos
│   │   ├── rating_fetcher.py        # TMDB, OMDb, MDBList API calls
│   │   ├── plex_poster_manager.py   # Orchestration and Plex integration
│   │   ├── backup_manager.py        # Original poster backups
│   │   └── overlay_composer.py      # Poster compositing
│   ├── collection_manager/          # Smart collection management
│   └── utils/
│       └── logger.py                # Clean progress tracking
├── web/
│   ├── backend/                     # FastAPI backend with WebSocket
│   │   ├── main.py                  # API endpoints and processing
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/                    # React frontend
│   │   ├── src/
│   │   │   ├── components/          # Dashboard, ProcessingProgress
│   │   │   ├── App.jsx
│   │   │   └── main.jsx
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── package.json
│   └── README.md                    # Web UI documentation
├── assets/
│   └── logos/                       # RT tomato/popcorn logos
├── examples/                        # Example scripts
├── docker compose.yml               # Docker Compose configuration
├── .env.example                     # Environment variables template
├── config.example.json              # CLI configuration example
└── README.md
```

## 🎨 Customization

### Badge Position
```python
# Options: 'northwest', 'northeast', 'southwest', 'southeast'
manager.process_library(position='northwest')
```

### Badge Styling
The badge automatically:
- Scales to 45% of poster width
- Uses semi-transparent black background (50% opacity)
- Left-aligns all logos
- Displays gold ratings with white symbols
- Adjusts logo sizes (popcorn icons 1.2-1.3x larger for visibility)

### Adding Custom Logos
Place PNG files in `assets/logos/`:
- `tmdb.png` - TMDB logo
- `imdb.png` - IMDb logo
- `rt_fresh.png` - Fresh tomato (critic ≥60%)
- `rt_rotten.png` - Rotten splat (critic <60%)
- `rt_audience_fresh.png` - Fresh popcorn (audience ≥60%)
- `rt_audience_rotten.png` - Spilled popcorn (audience <60%)

Logos should have transparent backgrounds (PNG with alpha channel).

## 🔧 Advanced Features

### Process TV Shows
```python
manager = PlexPosterManager(
    plex_url=config['plex']['url'],
    plex_token=config['plex']['token'],
    library_name='TV Shows',  # Change to TV library
    ...
)
manager.process_library()
```

### Force Reprocessing
```python
# Reprocess all items, even if already done
manager.process_library(force=True)
```

### Limit Processing
```python
# Test on first 10 movies
manager.process_library(limit=10)
```

### Custom Backup Directory
```python
# IMPORTANT: Use a persistent location, NOT /tmp!
manager = PlexPosterManager(
    ...,
    backup_dir='/home/user/kometizarr/backups'  # Or any persistent path
)
```

## 🛡️ Safety Features

### Automatic Backups
- Original posters saved to `backup_dir/LibraryName/MovieTitle/`
- **Web UI/Docker:** Backups stored in `./data/backups/` (persistent across reboots)
- **CLI:** Default is `/tmp/kometizarr_backups` - **⚠️ WARNING:** This gets cleared on reboot! Use a persistent location for production
- Metadata stored (TMDB ID, IMDb ID, ratings)
- Overlay version also saved for reference

### Restoration
- Restore from backed up originals
- Safe to run multiple times
- No data loss

### Dry-Run Mode
```python
manager = PlexPosterManager(..., dry_run=True)
manager.process_library()  # Preview without applying
```

## 📈 Roadmap

### Completed ✅
- [x] Multi-source rating badges (TMDB, IMDb, RT Critic, RT Audience)
- [x] Dynamic RT logo system
- [x] Batch processing for movies
- [x] TV show support
- [x] Automatic backups and restoration
- [x] Beautiful overlay design with proper alignment
- [x] Rate limiting and API safety
- [x] Collection management (decades, studios, keywords, genres)
- [x] **Web UI** - React dashboard with FastAPI backend
- [x] **Real-time progress** - WebSocket updates for live tracking
- [x] **Docker deployment** - Docker Compose support
- [x] **Smart library detection** - Auto-detect movie vs TV show libraries
- [x] **Network/Studio presets** - 13 streaming services + 12 movie studios
- [x] **Collection visibility controls** - Hide collections from library view
- [x] **Modal-based creation** - Select which collections to create (no auto-duplication)
- [x] **Cancel/Stop Button** - Ability to abort running overlay processing
  - Stop button in Web UI during active processing
  - Gracefully terminate backend processing loop
  - Confirm dialog to prevent accidental cancellation
- [x] **Rating source filtering** - Selectively choose which rating sources to display
  - Web UI checkboxes for TMDB, IMDb, RT Critic, RT Audience
  - Preferences saved in localStorage (persists across sessions)
  - CLI configuration via config.json
- [x] **Browser reconnection** - Resume monitoring active processing after page refresh
  - Frontend checks `/api/status` on mount to detect active operations
  - Automatically reconnects to processing view with current progress
  - Stop button remains functional after reconnection
- [x] **WebSocket auto-reconnect** - Resilient real-time updates during backend restarts
  - Automatic reconnection with visual feedback banner
  - Seamless resume of live progress updates
  - Handles frontend/backend container rebuilds gracefully
- [x] **10-second countdown** - Completion screen with countdown before returning to dashboard
  - Prevents accidental navigation away from completion stats
  - Skip button to return immediately
- [x] **4-Badge Independent Positioning** (v1.1.1) - Each rating source can be positioned separately
  - Visual alignment guides with live grid overlay
  - Per-badge customization (font, color, opacity, size)
  - 11 font choices (DejaVu Sans/Serif/Mono variants)
  - Real-time preview with drag-and-drop positioning
  - Backward compatible with legacy unified badge mode

### Planned 🚧
- [ ] **Multi-server support** - Add/remove Plex servers from Web UI
  - Network discovery for Plex servers
  - OAuth authentication flow (no manual token setup)
  - Auto-discover libraries from selected server
  - Switch between servers without editing .env
  - Save server configurations in database
- [ ] **Scheduled automatic processing** - Set-and-forget automation for rating overlays
  - Cron-style scheduling (daily, weekly, custom intervals)
  - Sequential library processing (Movies → TV Shows automatically)
  - Per-library schedules (e.g., TV shows every Sunday, movies every Wednesday)
  - Default: all selected libraries run back-to-back on your chosen schedule
  - Keeps ratings fresh as new content gets rated and RT scores change
- [ ] **unRAID Community Applications** - Official unRAID template for one-click installation
  - Easier deployment for unRAID users
  - Auto-updates from Community Applications store
  - Releasing after initial stabilization period with early adopters
- [ ] Per-episode ratings for TV shows
- [ ] Custom badge themes
- [ ] Integration with Tautulli for viewing stats
- [ ] Genre-based smart collections

## 🤝 Contributing

Contributions welcome! Please:
1. Open an issue first to discuss changes
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- **[Posterizarr](https://github.com/fscorrupt/Posterizarr)** - Original overlay inspiration
- **[Kometa](https://github.com/Kometa-Team/Kometa)** - Collection management patterns
- **[PlexAPI](https://github.com/pkkid/python-plexapi)** - Excellent Python Plex library
- **[MDBList](https://mdblist.com/)** - RT ratings API
- **[TMDB](https://www.themoviedb.org/)** - Movie database and ratings

## 💬 Support

- **Issues:** https://github.com/P2Chill/kometizarr/issues
- **Discussions:** https://github.com/P2Chill/kometizarr/discussions

---

**Made with ❤️ for the Plex community**
