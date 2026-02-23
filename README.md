# Kometizarr

**Automated rating overlays and collection management for Plex - Simple, fast, and powerful.**

Kometizarr automatically adds gorgeous multi-source rating badges to your Plex movie and TV show posters. No more messy YAML configs, no database risks, just clean Python that works.

![Kometizarr Demo](docs/beforeafter.jpg)

## ✨ Features

### 🎯 Multi-Source Rating Overlays
- **4 independent rating badges** — TMDB, IMDb, RT Critic, RT Audience
- **Independent positioning** — Place each badge separately anywhere on the poster
- **Visual alignment guides** — Live grid overlay for precise badge placement
- **11 font options** — DejaVu Sans/Serif/Mono in Bold, Regular, and Italic variants
- **Per-badge customization** — Font, color, opacity, size, and logo scale per badge
- **Live preview** — Render 3 real posters from your library before committing
- **Backward compatible** — Legacy unified badge still supported

### 🎨 Beautiful Design
- **Dynamic RT logos:** Fresh tomato/rotten splat for critic scores, fresh/spilled popcorn for audience scores
- **Smart sizing:** Logos scale proportionally, popcorn icons enlarged for visibility
- **Perfect alignment:** All ratings and logos line up beautifully
- **50% opacity background:** Semi-transparent black rounded rectangle
- **Color-coded text:** Gold ratings, white symbols (/10, %)
- **Drop shadows:** Crisp text on any poster background

### ⚙️ Set-and-Forget Automation (NEW in v1.2.0)
- **Two independent cron schedules** — Normal run (new items only) + Force run (refresh all ratings)
- **Human-readable scheduling** — Daily, Weekly, Every hour with a time picker — no cron syntax needed
- **Plex Webhook** — Automatically process the exact item added, the moment it's added
- **Webhook queue** — Bulk imports (10 items at once) handled cleanly, no dropped events
- **Multi-library selection** — Checkboxes for cron and webhook — pick any combination of libraries
- **Settings tab** — All automation configured from the Web UI, persisted across restarts

### 📊 Dashboard
- **Multi-library processing** — Select any combination of libraries and process them in one click
- **Real-time progress** — WebSocket updates with live success/failure/skipped counts
- **Library stats** — Total items and processed count per library
- **Stop button** — Graceful abort mid-run

### 📦 Smart Collection Management
- **Decade collections:** Automatically organize by era
- **Keyword collections:** DC Universe, Zombies, Time Travel, etc.
- **Studio collections:** Marvel, Disney, Warner Bros
- **Custom collections:** Define your own criteria
- **Dry-run mode:** Preview before applying
- **Safe operations:** No database modifications, uses official Plex API

### 🚀 Fast & Safe
- **Atomic operations:** Each poster processed independently
- **Automatic backups:** Original posters saved before modification
- **Easy restoration:** One-click restore from the Web UI or CLI
- **Rate limited:** Respects API limits (TMDB, MDBList)
- **Resume support:** Skip already-processed items

## 🖼️ Screenshots

### 4-Badge Independent Positioning

**High Rated Classic** - 12 Monkeys (IMDb 8.0, TMDB 7.6, RT 88%/88%)
![12 Monkeys](docs/12_monkeys.jpg)

**Mixed Ratings** - 2 Guns (IMDb 6.7, TMDB 6.5, RT 66%/64%)
![2 Guns](docs/2_guns.jpg)

