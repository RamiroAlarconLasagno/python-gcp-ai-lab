# infra/secrets.tf
# Database password in Secret Manager. The value is also in the Terraform state,
# which lives in the private, versioned state bucket.

resource "google_secret_manager_secret" "db_password" {
  secret_id = "quotes-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db.result
}
