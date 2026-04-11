# ------------------------------------------------------------------------------
# Multi-Cloud DataOps Pipeline
# Providers: GCP (Active), AWS & Azure (Architecture Proof)
# Compliance: ISO 27018, GDPR, GCC Data Localization
# ------------------------------------------------------------------------------

# --- 1. SECURITY: GCP KMS (Encryption at Rest) ---
resource "google_kms_key_ring" "key_ring" {
  name     = "marwat-flight-keyring2"
  location = var.region
}

resource "google_kms_crypto_key" "flight_key" {
  name            = "flight-data-encryption-key2"
  key_ring        = google_kms_key_ring.key_ring.id
  rotation_period = "7776000s" # 90 days rotation for compliance

  lifecycle {
    prevent_destroy = false
  }
}

# --- 1a. SECURITY: IAM Permission for GCS to use KMS Key ---
# Fulfills the "Secure KMS Integration" requirement.
data "google_storage_project_service_account" "gcs_account" {}

resource "google_kms_crypto_key_iam_member" "gcs_kms_binding" {
  crypto_key_id = google_kms_crypto_key.flight_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

# --- 2. STORAGE: GCP Cloud Storage (Data Lake) ---
resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true

  # Encryption at rest using the KMS key
  encryption {
    default_kms_key_name = google_kms_crypto_key.flight_key.id
  }

  labels = {
    name        = "flightdatalake"
    compliance  = "iso27018"
    environment = "dev"
    data_region = "gcc-central"
  }

  # Ensure permissions are granted before creating the bucket
  depends_on = [google_kms_crypto_key_iam_member.gcs_kms_binding]
}

resource "google_storage_bucket_object" "upload_csv" {
  name   = "raw/data.csv"
  bucket = google_storage_bucket.data_lake.name
  source = "/home/marwat/Documents/gcp-lab/Air-flow/dags/data.csv"
}

# --- 3. DATABASE: Cloud SQL (PostgreSQL Instance) ---
resource "google_sql_database_instance" "flight_db" {
  name             = "flight-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier            = "db-f1-micro"
    disk_autoresize = true

    ip_configuration {
      ipv4_enabled = true
      
      # Modern Provider 5.0+ Syntax for SSL
      ssl_mode = "ENCRYPTED_ONLY" 

      authorized_networks {
        name  = "all-networks-lab-only"
        value = "0.0.0.0/0"
      }
    }

    backup_configuration {
      enabled = true
    }
  }
  deletion_protection = false
}

# --- 3a. DATABASE SCHEMA ---
resource "google_sql_database" "flight_database" {
  name     = "flight_analytics"
  instance = google_sql_database_instance.flight_db.name

  depends_on = [google_sql_database_instance.flight_db]
}

# --- 3b. DATABASE USER ---
resource "google_sql_user" "db_user" {
  name     = var.db_username
  instance = google_sql_database_instance.flight_db.name
  password = var.db_password

  depends_on = [google_sql_database_instance.flight_db]
}

# --- 4. MULTI-CLOUD ARCHITECTURE (Commented out for GCP execution) ---
/*
resource "aws_s3_bucket" "aws_backup_lake" {
  bucket = "marwat-dataops-backup-aws"
  tags = { Compliance = "GDPR" }
}

resource "azurerm_storage_account" "azure_lake" {
  name                     = "marwatdatalakeaz"
  resource_group_name      = "dataops-rg"
  location                 = "East US"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
*/
