.PHONY: versions

versions:
	@echo "=== Team Tool Versions ==="
	@python3 --version
	@kubectl version --client
	@kind version
	@helm version --short
	@kubectl argo rollouts version
	@argocd version --client


.PHONY: db-setup
db-setup:
	cd app && alembic upgrade head && python -m src.seed

