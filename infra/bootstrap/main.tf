# infra/bootstrap/main.tf
# Remote state bucket for infra/. This root keeps its own state LOCAL (not committed):
# it is applied once at the start and destroyed last, after infra/ is gone.

terraform {
  required_version = ">= 1.17"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.12"
    }
  }
}

variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
  default     = "python-gcp-ai-lab"
}

variable "region" {
  description = "Region for the bucket."
  type        = string
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region

  default_labels = {
    lab = "gcp-ai"
  }
}

resource "google_storage_bucket" "tfstate" {
  name     = "${var.project_id}-tfstate"
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # Lab: allows destroying the bucket together with its state versions at the very end.
  force_destroy = true

  versioning {
    enabled = true
  }

  # Keep only the last 5 old versions of each state file.
  lifecycle_rule {
    condition {
      num_newer_versions = 5
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }
}

output "state_bucket" {
  description = "Bucket name to use in the gcs backend of infra/."
  value       = google_storage_bucket.tfstate.name
}
