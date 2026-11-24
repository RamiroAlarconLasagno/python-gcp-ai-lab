# infra/outputs.tf

output "service_url" {
  description = "URL of the private Cloud Run service (needs an identity token)."
  value       = google_cloud_run_v2_service.api.uri
}

output "registry" {
  description = "Docker registry path to tag and push images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "migrate_job" {
  description = "Cloud Run job that runs alembic upgrade head."
  value       = google_cloud_run_v2_job.migrate.name
}

output "sql_instance" {
  description = "Cloud SQL instance name (has a random suffix)."
  value       = google_sql_database_instance.main.name
}
