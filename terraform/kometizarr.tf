terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
  }
}

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
    name = docker_network.kometizarr.name
  }

  ports {
    internal = 8000
    external = 8000
  }

  volumes {
    host_path      = "/home/pieter/ai/kometizarr"
    container_path = "/app/kometizarr"
  }

  volumes {
    host_path      = "/tmp/kometizarr_backups"
    container_path = "/backups"
  }

  volumes {
    host_path      = "/tmp/kometizarr_temp"
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
    context    = "/home/pieter/ai/kometizarr/web/backend"
    dockerfile = "Dockerfile"
    tag        = ["kometizarr-backend:latest"]
  }

  triggers = {
    dir_sha1 = sha1(join("", [for f in fileset("/home/pieter/ai/kometizarr/web/backend", "**") : filesha1("/home/pieter/ai/kometizarr/web/backend/${f}")]))
  }
}

# Frontend image
resource "docker_image" "kometizarr_frontend" {
  name = "kometizarr-frontend:latest"

  build {
    context    = "/home/pieter/ai/kometizarr/web/frontend"
    dockerfile = "Dockerfile"
    tag        = ["kometizarr-frontend:latest"]
  }

  triggers = {
    dir_sha1 = sha1(join("", [for f in fileset("/home/pieter/ai/kometizarr/web/frontend", "**") : filesha1("/home/pieter/ai/kometizarr/web/frontend/${f}")]))
  }
}
