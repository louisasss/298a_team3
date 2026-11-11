.PHONY: versions terraform-fmt cloud-validate cloud-bootstrap-init cloud-bootstrap-plan cloud-bootstrap-apply cloud-init cloud-plan cloud-apply cloud-ready cloud-destroy-plan cloud-destroy

TF_STATE_BUCKET ?= $(GCP_PROJECT_ID)-tfstate
TF_STATE_PREFIX ?= cluster
GCP_PROJECT_ID ?=
GCP_REGION ?= us-central1
GCP_ZONE ?= us-central1-a
CLUSTER_NAME ?= d298a-dev
NODE_SERVICE_ACCOUNT_EMAIL ?=
CONFIRM_CLOUD ?= no

versions:
	@echo "=== Team Tool Versions ==="
	@python3 --version
	@kubectl version --client
	@kind version
	@helm version --short
	@kubectl argo rollouts version
	@argocd version --client
	@terraform version
	@gcloud version

terraform-fmt:
	terraform fmt -recursive infra

cloud-validate:
	terraform -chdir=infra/bootstrap init -backend=false
	terraform -chdir=infra/bootstrap validate
	terraform -chdir=infra/cluster init -backend=false
	terraform -chdir=infra/cluster validate

cloud-bootstrap-init:
	@test -n "$(GCP_PROJECT_ID)" || (echo "Set GCP_PROJECT_ID before initializing bootstrap." && exit 1)
	terraform -chdir=infra/bootstrap init

cloud-bootstrap-plan: cloud-bootstrap-init
	terraform -chdir=infra/bootstrap plan -var="project_id=$(GCP_PROJECT_ID)"

cloud-bootstrap-apply: cloud-bootstrap-init
	@test "$(CONFIRM_CLOUD)" = "yes" || (echo "Refusing cloud changes. Set CONFIRM_CLOUD=yes after reviewing the plan." && exit 1)
	terraform -chdir=infra/bootstrap apply -var="project_id=$(GCP_PROJECT_ID)"

cloud-init: cloud-validate
	@test -n "$(GCP_PROJECT_ID)" || (echo "Set GCP_PROJECT_ID before initializing the cluster backend." && exit 1)
	@test -n "$(TF_STATE_BUCKET)" || (echo "Set TF_STATE_BUCKET to the bootstrap bucket name." && exit 1)
	terraform -chdir=infra/cluster init -backend-config="bucket=$(TF_STATE_BUCKET)" -backend-config="prefix=$(TF_STATE_PREFIX)"

cloud-plan: cloud-init
	terraform -chdir=infra/cluster plan -var="project_id=$(GCP_PROJECT_ID)" -var="region=$(GCP_REGION)" -var="zone=$(GCP_ZONE)" -var="cluster_name=$(CLUSTER_NAME)" var="node_service_account_email=$(NODE_SERVICE_ACCOUNT_EMAIL)" -out=tfplan

cloud-apply: cloud-plan
	@test "$(CONFIRM_CLOUD)" = "yes" || (echo "Refusing cloud changes. Set CONFIRM_CLOUD=yes after reviewing the plan." && exit 1)
	terraform -chdir=infra/cluster apply tfplan

cloud-ready:
	@test -n "$(GCP_PROJECT_ID)" || (echo "Set GCP_PROJECT_ID before checking readiness." && exit 1)
	gcloud container clusters get-credentials "$(CLUSTER_NAME)" --zone "$(GCP_ZONE)" --project "$(GCP_PROJECT_ID)"
	kubectl wait --for=condition=Ready nodes --all --timeout=10m

cloud-destroy-plan: cloud-init
	terraform -chdir=infra/cluster plan -destroy -var="project_id=$(GCP_PROJECT_ID)" -var="region=$(GCP_REGION)" -var="zone=$(GCP_ZONE)" -var="cluster_name=$(CLUSTER_NAME)" var="node_service_account_email=$(NODE_SERVICE_ACCOUNT_EMAIL)"

cloud-destroy: cloud-init
	@test "$(CONFIRM_CLOUD)" = "yes" || (echo "Refusing cloud destruction. Set CONFIRM_CLOUD=yes after reviewing the destroy plan." && exit 1)
	terraform -chdir=infra/cluster destroy -var="project_id=$(GCP_PROJECT_ID)" -var="region=$(GCP_REGION)" -var="zone=$(GCP_ZONE)" -var="cluster_name=$(CLUSTER_NAME)" var="node_service_account_email=$(NODE_SERVICE_ACCOUNT_EMAIL)" -auto-approve

.PHONY: cloud-smoke
cloud-smoke: cloud-ready
	 kubectl create namespace d298a-smoke --dry-run=client -o yaml | kubectl apply -f -
	 kubectl -n d298a-smoke create deployment smoke --image=busybox:1.36 -- /bin/sh -c 'sleep 60'
	 kubectl -n d298a-smoke rollout status deployment/smoke --timeout=5m
	 kubectl delete namespace d298a-smoke --wait=true



