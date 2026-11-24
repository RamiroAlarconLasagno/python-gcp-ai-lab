<!-- docs/design/003-terraform.md -->
# ND-003: All cloud infrastructure in Terraform, with remote state

- **Status:** proposed
- **Date:** 2026-11-24
- **Authoring:** AI-assisted draft, to be reviewed by Ramiro.

## Context

The lab follows a short cycle: deploy, verify, document, retire. The cloud infrastructure exists only from 2026-11-25 to 2026-11-30. Retiring it completely, and being able to recreate it later from code, matters more than speed of first setup. Resources that bill while idle (Cloud SQL) must not be forgotten.

## Decision

1. **Everything in Terraform.** Every resource in `infra/` is declared in Terraform: APIs, Artifact Registry, service account and IAM, Cloud SQL, the secret, the Cloud Run service and the migration job. Only three things stay out:
   - building and pushing the image (`docker build` and `push`);
   - running the migration job;
   - the state bucket itself.
2. **Remote state in GCS.** `infra/bootstrap/` creates a private, versioned bucket, and `infra/` uses it as its `gcs` backend. The bootstrap root keeps its own small state locally and uncommitted. It is applied once and destroyed last.
3. **Flat files, no modules.** Each concern has its own file (`sql.tf`, `run.tf`, and so on). A module is only worth it when the same block repeats at least three times.
4. **Pinned providers.** `google ~> 8.12` and `random ~> 3.9`, with `.terraform.lock.hcl` committed.

## Why

- **Complete, verifiable retirement.** `terraform destroy` removes exactly what was created, including resources that are easy to forget by hand (IAM bindings, the secret, the job). Afterwards `scripts/inventario.sh` confirms that nothing billable remains.
- **Reproducible.** The same `apply` recreates the environment. A second `plan` showing `No changes` proves the code matches reality.
- **Reviewable changes.** `plan -out` followed by `apply <plan>` applies exactly what was reviewed. This is how the Cloud SQL creation was approved before it was applied.
- **Remote state.** It survives the local machine. Versioning allows recovering a previous state if a run corrupts it. GCS supports state locking, so two concurrent runs cannot overwrite each other.

## Consequences

- **Secrets in state.** The database password is in the state (`random_password` and the secret version). The bucket is private, with public access prevention enforced and uniform access. State, plans and `*.tfvars` are never committed.
- **A deploy is two steps.** The image must exist before the Cloud Run service can be created. The first deployment therefore used `apply -target` for the APIs, Artifact Registry and the service account, then a push, then a full `apply`. Later deploys only change the `image` variable.
- **The backend bucket name is hard-coded** in `versions.tf`, because backend blocks cannot use variables.
- **Local tooling issue.** On the author's machine, Avast breaks the local TLS link between Terraform and its providers. The fix is an antivirus exception, not a change in the code (see stage 1.4).
- **Not yet in Terraform:** CI/CD with Workload Identity Federation (stage 4.3).
