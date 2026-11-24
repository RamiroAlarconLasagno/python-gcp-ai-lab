# infra/variables.tf

variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
  default     = "python-gcp-ai-lab"
}

variable "region" {
  description = "Region for Cloud Run, Cloud SQL and Artifact Registry."
  type        = string
  default     = "us-central1"
}

variable "image" {
  description = "Full image reference in Artifact Registry (REGION-docker.pkg.dev/PROJECT/REPO/NAME:TAG)."
  type        = string
}

variable "sql_suffix" {
  description = "Suffix for the Cloud SQL instance name. Empty: a random one (deleted names cannot be reused for a while)."
  type        = string
  default     = ""
}
