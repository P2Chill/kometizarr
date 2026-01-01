# Kometizarr

**A safe and powerful Plex automation tool combining rating overlays with smart collection management.**

Kometizarr is a fork of [Posterizarr](https://github.com/fscorrupt/Posterizarr) that adds dynamic rating overlays and safe collection management, designed to avoid the library-breaking issues found in Kometa.

## Features

### ✅ Rating Overlay System
- **Dynamic rating badges** applied to movie/TV show posters
- **Multiple rating sources:**
  - TMDB ratings (movies and TV shows)
  - TVDB ratings (TV shows)
  - IMDb ratings (via OMDb API)
  - Rotten Tomatoes scores (via OMDb API)
- **Per-episode ratings** (when available)
- **Customizable badge styles:** Position, size, color themes
- **Batch processing:** Efficiently process thousands of posters

### 🎯 Safe Collection Management
- **Atomic operations:** Each item added independently (no cascading failures)
- **Dry-run mode:** Preview changes before applying
- **Easy rollback:** Delete collections with one command
- **Detailed logging:** Track every operation
- **NO metadata changes:** Collections only, no database modifications

### 📦 Collection Types
- **Decade collections:** 1980s, 1990s, 2000s, etc.
- **Top lists:** IMDb Top 250, Rotten Tomatoes Top 100
- **Studio collections:** Marvel, DC, Disney, etc.
- **Custom collections:** User-defined criteria

## Why Kometizarr?

**Kometa Issues:**
- ❌ Can break Plex libraries (requires 400GB+ restores)
- ❌ Modifies artwork and metadata permanently
- ❌ No rollback mechanism
- ❌ Concurrent database access risks

**Kometizarr Solutions:**
- ✅ Uses official Plex API (no database touching)
- ✅ Atomic collection operations
- ✅ Dry-run mode for safety
- ✅ Easy rollback
- ✅ Detailed error logging

## Quick Start

### Prerequisites
- Python 3.8+
- Plex Media Server
- TMDB API key (free from https://www.themoviedb.org/settings/api)
- Optional: OMDb API key for IMDb/RT ratings

### Installation
```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr
pip install -r requirements.txt
```

### Configuration
```bash
cp config.example.json config.json
# Edit config.json with your API keys and Plex details
```

### Usage

**Test rating overlay on a single movie:**
```bash
python examples/test_end_to_end.py
```

**Batch process multiple movies:**
```bash
python examples/batch_process_ratings.py
```

**Create collections (dry-run):**
```bash
python src/collection_manager/manager.py --dry-run
```

## Project Structure

```
kometizarr/
├── src/
│   ├── rating_overlay/      # Rating badge generation and overlay
│   ├── collection_manager/  # Safe Plex collection management
│   └── utils/               # Shared utilities
├── examples/                # Prototype scripts and examples
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── config.example.json      # Example configuration
└── README.md
```

## Performance

Based on testing with 10 sample movies:
- **Processing speed:** ~0.6 seconds per movie
- **Rate limiting:** 3 requests/second (well under TMDB's 40/10sec limit)
- **26,000 movie library:** Estimated ~4.3 hours to process

## License

MIT License - See LICENSE file for details

Incorporates code from:
- [Posterizarr](https://github.com/fscorrupt/Posterizarr) (overlay system)
- [Kometa](https://github.com/Kometa-Team/Kometa) (collection management patterns) - MIT License

## Roadmap

### Phase 1: Rating Overlays ✅
- [x] TMDB API integration
- [x] Badge generation with PIL
- [x] Poster compositing
- [x] Batch processing
- [ ] Integration into Posterizarr codebase

### Phase 2: Collection Management
- [ ] Decade collections
- [ ] Top list collections (IMDb Top 250, RT Top 100)
- [ ] Studio collections
- [ ] Custom collection builder

### Phase 3: Advanced Features
- [ ] Per-episode rating overlays
- [ ] Multiple rating sources (OMDb for IMDb/RT)
- [ ] Web UI for configuration
- [ ] Scheduled updates

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

## Acknowledgments

- [Posterizarr](https://github.com/fscorrupt/Posterizarr) for the excellent overlay system
- [Kometa](https://github.com/Kometa-Team/Kometa) for collection management inspiration
- [PlexAPI](https://github.com/pkkid/python-plexapi) for the Plex Python library
