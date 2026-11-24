# infra/versions.tf
# Terraform, providers and remote state (bucket created by infra/bootstrap/).

terraform {
  required_version = ">= 1.17"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.9"
    }
  }

  # Backend blocks cannot use variables: the bucket name is fixed here.
  backend "gcs" {
    bucket = "python-gcp-ai-lab-tfstate"
    prefix = "infra"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Applied to every resource that supports labels (Cloud SQL uses user_labels).
  default_labels = local.labels
}

locals {
  labels = {
    lab = "gcp-ai"
  }
}
