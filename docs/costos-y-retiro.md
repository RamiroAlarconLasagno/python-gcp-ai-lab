<!-- docs/costos-y-retiro.md -->
# Costos y retiro de la infraestructura

La infraestructura en GCP vive del **25 al 30 de noviembre de 2026** y se retira en el bloque B6. Ciclo: desplegar → verificar → documentar → retirar.

## Qué cobra aunque la app esté detenida

Precios de Cloud SQL para PostgreSQL, edición Enterprise, región `us-central1`. Fuente: página oficial de precios de Cloud SQL (<https://cloud.google.com/sql/pricing>), consultada por Ramiro el 2026-11-23.

| Recurso | Precio | Por día | Por semana | ¿Cobra sin tráfico? |
|---|---|---|---|---|
| Instancia Cloud SQL `db-f1-micro` | US$0,0105/h | US$0,252 | US$1,76 | **Sí**, mientras exista (aunque esté ociosa) |
| Disco SSD de 10 GiB | US$0,000232877/GiB-h | US$0,056 | US$0,39 | **Sí** |
| IP pública de la instancia | US$0,01/h | US$0,240 | US$1,68 | **Sí** |
| **Total Cloud SQL** | US$0,0228/h | **≈ US$0,55** | **≈ US$3,84** | |

Para la ventana del 25 al 30 de noviembre (6 días): ≈ **US$3,30**.

Otros recursos (precios no verificados en esta etapa; con este volumen son centavos o entran en el nivel gratuito):

| Recurso | Cobra sin tráfico | Nota |
|---|---|---|
| Artifact Registry (repo `quotes`) | Sí, por GB almacenado | Cada imagen ocupa ~100 MB; las imágenes se acumulan si no se borran. |
| Bucket del estado de Terraform | Sí, por GB almacenado | Unos KB; guarda hasta 5 versiones viejas de cada estado. |
| Secret Manager (`quotes-db-password`) | Sí, por versión activa | Una versión. |
| Cloud Run (servicio y job) | **No** | Mínimo 0 instancias: solo cobra mientras atiende o mientras corre el job. |
| APIs habilitadas | No | Quedan habilitadas después del retiro. |

## Cómo se retira (bloque B6)

Pasos en orden. Ejecutar desde la raíz del repo, en PowerShell o Git Bash.

1. **Inventario inicial**, para comparar después: `bash scripts/inventario.sh > inventario-antes.txt`
2. **Destruir la infraestructura** (Cloud Run, Cloud SQL, secreto, cuenta de servicio, IAM, Artifact Registry). Necesita una imagen cualquiera en la variable, porque es obligatoria:
   ```
   terraform -chdir=infra destroy -var "image=unused"
   ```
   Revisar que el plan diga `0 to add, 0 to change, N to destroy` y confirmar con `yes`. Cloud SQL tarda unos minutos.
3. **Lo que Terraform no gestiona:**
   - Imágenes en Artifact Registry: se borran con el repositorio en el paso 2. Si el repo no se borró por tener imágenes: `gcloud artifacts repositories delete quotes --location us-central1`.
   - Backups de Cloud SQL: los automáticos están desactivados; comprobar con el inventario que no queda ninguno manual.
   - Repos `gcf-artifacts` que crea Cloud Functions (si alguna etapa la usó): `gcloud artifacts repositories list` y borrarlos.
   - La credencial de Docker para Artifact Registry (local, no cobra): quitar `us-central1-docker.pkg.dev` de `credHelpers` en `%USERPROFILE%\.docker\config.json`.
4. **Destruir el bucket del estado** (al final, porque guarda el estado del paso 2):
   ```
   terraform -chdir=infra/bootstrap destroy
   ```
   `force_destroy = true` borra también las versiones viejas del estado.
5. **Inventario final**: `bash scripts/inventario.sh` no debe listar instancias de Cloud SQL, servicios ni jobs de Cloud Run, buckets, repos de Artifact Registry ni secretos del laboratorio.
6. Al día siguiente, revisar en Facturación → Informes que el costo diario de Cloud SQL bajó a cero.

Nota: un nombre de instancia de Cloud SQL borrada no se puede reutilizar durante un tiempo; por eso el nombre lleva un sufijo aleatorio (`random_id`) y un `apply` posterior crea otro nombre.
