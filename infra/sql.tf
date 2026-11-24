# infra/sql.tf
# Smallest Cloud SQL for PostgreSQL instance (lab): shared core, zonal, no backups,
# no deletion protection. It bills while it exists, even with no traffic.

resource "random_id" "sql_suffix" {
  byte_length = 3
}

locals {
  sql_suffix = var.sql_suffix != "" ? var.sql_suffix : random_id.sql_suffix.hex
}

resource "google_sql_database_instance" "main" {
  name             = "quotes-${local.sql_suffix}"
  database_version = "POSTGRES_17"
  region           = var.region

  # Terraform-level protection off so the lab can be retired with terraform destroy.
  deletion_protection = false

  settings {
    edition           = "ENTERPRISE"
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = false
    user_labels       = local.labels

    deletion_protection_enabled = false

    backup_configuration {
      enabled = false
    }

    # Public IP without authorized networks: only the Cloud SQL connector
    # (IAM-checked, used by the Cloud Run integration) can reach it.
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_sql_database" "app" {
  name     = "quotes"
  instance = google_sql_database_instance.main.name
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_user" "app" {
  name     = "quotes"
  instance = google_sql_database_instance.main.name
  password = random_password.db.result

  # PostgreSQL cannot drop a user that owns objects; deleting the instance removes it.
  deletion_policy = "ABANDON"
}
