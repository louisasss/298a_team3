#!/usr/bin/env bash
set -euo pipefail

echo "Adding Helm repositories for Argo Rollouts and Prometheus..."

helm repo add argo https://argoproj.github.io/argo-helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update

echo "Installing Argo Rollouts..."

helm upgrade --install argo-rollouts argo/argo-rollouts \
  --namespace argo-rollouts \
  --create-namespace \
  --version 2.43.8 \
  --values platform/argo-rollouts.yaml \
  --wait \
  --timeout 5m

echo "Argo Rollouts installed successfully."