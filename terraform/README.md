# Kometizarr Terraform Configuration

Terraform configuration for deploying Kometizarr containers on the Mini PC.

## Prerequisites

- Terraform 1.9.0+
- Docker Desktop running on WSL2
- Docker provider configured

## Setup

1. **Copy example variables:**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

2. **Edit `terraform.tfvars` with your credentials:**
```hcl
plex_url   = "http://192.168.1.20:32400"
plex_token = "your_actual_plex_token"

tmdb_api_key    = "your_actual_tmdb_key"
omdb_api_key    = "your_actual_omdb_key"
mdblist_api_key = "your_actual_mdblist_key"
```

3. **Initialize Terraform:**
```bash
terraform init
```

4. **Review the plan:**
```bash
terraform plan
```

5. **Apply the configuration:**
```bash
terraform apply
```

## What Gets Created

- **Network:** `kometizarr` (bridge network)
- **Backend Container:** `kometizarr-backend`
  - Port: 8000
  - Volumes: Project files, backups, temp
  - Environment: Plex & API credentials
- **Frontend Container:** `kometizarr-frontend`
  - Port: 3001
  - Serves React UI via Nginx

## Accessing Kometizarr

After deployment, access the Web UI at:
```
http://localhost:3001
```

## Updating Containers

When you make changes to the code:

```bash
terraform apply
```

Terraform will detect file changes and rebuild the images automatically.

## Destroying

To remove all Kometizarr containers and network:

```bash
terraform destroy
```

## Integration with Mini PC Terraform

You can add this to your main Mini PC Terraform configuration by:

1. **Copy to main terraform directory:**
```bash
cp terraform/kometizarr.tf ~/docker/terraform/
cp terraform/variables.tf ~/docker/terraform/kometizarr_variables.tf
```

2. **Add variables to main terraform.tfvars:**
```bash
# In ~/docker/terraform/terraform.tfvars
plex_token      = "your_token"
tmdb_api_key    = "your_key"
omdb_api_key    = "your_key"
mdblist_api_key = "your_key"
```

3. **Apply from main terraform:**
```bash
cd ~/docker/terraform
terraform apply
```

## Notes

- **Sensitive Variables:** All API keys and tokens are marked as sensitive
- **Auto-Rebuild:** Images rebuild automatically when source files change
- **State Management:** Local state stored in `.terraform/`
- **Git Safety:** `.gitignore` prevents committing secrets
