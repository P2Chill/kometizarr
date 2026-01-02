# Kometizarr

**Beautiful rating overlays for Plex - Simple, fast, and better than Kometa.**

Kometizarr automatically adds gorgeous multi-source rating badges to your Plex movie and TV show posters. No more messy YAML configs, no database risks, just clean Python that works.

![Kometizarr Demo](docs/demo.png)

## ✨ Features

### 🎯 Multi-Source Rating Overlays
- **4 rating sources in one badge:**
  - 🎬 **TMDB** ratings (movies and TV shows)
  - ⭐ **IMDb** ratings (via OMDb API)
  - 🍅 **Rotten Tomatoes Critic** scores (via MDBList)
  - 🍿 **Rotten Tomatoes Audience** scores (via MDBList)

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

### Rating Overlay Examples

**Movie with High Scores:**
- The Dark Knight: TMDB 8.5, IMDb 9.1, RT 94% (fresh tomato), RT Audience 94% (standing popcorn)

**Movie with Mixed Scores:**
- 2 Fast 2 Furious: TMDB 6.5, IMDb 5.9, RT 37% (rotten splat), RT Audience 50% (spilled popcorn)

**TV Show:**
- The 100: TMDB 7.9, IMDb 7.5, RT 93% (fresh tomato), RT Audience 68% (fresh popcorn)

> **Dynamic Logo System:** RT logos automatically change based on score:
> - **Critic ≥60%:** Fresh tomato 🍅 | **<60%:** Rotten splat 💥
> - **Audience ≥60%:** Fresh popcorn 🍿 | **<60%:** Spilled popcorn 🍿💔

## 🚀 Quick Start

### Method 1: Web UI (Recommended) 🌐

The easiest way to use Kometizarr is with the Web UI - a beautiful dashboard with live progress tracking!

#### Option A: Docker Compose (Quick Start)

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr
cp .env.example .env
# Edit .env with your Plex credentials and API keys
docker-compose up -d
```

Then open `http://localhost:3001` in your browser! 🎉

#### Option B: Terraform (Infrastructure as Code)

For those managing infrastructure with Terraform:

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials
terraform init
terraform apply
```

See [Terraform Documentation](terraform/README.md) for details.

**Features:**
- 📊 Visual dashboard with library stats
- ⚡ Real-time progress with WebSocket updates
- 🎯 One-click processing
- 📈 Live success/failure tracking
- 🏗️ Infrastructure as code with Terraform

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
    backup_dir='/tmp/kometizarr_backups'
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

### Kometa Problems ❌
- Complex YAML configurations (dozens of files)
- Slow processing (hours for large libraries)
- Can break Plex databases (risky concurrent access)
- No easy rollback
- Limited rating sources
- Static tomato icons (don't change with score)

### Kometizarr Solutions ✅
- **Simple:** One config.json file
- **Fast:** Direct API calls, efficient processing
- **Safe:** Official Plex API, automatic backups, atomic operations
- **Flexible:** Easy restoration, dry-run mode, skip processed items
- **Beautiful:** Multi-source ratings, dynamic RT logos, perfect design
- **Modern:** Clean Python code, not YAML spaghetti

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
├── terraform/
│   ├── kometizarr.tf                # Main Terraform config
│   ├── variables.tf                 # Variable definitions
│   ├── terraform.tfvars.example     # Example variables
│   └── README.md                    # Terraform documentation
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
manager = PlexPosterManager(
    ...,
    backup_dir='/mnt/nas/plex_backups'
)
```

## 🛡️ Safety Features

### Automatic Backups
- Original posters saved to `backup_dir/LibraryName/MovieTitle/`
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
- [x] Collection management (decades, studios, keywords)

### Planned 🚧
- [ ] Web UI for configuration
- [ ] Per-episode ratings for TV shows
- [ ] Scheduled updates (refresh ratings periodically)
- [ ] Custom badge themes
- [ ] Integration with Tautulli for viewing stats
- [ ] Docker container for easy deployment

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
