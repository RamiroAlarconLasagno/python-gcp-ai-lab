# infra/iam.tf
# Runtime identity of the Cloud Run service and job, with minimal roles:
# connect to Cloud SQL and read only its own secret.

resource "google_service_account" "runtime" {
  account_id   = "quotes-runtime"
  display_name = "Quotes API runtime"

  depends_on = [google_project_service.enabled]
}

# Cloud SQL has no per-instance IAM: the client role is granted on the project.
resource "google_project_iam_member" "runtime_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = google_service_account.runtime.member
}

resource "google_secret_manager_secret_iam_member" "runtime_db_password" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.runtime.member
}
