terraform {
  required_version = ">= 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.6.2"
    }
  }
}

# Configure Docker provider
# This connects to the local Docker socket
provider "docker" {
  host = "unix:///var/run/docker.sock"
}
