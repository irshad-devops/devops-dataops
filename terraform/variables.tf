
variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "GCS bucket name"
  type        = string
  default     = "secure-flight-data"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "dbadmin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

