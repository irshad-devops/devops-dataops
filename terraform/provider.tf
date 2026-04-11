terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  # Replace with your actual GCP Project ID
  project     = "marwat-project" 
  region      = var.region
  credentials = file("gcp-key.json")
}
