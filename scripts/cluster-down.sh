#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="canary-pipeline"

echo "Deleting kind cluster: ${CLUSTER_NAME}"

kind delete cluster \
  --name "${CLUSTER_NAME}"

echo "Kind cluster '${CLUSTER_NAME}' deleted successfully."