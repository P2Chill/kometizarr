# Kometizarr Terraform Configuration

Deploy Kometizarr containers using Terraform for infrastructure-as-code management.

## Prerequisites

- Terraform 1.0+ ([Download](https://www.terraform.io/downloads))
- Docker installed and running
- Git (to clone the repository)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/P2Chill/kometizarr.git
cd kometizarr/terraform
```

### 2. Create Variables File

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your credentials:
```hcl
plex_url        = "http://192.168.1.20:32400"
plex_token      = "your_actual_plex_token"
tmdb_api_key    = "your_actual_tmdb_key"
omdb_api_key    = "your_actual_omdb_key"  # Optional
mdblist_api_key = "your_actual_mdblist_key"
```

**How to get your Plex token:** https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Review the Plan

```bash
terraform plan
```

This shows you what Terraform will create:
- `docker_network.kometizarr` - Isolated network
- `docker_image.kometizarr_backend` - Backend image
- `docker_image.kometizarr_frontend` - Frontend image
- `docker_container.kometizarr_backend` - Backend container (port 8000)
- `docker_container.kometizarr_frontend` - Frontend container (port 3001)

### 5. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted.

### 6. Access the Web UI

Open your browser to:
```
http://localhost:3001
```

## What Gets Created

### Containers
- **kometizarr-backend** - FastAPI backend on port 8000
- **kometizarr-frontend** - React frontend on port 3001

### Network
- **kometizarr** - Bridge network for container communication

### Volumes
- `/path/to/kometizarr` → `/app/kometizarr` (project files)
- `/path/to/kometizarr/data/backups` → `/backups` (poster backups)
- `/path/to/kometizarr/data/temp` → `/temp` (temporary processing)

All paths are calculated automatically based on where you cloned the repository.

## Managing Containers

### View Status

```bash
terraform show
```

### Update to Latest Version

Kometizarr images are pulled from GitHub Container Registry. To update:

```bash
terraform apply
```

Terraform will automatically pull the latest `:latest` tag. For specific versions, edit `kometizarr.tf` to use version tags like `:v1.0.6`.

### Stop Containers

```bash
terraform destroy
```

This removes all containers, images, and networks. Your data in `data/backups` is preserved.

## Troubleshooting

### "Error: Duplicate required providers configuration"

This happens if you're integrating with existing Terraform configs. Remove the `terraform {}` block from `providers.tf` and let your main config handle provider versions.

### Images won't pull

If you get errors pulling images from the registry:
1. Check Docker daemon is running: `docker ps`
2. Try pulling manually: `docker pull ghcr.io/p2chill/kometizarr-backend:latest`
3. Check your internet connection
4. Alternative: Use Docker Hub instead by editing `kometizarr.tf` to use `p2chill/kometizarr-*` images

### Containers won't start

Check Docker is running:
```bash
docker ps
```

Check logs:
```bash
docker logs kometizarr-backend
docker logs kometizarr-frontend
```

### Port already in use

If ports 3001 or 8000 are already in use, edit `kometizarr.tf` and change the `external` port numbers.

## Notes

- **Pre-built Images:** Images are pulled from GitHub Container Registry (no build required)
- **Version Pinning:** Use `:latest` for auto-updates or `:v1.0.6` for stable versions
- **Sensitive Variables:** API keys and tokens are marked as sensitive (won't show in logs)
- **State Management:** Terraform state is stored locally in `.terraform/`
- **Git Safety:** The `.gitignore` prevents committing secrets

## Advanced: Integration with Existing Terraform

If you already manage infrastructure with Terraform:

1. **Copy files to your terraform directory:**
   ```bash
   cp kometizarr.tf /path/to/your/terraform/
   ```

2. **Add variables to your existing `variables.tf`** or create `kometizarr_variables.tf`

3. **Add values to your `terraform.tfvars`**

4. **Remove `providers.tf`** (use your existing provider config)

5. **Adjust paths** if running from a different directory:
   ```hcl
   # Example: if running from ~/terraform and kometizarr is at ~/kometizarr
   host_path = "/home/user/kometizarr"
   ```

## Cleanup

To completely remove Kometizarr:

```bash
terraform destroy
rm -rf .terraform/ terraform.tfstate*
```

This removes all containers, images, networks, and Terraform state. Backup data in `../data/backups` is **NOT** deleted.
