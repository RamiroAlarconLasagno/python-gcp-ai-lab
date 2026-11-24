#!/usr/bin/env bash
# scripts/inventario.sh
# Lista los recursos del laboratorio que pueden generar costo. Solo lee; no cambia nada.
# Uso (Git Bash): bash scripts/inventario.sh [PROYECTO] [REGION]
set -u

PROJECT="${1:-python-gcp-ai-lab}"
REGION="${2:-us-central1}"

section() {
  printf '\n== %s ==\n' "$1"
}

# Corre un comando de listado sin preguntas interactivas; si falla, lo informa y sigue.
run() {
  "$@" --quiet 2>&1 || echo "(no se pudo listar)"
}

# APIs habilitadas, consultadas una sola vez. Si una API está apagada, no puede haber
# recursos de ese tipo: se informa y se salta la sección.
ENABLED_APIS="$(gcloud services list --enabled --project "$PROJECT" --format="value(config.name)" 2>/dev/null)"
if [ -z "$ENABLED_APIS" ]; then
  echo "No se pudieron listar las APIs habilitadas de ${PROJECT} (¿sesión de gcloud vencida?)." >&2
  exit 1
fi

api_on() {
  if grep -qx "$1" <<<"$ENABLED_APIS"; then
    return 0
  fi
  echo "(API $1 deshabilitada: no hay recursos de este tipo)"
  return 1
}

echo "Inventario del proyecto ${PROJECT} ($(date -u +%Y-%m-%dT%H:%M:%SZ))"

section "Cloud Run: servicios"
api_on run.googleapis.com && run gcloud run services list --project "$PROJECT" \
  --format="table(metadata.name,region,status.url,metadata.labels.lab)"

section "Cloud Run: jobs"
api_on run.googleapis.com && run gcloud run jobs list --project "$PROJECT" \
  --format="table(metadata.name,region,metadata.labels.lab)"

section "Cloud SQL: instancias (cobran aunque no haya tráfico)"
api_on sqladmin.googleapis.com && run gcloud sql instances list --project "$PROJECT" \
  --format="table(name,databaseVersion,region,settings.tier,state,settings.userLabels.lab)"

section "Cloud SQL: backups"
api_on sqladmin.googleapis.com &&
for instance in $(gcloud sql instances list --project "$PROJECT" --format="value(name)" 2>/dev/null); do
  echo "-- ${instance}"
  run gcloud sql backups list --instance "$instance" --project "$PROJECT" \
    --format="table(id,windowStartTime,type,status)"
done

section "GKE: clusters"
api_on container.googleapis.com && run gcloud container clusters list --project "$PROJECT" --format="table(name,location,status)"

section "Cloud Functions"
api_on cloudfunctions.googleapis.com && run gcloud functions list --project "$PROJECT" --format="table(name,state,environment)"

section "Cloud Storage: buckets"
run gcloud storage buckets list --project "$PROJECT" \
  --format="table(name,location,versioning_enabled,labels.lab)"

section "Artifact Registry: repositorios (incluye gcf-artifacts de Cloud Functions)"
api_on artifactregistry.googleapis.com && run gcloud artifacts repositories list --project "$PROJECT" \
  --format="table(name.basename(),format,location,sizeBytes,labels.lab)"

section "Artifact Registry: imágenes del repo quotes"
api_on artifactregistry.googleapis.com && run gcloud artifacts docker images list "${REGION}-docker.pkg.dev/${PROJECT}/quotes" \
  --include-tags --format="table(package.basename(),tags,createTime.date())"

section "Secret Manager: secretos"
api_on secretmanager.googleapis.com && run gcloud secrets list --project "$PROJECT" --format="table(name.basename(),createTime.date(),labels.lab)"

section "Pub/Sub: topics y suscripciones"
if api_on pubsub.googleapis.com; then
  run gcloud pubsub topics list --project "$PROJECT" --format="table(name.basename(),labels.lab)"
  run gcloud pubsub subscriptions list --project "$PROJECT" --format="table(name.basename(),topic.basename())"
fi

section "BigQuery: datasets"
api_on bigquery.googleapis.com && { bq ls --project_id "$PROJECT" 2>&1 || echo "(no se pudo listar)"; }

section "Workload Identity: pools"
api_on iam.googleapis.com && run gcloud iam workload-identity-pools list --location global --project "$PROJECT" \
  --format="table(name.basename(),state)"

section "Red: direcciones IP y forwarding rules (las reservadas cobran)"
if api_on compute.googleapis.com; then
  run gcloud compute addresses list --project "$PROJECT" --format="table(name,address,region,status)"
  run gcloud compute forwarding-rules list --project "$PROJECT" --format="table(name,region,IPAddress)"
fi
