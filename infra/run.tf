# infra/run.tf
# Private Cloud Run service (no allUsers invoker) and the migration job.
# Both use the same image, identity and Cloud SQL connection.

locals {
  db_env = {
    DB_USER                  = google_sql_user.app.name
    DB_NAME                  = google_sql_database.app.name
    INSTANCE_CONNECTION_NAME = google_sql_database_instance.main.connection_name
  }
}

resource "google_cloud_run_v2_service" "api" {
  name                = "quotes-api"
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    # Built-in Cloud SQL connection: a Unix socket under /cloudsql/<connection name>.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    containers {
      image = var.image

      dynamic "env" {
        for_each = local.db_env
        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  depends_on = [
    google_project_iam_member.runtime_sql_client,
    google_secret_manager_secret_iam_member.runtime_db_password,
    google_secret_manager_secret_version.db_password,
  ]
}

resource "google_cloud_run_v2_job" "migrate" {
  name                = "quotes-migrate"
  location            = var.region
  deletion_protection = false

  template {
    task_count = 1

    template {
      service_account = google_service_account.runtime.email
      max_retries     = 0
      timeout         = "300s"

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }

      containers {
        image   = var.image
        command = ["alembic"]
        args    = ["upgrade", "head"]

        dynamic "env" {
          for_each = local.db_env
          content {
            name  = env.key
            value = env.value
          }
        }

        env {
          name = "DB_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }
  }

  depends_on = [
    google_project_iam_member.runtime_sql_client,
    google_secret_manager_secret_iam_member.runtime_db_password,
    google_secret_manager_secret_version.db_password,
  ]
}
