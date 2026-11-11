# Cloud infrastructure

This directory contains two independent Terraform roots:

- bootstrap: persistent GCS state bucket, deployment identities, required APIs, and optional budget notification channels.
- cluster: disposable VPC, subnet secondary ranges, GKE Standard zonal cluster, and one managed node pool.

The bootstrap bucket must exist before the cluster backend is initialized.
The two roots use separate GCS prefixes and must never share a state object.

## Workflow

1. Create a GCP project, link billing, and authenticate with an individual operator identity.
2. Copy the example tfvars files to local, untracked terraform.tfvars files.
3. Run make terraform-fmt and make cloud-validate.
4. Review and apply bootstrap with make cloud-bootstrap-plan GCP_PROJECT_ID=..., then make cloud-bootstrap-apply GCP_PROJECT_ID=... CONFIRM_CLOUD=yes.
5. Use the bootstrap output bucket name as TF_STATE_BUCKET, review make cloud-plan, then apply with make cloud-apply CONFIRM_CLOUD=yes.
6. Run make cloud-ready and record readiness evidence.
7. Review and run make cloud-destroy-plan, then make cloud-destroy CONFIRM_CLOUD=yes.

Apply and destroy require explicit confirmation. The targets do not create a
project or billing account and never disable Terraform state locking.

GCS backend locking is automatic. Object versioning is enabled for recovery.
Never use -lock=false. Force unlock is only for a lock owned by the operator
after an interrupted run. The cloud owner retains independent recovery access.
No service-account JSON key or Terraform state file belongs in Git.
