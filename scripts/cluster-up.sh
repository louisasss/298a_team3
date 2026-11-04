#!/usr/bin/env bash
set -euo pipefail   # -e: stop the script if a command fails, -u: stop if you try to use a variable that was never set, -o pipefail: if any command in a pipeline fails, treat whole pipeline as failed

CLUSTER_NAME="canary-pipeline"

echo "Creating kind cluster: ${CLUSTER_NAME}"

kind create cluster \
  --name "${CLUSTER_NAME}"

echo "Waiting for Kubernetes node to become Ready..."

kubectl wait \
  --for=condition=Ready \
  node \
  --all \
  --timeout=120s
echo "Kind cluster '${CLUSTER_NAME}' is ready."