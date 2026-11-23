#!/usr/bin/env bash
set -euo pipefail
# -e: stop if a command fails
# -u: stop if an unset variable is used
# -o pipefail: fail if any command in a pipeline fails

CLUSTER_NAME="canary-pipeline"
TRAEFIK_CHART_VERSION="42.3.0"

echo "Creating kind cluster: ${CLUSTER_NAME}"

kind create cluster \
  --name "${CLUSTER_NAME}" \
  --config scripts/kind-config.yaml

echo "Waiting for Kubernetes node to become Ready..."

kubectl wait \
  --for=condition=Ready \
  node \
  --all \
  --timeout=120s

echo "Adding Traefik Helm repository..."

helm repo add traefik https://traefik.github.io/charts --force-update
helm repo update

echo "Installing Traefik ingress controller..."

helm upgrade --install traefik traefik/traefik \
  --namespace traefik \
  --create-namespace \
  --version "${TRAEFIK_CHART_VERSION}" \
  --values scripts/traefik-values.yaml \
  --wait \
  --timeout 5m

echo "Waiting for Traefik to become Ready..."

kubectl rollout status deployment/traefik \
  --namespace traefik \
  --timeout=180s

echo "Kind cluster '${CLUSTER_NAME}' with Traefik is ready."
