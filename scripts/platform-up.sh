#!/usr/bin/env bash
set -euo pipefail

ARGO_ROLLOUTS_CHART_VERSION="2.43.8"
ARGOCD_CHART_VERSION="10.11.7"
PROMETHEUS_CHART_VERSION="92.14.1"

echo "Adding Helm repositories..."

helm repo add argo https://argoproj.github.io/argo-helm --force-update
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update

helm repo update

echo "Installing Argo Rollouts..."

helm upgrade --install argo-rollouts argo/argo-rollouts \
  --namespace argo-rollouts \
  --create-namespace \
  --version "${ARGO_ROLLOUTS_CHART_VERSION}" \
  --values platform/argo-rollouts.yaml \
  --wait \
  --timeout 5m

echo "Installing Argo CD..."

helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --version "${ARGOCD_CHART_VERSION}" \
  --values platform/argo-cd.yaml \
  --wait \
  --timeout 10m

echo "Installing kube-prometheus-stack..."

helm upgrade --install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --version "${PROMETHEUS_CHART_VERSION}" \
  --values platform/kube-prometheus-stack.yaml \
  --wait \
  --timeout 10m

echo "Platform stack installed successfully."