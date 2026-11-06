# Use Python 3.10 on Debian 12 (Bookworm) as the shared development environment.
# Pinning the base environment keeps development consistent across team machines.
FROM mcr.microsoft.com/devcontainers/python:1-3.10-bookworm

USER root

# Remove the unused Yarn APT source because its signing key can break apt updates
# + this project does not use Yarn.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        git \
        make \
    && rm -rf /var/lib/apt/lists/*

# Pin kubectl so all team members use the same Kubernetes client version
ARG KUBECTL_VERSION=v1.37.1

# Detect the container architecture (amd64/arm64), download kubectl, and make the binary executable
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSLo /usr/local/bin/kubectl \
       "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl


# Pin kind so all team members create local clusters with the same tool version
ARG KIND_VERSION=v0.33.0
# Download the correct kind binary for the container architecture
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSLo /usr/local/bin/kind \
       "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-${ARCH}" \
    && chmod +x /usr/local/bin/kind


# Helm so all team members use the same Kubernetes package manager ver
ARG HELM_VERSION=v4.3.1
# Download and install Helm for the container architecture
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSL \
       "https://get.helm.sh/helm-${HELM_VERSION}-linux-${ARCH}.tar.gz" \
       -o /tmp/helm.tar.gz \
    && tar -xzf /tmp/helm.tar.gz -C /tmp \
    && mv "/tmp/linux-${ARCH}/helm" /usr/local/bin/helm \
    && chmod +x /usr/local/bin/helm \
    && rm -rf /tmp/helm.tar.gz "/tmp/linux-${ARCH}"

# Pin Argo Rollouts kubectl plugin for canary rollout management
ARG ARGO_ROLLOUTS_VERSION=v1.10.1
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSLo /usr/local/bin/kubectl-argo-rollouts \
       "https://github.com/argoproj/argo-rollouts/releases/download/${ARGO_ROLLOUTS_VERSION}/kubectl-argo-rollouts-linux-${ARCH}" \
    && chmod +x /usr/local/bin/kubectl-argo-rollouts


# Argo CD CLI used to inspect and manage GitOps applications
ARG ARGOCD_VERSION=v3.5.7
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSLo /usr/local/bin/argocd \
       "https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-${ARCH}" \
    && chmod +x /usr/local/bin/argocd