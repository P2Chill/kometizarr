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
  image = docker_image.kometizarr_backend.image_id

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
  image = docker_image.kometizarr_frontend.image_id

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
resource "docker_image" "kometizarr_backend" {
  name = "kometizarr-backend:latest"

  build {
    context    = abspath("${path.cwd}/../web/backend")
    dockerfile = "Dockerfile"
    tag        = ["kometizarr-backend:latest"]
  }
}

# Frontend image
resource "docker_image" "kometizarr_frontend" {
  name = "kometizarr-frontend:latest"

  build {
    context    = abspath("${path.cwd}/../web/frontend")
    dockerfile = "Dockerfile"
    tag        = ["kometizarr-frontend:latest"]
  }
}
