
# -----------------------------
# Cloud Storage Bucket (Data Lake)
# -----------------------------
resource "google_storage_bucket" "data_lake" {
  name     = var.bucket_name
  location = var.region

  uniform_bucket_level_access = true

  labels = {
    name        = "flightdatalake"
    compliance  = "iso27018"
    environment = "dev"
  }
}

# -----------------------------
# Upload CSV to GCS
# -----------------------------
resource "google_storage_bucket_object" "upload_csv" {
  name   = "raw/data.csv"
  bucket = google_storage_bucket.data_lake.name
  source = "/home/marwat/Documents/gcp-lab/Air-flow/dags/data.csv"
}

# -----------------------------
# Cloud SQL Instance (PostgreSQL)
# -----------------------------
resource "google_sql_database_instance" "flight_db" {
  name             = "flight-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    disk_autoresize = true

    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = false
}

# -----------------------------
# Create Database
# -----------------------------
resource "google_sql_database" "flight_database" {
  name     = "flight_analytics"
  instance = google_sql_database_instance.flight_db.name
}

# -----------------------------
# Create Database User
# -----------------------------
resource "google_sql_user" "db_user" {
  name     = var.db_username
  instance = google_sql_database_instance.flight_db.name
  password = var.db_password
}

