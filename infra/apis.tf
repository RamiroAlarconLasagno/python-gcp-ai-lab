# infra/apis.tf
# APIs the lab needs. They stay enabled on destroy (disabling them can break other
# resources, and an enabled API costs nothing by itself).

locals {
  services = [
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.services)

  service            = each.value
  disable_on_destroy = false
}
