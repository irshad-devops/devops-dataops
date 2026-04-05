terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project     = "marwat-project"
  region      = "us-central1"
  zone        = "us-central1-a"
  credentials = file("marwat-project-253f9fdf3912.json")
}


