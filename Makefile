.PHONY: versions cluster-up cluster-down

versions:
	@echo "=== Team Tool Versions ==="
	@python3 --version
	@kubectl version --client
	@kind version
	@helm version --short
	@kubectl argo rollouts version
	@argocd version --client

cluster-up:
	./scripts/cluster-up.sh

cluster-down:
	./scripts/cluster-down.sh