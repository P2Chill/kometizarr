# Kometizarr - Plex Rating Overlay Web UI
#
# IMPORTANT: This config assumes you're running terraform from the terraform/ directory
# If integrating with existing terraform, adjust paths accordingly

# Kometizarr network
resource "docker_network" "kometizarr" {
  name = "kometizarr"
}

# Backend container
resource "docker_container" "kometizarr_backend" {
  name  = "kometizarr-backend"
  image = docker_image.kometizarr_backend.name

  restart = "unless-stopped"

  networks_advanced {
    name    = docker_network.kometizarr.name
    aliases = ["backend"]
  }

  ports {
    internal = 8000
    external = 8000
  }

  volumes {
    host_path      = abspath("${path.cwd}/..")
    container_path = "/app/kometizarr"
  }

  volumes {
    host_path      = abspath("${path.cwd}/../data/backups")
    container_path = "/backups"
  }

  volumes {
    host_path      = abspath("${path.cwd}/../data/temp")
    container_path = "/temp"
  }

  env = [
    "PLEX_URL=${var.plex_url}",
    "PLEX_TOKEN=${var.plex_token}",
    "TMDB_API_KEY=${var.tmdb_api_key}",
    "OMDB_API_KEY=${var.omdb_api_key}",
    "MDBLIST_API_KEY=${var.mdblist_api_key}",
  ]
}

# Frontend container
resource "docker_container" "kometizarr_frontend" {
  name  = "kometizarr-frontend"
  image = docker_image.kometizarr_frontend.name

  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.kometizarr.name
  }

  ports {
    internal = 80
    external = 3001
  }

  depends_on = [
    docker_container.kometizarr_backend
  ]
}

# Backend image
# NOTE: Pre-built images are pulled from GitHub Container Registry
# If you want to build locally instead, uncomment the build block below
resource "docker_image" "kometizarr_backend" {
  name         = "ghcr.io/p2chill/kometizarr-backend:latest"
  keep_locally = true  # Don't delete image when destroyed

  # Uncomment to build locally instead of pulling from registry:
  # build {
  #   context    = abspath("${path.cwd}/../web/backend")
  #   dockerfile = "Dockerfile"
  #   tag        = ["kometizarr-backend:latest"]
  # }
}

# Frontend image
# NOTE: Pre-built images are pulled from GitHub Container Registry
# If you want to build locally instead, uncomment the build block below
resource "docker_image" "kometizarr_frontend" {
  name         = "ghcr.io/p2chill/kometizarr-frontend:latest"
  keep_locally = true  # Don't delete image when destroyed

  # Uncomment to build locally instead of pulling from registry:
  # build {
  #   context    = abspath("${path.cwd}/../web/frontend")
  #   dockerfile = "Dockerfile"
  #   tag        = ["kometizarr-frontend:latest"]
  # }
}
