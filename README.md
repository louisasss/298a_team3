# 298a_team3

Autonomous DevOps Engineer and Self-Healing CI/CD

## Team

Sang Ah Lee, Pragya Priyadarshini, Louisa Stumpf, Akshit Tyagi

## Environments

- Python: 3.10

## Development Environment

This project uses a Docker-based development container to provide a consistent toolchain across team machines.

### Pinned tools

The development container includes:

- Python 3.10
- kubectl
- kind
- Helm
- Argo Rollouts CLI
- Argo CD CLI

To verify the installed tool versions, run:

```bash
make versions
```

### VS Code

1. Install Docker Desktop and make sure it is running.
2. Install the VS Code **Dev Containers** extension.
3. Open the repository in VS Code.
4. Open the Command Palette and select **Dev Containers: Reopen in Container**.
5. Run:

```bash
make versions
```

### Other editors

The development environment can also be built directly with Docker:

```bash
docker build -t 298a-team3-dev .devcontainer
```

Then run it from the repository root:

```bash
docker run --rm -it \
  -v "$PWD:/workspace" \
  -w /workspace \
  298a-team3-dev \
  bash
```

## Repository Structure

- `app/` — application source code, tests, and migrations
- `k8s/` — Kubernetes manifests and Kustomize overlays
- `argocd/` — Argo CD application definitions
- `platform/` — platform configuration for Prometheus, Argo Rollouts, and Argo CD
- `load/` — load-generation configuration
- `scenarios/` — failure-injection scenarios
- `scoring/` — agent evaluation and scoring utilities
- `infra/` — cloud infrastructure and Terraform configuration
- `scripts/` — cluster and platform automation scripts
- `docs/` — architecture decisions, contracts, and project documentation
- `.github/` — GitHub workflows and pull request configuration
- `.devcontainer/` — reproducible development environment

## Makefile Targets

Current targets:

- `make versions` — display the versions of the team development tools

Additional targets will be added as the cluster, platform, deployment, and evaluation workflows are implemented.