**High Audience Score** - #Alive (IMDb 6.3, TMDB 7.2, RT 63%/88%)
![#Alive](docs/numberalive.jpg)

> **4-Badge System:** Each rating source positioned independently with custom styling
> - **Independent positioning** — Place each badge anywhere on the poster
> - **Visual alignment guides** — Grid overlay for precise placement
> - **11 font options** — DejaVu Sans/Serif/Mono in Bold/Regular/Italic
> - **Dynamic RT logos:** Fresh tomato (≥60%) / Rotten splat (<60%) for critics, Fresh popcorn (≥60%) / Spilled (<60%) for audience

## 🚀 Quick Start

**📦 Pre-built Docker Images Available:**
- **Docker Hub:** `p2chill/kometizarr-backend:latest` & `p2chill/kometizarr-frontend:latest`
- **GitHub Container Registry:** `ghcr.io/p2chill/kometizarr-backend:latest` & `ghcr.io/p2chill/kometizarr-frontend:latest`

No build required — just pull and run! ⚡

### Method 1: Web UI (Recommended) 🌐

The easiest way to use Kometizarr is with the Web UI — a beautiful dashboard with live progress tracking and full automation!

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

Open `http://localhost:3001` — done in 5 seconds! 🎉

**Alternative registries:**
- **Docker Hub:** Replace `ghcr.io/p2chill/` with `p2chill/`
- **Version pinning:** Replace `:latest` with `:v1.2.0` for stable releases

#### Option B: Clone Repository (For Development)

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr
cp .env.example .env
# Edit .env with your Plex credentials and API keys
docker compose up -d
```

<details>
<summary>📄 View docker-compose.yml</summary>

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
- 📊 Visual dashboard with library stats and multi-library processing
- ⚡ Real-time progress with WebSocket updates (auto-reconnect on disconnection)
- 🎯 One-click processing with live progress tracking
- 📈 Live success/failure/skipped counts
- 🎨 Rating source filtering (choose TMDB, IMDb, RT Critic, RT Audience)
- 🔄 Browser refresh resilience (resumes monitoring active operations)
- ⏱️ 10-second countdown on completion with skip option
- 🛑 Cancel/stop button to abort processing mid-run
- ⚙️ Settings tab — cron scheduling, webhook, library maintenance

### Setting Up Automation (v1.2.0)

After starting the stack, open the **Settings** tab in the Web UI:

1. **Scheduled Processing** — Enable either or both cron jobs, pick Daily/Weekly/Hourly and a time, select which libraries to include (none = all). Save.
2. **Plex Webhook** — Copy the webhook URL into **Plex → Settings → Webhooks**. Enable and optionally scope to specific libraries.

That's it — Kometizarr will keep your ratings fresh automatically.

### Method 2: CLI/Python Script

For advanced users or automation:

**Prerequisites:**
- Python 3.8+
- Plex Media Server
- **TMDB API key** (free) — https://www.themoviedb.org/settings/api
- **MDBList API key** (free) — https://mdblist.com/
- Optional: **OMDb API key** for IMDb ratings — http://www.omdbapi.com/

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
Same API, just use `library_name='TV Shows'` — works identically!

## 📊 Performance

**Tested on 2,363 movie library:**
- **Processing speed:** ~0.5–4 movies/second depending on your CPU
- **Total time:** ~35–55 minutes for full library
- **API limits:** Respects TMDB (40 req/10s) and MDBList limits
- **Memory usage:** Minimal (processes one at a time)

**Rate limiting:**
- 0.3s delay between movies (default)
- Adjustable in `process_library(rate_limit=0.3)`

## 🎯 Why Kometizarr?

Kometizarr is designed to be a lightweight, focused alternative for rating overlays:

- **Simple Configuration:** Single JSON config file, no complex YAML hierarchy
- **Fast Processing:** Direct API calls with efficient rate limiting
- **Safe Operations:** Official Plex API, automatic backups, atomic operations
- **Flexible Workflows:** Easy restoration, dry-run mode, skip processed items
- **Beautiful Design:** Multi-source ratings (TMDB, IMDb, RT), dynamic RT logos that change based on score
- **Modern Stack:** Clean Python code with optional Web UI (React + FastAPI)
- **Plex-First Ratings:** Extracts ratings from Plex metadata before hitting external APIs (97%+ success rate)
- **True Automation:** Cron scheduling + Plex webhook — fully set-and-forget

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
│   │   ├── main.py                  # API endpoints, cron scheduler, webhook
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/                    # React frontend
│   │   ├── src/
│   │   │   ├── components/          # Dashboard, Settings, ProcessingProgress
│   │   │   ├── App.jsx
│   │   │   └── main.jsx
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── package.json
│   └── README.md                    # Web UI documentation
├── assets/
│   └── logos/                       # RT tomato/popcorn logos
├── examples/                        # Example scripts
├── docker-compose.yml               # Docker Compose configuration
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
- Adjusts logo sizes (popcorn icons 1.2–1.3x larger for visibility)

### Adding Custom Logos
Place PNG files in `assets/logos/`:
- `tmdb.png` — TMDB logo
- `imdb.png` — IMDb logo
- `rt_fresh.png` — Fresh tomato (critic ≥60%)
- `rt_rotten.png` — Rotten splat (critic <60%)
- `rt_audience_fresh.png` — Fresh popcorn (audience ≥60%)
- `rt_audience_rotten.png` — Spilled popcorn (audience <60%)

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
- **CLI:** Default is `/tmp/kometizarr_backups` — **⚠️ WARNING:** This gets cleared on reboot! Use a persistent location for production
- Metadata stored (TMDB ID, IMDb ID, ratings)
- Overlay version also saved for reference

### Restoration
- Restore from backed up originals via Web UI or CLI
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
- [x] Batch processing for movies and TV shows
- [x] Automatic backups and restoration
- [x] Beautiful overlay design with proper alignment
- [x] Rate limiting and API safety
- [x] Collection management (decades, studios, keywords, genres)
- [x] **Web UI** — React dashboard with FastAPI backend
- [x] **Real-time progress** — WebSocket updates for live tracking
- [x] **Docker deployment** — Docker Compose support
- [x] **Smart library detection** — Auto-detect movie vs TV show libraries
- [x] **Network/Studio presets** — 13 streaming services + 12 movie studios
- [x] **Collection visibility controls** — Hide collections from library view
- [x] **Cancel/Stop Button** — Gracefully abort running processing
- [x] **Rating source filtering** — Choose which rating sources to display per run
- [x] **Browser reconnection** — Resume monitoring after page refresh
- [x] **WebSocket auto-reconnect** — Resilient real-time updates
- [x] **4-Badge Independent Positioning** (v1.1.1) — Each badge placed and styled separately
- [x] **Visual alignment guides** — Live grid overlay for precise placement
- [x] **11 font choices** — DejaVu Sans/Serif/Mono in Bold/Regular/Italic
- [x] **Live poster preview** (v1.2.0) — Render real posters before committing
- [x] **Font & logo size sliders** (v1.2.0) — Fine-tune badge scale visually
- [x] **Scheduled processing** (v1.2.0) — Two independent cron jobs (normal + force reprocess)
- [x] **Plex Webhook** (v1.2.0) — Process new items automatically the moment they're added
- [x] **Multi-library selection** (v1.2.0) — Checkbox selection for cron, webhook, and dashboard
- [x] **Settings tab** (v1.2.0) — Full automation config in the Web UI, persisted across restarts

### Planned 🚧
- [ ] **Per-episode ratings for TV shows** — Season/episode level overlay support
- [ ] **unRAID Community Applications** — Official unRAID template for one-click installation
- [ ] **Multi-server support** — Add/remove Plex servers from Web UI

## 🤝 Contributing

Contributions welcome! Please:
1. Open an issue first to discuss changes
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## 📄 License

MIT License — See LICENSE file for details.

## 🙏 Acknowledgments

- **[Posterizarr](https://github.com/fscorrupt/Posterizarr)** — Original overlay inspiration
- **[Kometa](https://github.com/Kometa-Team/Kometa)** — Collection management patterns
- **[PlexAPI](https://github.com/pkkid/python-plexapi)** — Excellent Python Plex library
- **[MDBList](https://mdblist.com/)** — RT ratings API
- **[TMDB](https://www.themoviedb.org/)** — Movie database and ratings

## 💬 Support

- **Issues:** https://github.com/P2Chill/kometizarr/issues
- **Discussions:** https://github.com/P2Chill/kometizarr/discussions

---

**Made with ❤️ for the Plex community**
