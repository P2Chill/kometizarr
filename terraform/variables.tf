variable "plex_url" {
  description = "Plex server URL"
  type        = string
  default     = "http://192.168.1.20:32400"
}

variable "plex_token" {
  description = "Plex authentication token"
  type        = string
  sensitive   = true
}

variable "tmdb_api_key" {
  description = "TMDB API key"
  type        = string
  sensitive   = true
}

variable "omdb_api_key" {
  description = "OMDb API key (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "mdblist_api_key" {
  description = "MDBList API key (optional)"
  type        = string
  default     = ""
  sensitive   = true
}
