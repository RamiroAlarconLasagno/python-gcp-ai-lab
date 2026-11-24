# infra/registry.tf
# Docker repository for the API image.

resource "google_artifact_registry_repository" "docker" {
  repository_id = "quotes"
  location      = var.region
  format        = "DOCKER"
  description   = "API images of the shipping quote lab."

  depends_on = [google_project_service.enabled]
}
