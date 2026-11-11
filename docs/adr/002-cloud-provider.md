# D298A — Cloud Infrastructure Requirements and Architecture Decisions

**Project:** AI-Augmented CI/CD Pipelines: From Code Commit to Production with Autonomous Decisions  
**Repository:** https://github.com/louisasss/298a_team3  
**Infrastructure issue:** Choose the cloud provider and provision the cluster with Terraform  
**Status:** Architecture decisions established; implementation and live acceptance testing pending  
**Cloud provider:** Google Cloud Platform (GCP)  
**Last updated:** November 10, 2026

---

# 1. Project Context and Infrastructure Objective

The D298A project aims to develop and evaluate an AI-augmented CI/CD system capable of detecting pipeline failures, analyzing incidents, recommending or executing remediation actions, and supporting self-healing deployment workflows.

The project follows a two-semester development structure.

**Semester 1 — DATA 298A**

- Reproduce one selected baseline model.
- Implement the first end-to-end CI/CD pipeline.
- Introduce the initial Stateful Graph-Orchestrated Incident Agent.
- Demonstrate an operational pipeline with agent integration.
- Establish reproducible infrastructure and evaluation foundations.

**Semester 2 — DATA 298B**

- Implement three additional progressively complex models.
- Extend the agent's decision-making and remediation capabilities.
- Complete end-to-end integration of the models and pipelines.
- Evaluate and compare models against the baseline using consistent metrics.

The cloud infrastructure must support the project's eventual Kubernetes-based CI/CD deployment and evaluation environment.

The initial infrastructure issue is foundational. It must not depend on unfinished model, agent, application, or evaluation components.

## 1.1 Existing repository findings

The uploaded repository snapshot was reviewed during planning.

The following directories were present but contained only placeholders:

- `infra/`
- `app/`
- `agents/agent1/`
- `agents/classifier/`
- `k8s/`
- `argocd/`
- `platform/`
- `scenarios/`
- `scoring/`
- `load/`

Additional findings:

- The root `Makefile` currently implements only the `versions` target.
- The `.github/` directory contains a pull request template but no implemented CI workflows.
- The development container includes tools such as Git, Make, kubectl, kind, Helm, Argo CD CLI, and Argo Rollouts CLI.
- Terraform, Google Cloud CLI, and the GKE authentication plugin are not explicitly installed in the existing development container.

Therefore, cloud infrastructure must be introduced without assuming that the application, agents, GitOps controllers, or monitoring stack are already operational.

The infrastructure should be designed to support future integration without prematurely provisioning expensive services.

---

# 2. Original Linear Issue

**Title:** Choose the cloud provider and provision the cluster with Terraform

## Deliverables

1. Architecture Decision Record:
   `docs/adr/002-cloud-provider.md`
2. Documented cloud provider, region, credit source, and teardown policy.
3. Estimated hourly and monthly infrastructure costs.
4. Billing budget and alert configuration.
5. Terraform remote state with locking.
6. Terraform-managed networking infrastructure.
7. Managed Kubernetes cluster.
8. Small Kubernetes worker node group.
9. Makefile targets for creating and destroying cloud infrastructure.
10. Evidence demonstrating successful provisioning, state locking, and teardown.

## Acceptance criteria

- ADR includes hourly and monthly cost estimates.
- A test budget notification reaches the team.
- Two teammates can independently run Terraform plans against the same remote state.
- Concurrent state-modifying Terraform operations are blocked by locking.
- Terraform apply from empty cluster state produces Ready Kubernetes nodes.
- Terraform destroy removes disposable billable resources.
- Resource deletion is independently checked in the cloud console.

**Dependencies:** None from the project's model or pipeline development tasks.

**Implementation target:** Terraform configuration, ADR, and Makefile changes ready for commit.

**Important distinction:** Code completion and successful live infrastructure acceptance testing are separate milestones.

---

# 3. Cloud Provider Selection

## 3.1 Providers evaluated

Four managed Kubernetes options were considered.

| Provider | Kubernetes service | Assessment |
|---|---|---|
| AWS | Elastic Kubernetes Service (EKS) | Technically suitable but comparatively expensive for the project's budget |
| Google Cloud | Google Kubernetes Engine (GKE) | Selected |
| Microsoft Azure | Azure Kubernetes Service (AKS) Free tier | Viable alternative |
| Oracle Cloud | Oracle Kubernetes Engine (OKE) Basic | Potential low-cost alternative, not selected |

## 3.2 Selected provider

**Google Cloud Platform — Google Kubernetes Engine Standard, zonal configuration.**

Reasons:

- Mature managed Kubernetes service.
- Terraform support through the Google provider.
- Native integration with Google Cloud IAM.
- Supports independently managed node pools.
- Supports Kubernetes-native networking and workloads.
- Compatible with future GitOps and observability components.
- Suitable for reproducible CI/CD infrastructure experiments.
- Eligible GKE Standard zonal clusters can benefit from the recurring monthly cluster-management free-tier credit.
- Allows on-demand creation and destruction to minimize spending.

## 3.3 Account and credits

Confirmed:

- The cloud account is personally owned.
- An existing Google student account is available.
- The previous promotional student credits have expired.
- No active GCP billing account was available during planning.
- The owner is willing to activate billing.
- The owner is willing to create a new GCP project.
- No promotional credits are assumed in cost estimates.

The recurring GKE cluster-management free-tier credit is distinct from introductory promotional credits.

The current GKE pricing documentation describes a $74.40 monthly credit against eligible cluster-management fees.

This credit does not cover worker VMs, persistent disks, networking, load balancers, or other separately billed services.

Eligibility and billing treatment must be verified against the active billing account before deployment.

**References:**

- https://cloud.google.com/kubernetes-engine/pricing
- https://cloud.google.com/free
- https://cloud.google.com/compute/all-pricing

---

# 4. Region and Kubernetes Configuration

## 4.1 Region

**Selected region:** `us-central1`  
**Selected zone:** `us-central1-a`

The cluster will be zonal rather than regional.

Rationale:

- Lower-complexity development environment.
- No requirement for multi-zone high availability.
- Suitable for infrastructure acceptance tests.
- Established Google Cloud region with standard GKE support.
- Avoids unnecessary high-availability infrastructure.

## 4.2 Cluster configuration

| Setting | Decision |
|---|---|
| Kubernetes service | GKE Standard |
| Cluster topology | Zonal |
| Region | `us-central1` |
| Zone | `us-central1-a` |
| Environment | `dev` |
| Cluster count | 1 |
| Node pools | 1 explicitly managed node pool |
| Worker nodes | 1 |
| Machine type | `e2-standard-2` |
| vCPU | 2 |
| Memory | 8 GiB |
| Provisioning | On-demand |
| Spot instances | Not used initially |
| Boot disk | 30 GiB |
| Disk type | `pd-standard` |
| GPU | None |
| Managed database | None |
| External application load balancer | None initially |
| Cloud NAT | Not planned initially |
| High availability | Not required |

## 4.3 Node pool management

The GKE cluster should use an independently managed Terraform node pool.

The cluster's default node pool should be removed or explicitly controlled to avoid unintentionally provisioning additional workers.

The desired configuration is one managed worker node, not one default worker plus another independently created worker.

Node type, disk size, and node count should be configurable Terraform variables.

## 4.4 Capacity limitation

The selected `e2-standard-2` node is intended for:

- Infrastructure smoke tests.
- Kubernetes API and connectivity verification.
- Basic deployment testing.
- Terraform apply/destroy acceptance testing.
- Initial lightweight GitOps experiments.

The node has not been proven sufficient to run the entire final project stack simultaneously.

Future components may include:

- Argo CD.
- Argo Rollouts.
- Prometheus.
- Application services.
- Incident agent.
- Failure injection and monitoring workloads.

Resource requests, memory consumption, and sustained CPU requirements must be measured before full platform deployment.

The initial infrastructure issue must not claim that the entire application and agent system has been validated on this node.

---

# 5. Infrastructure Architecture

The infrastructure is divided into two independently managed lifecycles.

## 5.1 Persistent bootstrap infrastructure

Resources that remain available between experiments:

- Terraform remote-state storage bucket.
- Bucket versioning and recovery configuration.
- Terraform state access policies.
- Deployment service account and related IAM configuration.
- Budget and notification configuration.
- Required persistent project-level configuration.

These resources are not deleted when the Kubernetes cluster is destroyed.

## 5.2 Disposable experiment infrastructure

Resources created for development, testing, and demonstrations:

- Dedicated VPC network.
- Subnet and required secondary IP ranges.
- GKE Standard zonal cluster.
- Managed Kubernetes node pool.
- Worker compute resources.
- Associated disposable networking and storage resources.

These resources must be removed through the cluster Terraform destroy workflow.

## 5.3 Network requirements

The initial network should use:

- A dedicated custom-mode VPC.
- A regional subnet in `us-central1`.
- VPC-native GKE networking.
- Secondary IP ranges for Kubernetes Pods and Services.
- Restricted firewall rules.
- No unnecessary public application endpoints.
- No default external load balancer.
- No Cloud NAT unless a demonstrated connectivity requirement makes it necessary.

A public-IP worker node is the initial low-complexity option for outbound connectivity.

Public IP assignment must not imply unrestricted inbound access. Node firewall rules, IAM permissions, and Kubernetes API access should remain appropriately restricted.

Network CIDR ranges must be selected to avoid overlaps and satisfy GKE requirements.

Exact CIDRs, control-plane access restrictions, and node network permissions require final implementation-level validation.

---

# 6. Terraform Architecture

## 6.1 Infrastructure as code

**Selected tool:** HashiCorp Terraform.

Terraform is responsible for reproducible provisioning and destruction of the cloud infrastructure.

All infrastructure code belongs under the repository's existing `infra/` directory.

The configuration should separate persistent bootstrap resources from disposable cluster resources.

A conceptual structure is:

- Persistent bootstrap Terraform root.
- Disposable cluster Terraform root.
- Shared documentation and configuration conventions.
- Separate Terraform states for each root.

The final directory naming remains an implementation detail.

## 6.2 Terraform remote backend

**Selected backend:** Google Cloud Storage (GCS).

Requirements:

- Remote state storage.
- Native Terraform state locking.
- Object versioning.
- Restricted IAM access.
- Separate state prefixes for bootstrap and cluster.
- No committed state files.
- No committed secrets.
- Documented state recovery procedure.

The state bucket must exist before the disposable cluster configuration initializes its backend.

## 6.3 Bootstrap sequence

The intended bootstrap lifecycle is:

1. Manually create the GCP project.
2. Activate and link the billing account.
3. Establish initial administrative access.
4. Enable required cloud APIs.
5. Initialize the bootstrap Terraform configuration locally.
6. Create the GCS state bucket and configure its protections.
7. Configure required service accounts and IAM.
8. Migrate bootstrap state to a separate protected GCS prefix.
9. Initialize the disposable cluster Terraform configuration against its own GCS prefix.
10. Verify backend access and locking.

The bootstrap and cluster configurations must not share the same Terraform state object.

## 6.4 Bootstrap recovery

An owner-controlled recovery path must exist independently of the routine Terraform deployment identity.

This is necessary because incorrect IAM changes could otherwise prevent the team from accessing the backend.

The recovery documentation must explain:

- Which identity retains administrative recovery authority.
- How backend access can be restored.
- How state object versions can be inspected or recovered.
- How to avoid accidental state deletion.
- How to recover from interrupted initialization or migration.

No service-account JSON credentials should be stored in the repository.

## 6.5 Locking

Terraform state locking must remain enabled.

The team must not bypass locking with `-lock=false`.

Two independently authenticated operators must be able to use the same remote backend.

A controlled locking test must demonstrate that a second state-modifying operation cannot proceed while the first holds the state lock.

The test should avoid unnecessary concurrent infrastructure changes.

**References:**

- https://developer.hashicorp.com/terraform/language/backend/gcs
- https://developer.hashicorp.com/terraform/language/state/locking
- https://registry.terraform.io/providers/hashicorp/google/latest/docs

---

# 7. Team Access and IAM

## 7.1 Team structure

The project has four teammates.

**Selected policy:** Four individual identities, two authorized infrastructure operators, and two reviewers.

| Role | Permissions |
|---|---|
| Cloud owner | Billing administration, IAM administration, recovery, infrastructure operations |
| Second infrastructure operator | Authorized Terraform plan/apply/destroy and required cluster operations |
| Infrastructure reviewers (2) | Review Terraform changes, inspect approved outputs, participate in CI validation |
| Automation identity | Restricted non-deploying CI permissions initially |

The second infrastructure operator has not yet been selected.

## 7.2 Authentication

Preferred authentication:

- Individual Google accounts.
- Google Cloud CLI authentication.
- Application Default Credentials where required.
- Dedicated Terraform deployment service account.
- Service-account impersonation for authorized operators.
- No shared personal credentials.
- No long-lived service-account JSON keys.
- No project-wide Owner role for teammates who do not require it.

The GKE worker-node service account must be separate from the Terraform deployment service account.

## 7.3 Operator permissions

The two authorized operators require permissions sufficient to:

- Read relevant project configuration.
- Initialize the Terraform backend.
- Read and update authorized state objects.
- Acquire and release state locks.
- Run Terraform plans.
- Provision and destroy the defined infrastructure.
- Obtain Kubernetes credentials.
- Verify cluster status.

Routine operators should not receive billing-account administration or unrestricted IAM administration unless explicitly required.

## 7.4 Reviewer permissions

The remaining two teammates should be able to:

- Review Terraform pull requests.
- Run formatting and static validation.
- Review appropriately sanitized Terraform plan summaries.
- Review infrastructure documentation.
- Review acceptance-test evidence.

They do not require direct raw-state access or deployment privileges.

Terraform state and plan artifacts may contain sensitive values, so access must be controlled.

## 7.5 GitHub Actions

Initial CI scope:

- Terraform formatting checks.
- Terraform validation.
- Optional static security checks.
- Pull request review support.

Not initially in scope:

- Automatic Terraform apply.
- Automatic Terraform destroy.
- Unapproved cloud deployment.
- Persistent cloud credentials stored in GitHub secrets.

Future cloud automation should use GitHub OIDC and short-lived cloud credentials.

---

# 8. Development Environment

## 8.1 Selected execution environment

**VS Code Development Container.**

The project already uses a Docker-based development environment.

This is preferred over relying on each teammate's native Windows, macOS, or Linux installation because it provides consistent tooling and reproducible commands.

## 8.2 Required tools

The development container should support:

- Git.
- Make.
- Terraform.
- Google Cloud CLI.
- `gke-gcloud-auth-plugin`.
- kubectl.
- Docker.
- kind.
- Helm.
- Argo CD CLI.
- Argo Rollouts CLI.

Terraform and Google Cloud CLI must be added to the existing container configuration.

Tool versions should be explicitly pinned or constrained using documented compatibility requirements.

## 8.3 Credential handling

Credentials must not be baked into the development container image.

Each operator authenticates individually inside the development environment.

The setup must support browser-based or appropriate device-based login without exposing credentials to teammates.

Local authentication files, tokens, and Terraform state files must be excluded from Git.

## 8.4 Existing Windows environment

The primary development machine uses Windows, VS Code, and Codex.

Git for Windows 2.56.0 is installed and accessible through PATH.

Git Credential Manager 2.9.1 is installed.

VS Code is configured as Git's default editor.

GitHub authentication and repository access must be independently verified.

The native Windows Git installation and the Linux development container's Git installation are separate environments.

---

# 9. Cost Requirements

## 9.1 Budget

**Preferred monthly budget:** Less than $20 USD.

No promotional credits are assumed.

The infrastructure should minimize both active cluster charges and persistent charges.

The budget is a preferred spending target, not a provider-enforced hard limit.

## 9.2 Published pricing assumptions

Selected worker:

`e2-standard-2` in `us-central1`.

Previously established planning rate:

Approximately **$0.06701/hour** for worker compute.

Additional illustrative assumptions:

- External IPv4 address: approximately $0.005/hour.
- 30 GiB standard disk: approximately $1.20/month if retained for the entire month.
- Eligible GKE zonal Standard cluster-management fees offset by the recurring GKE free-tier credit.

The disk's actual cost depends on how long the underlying disk exists.

All estimates must be revalidated against current official pricing before being treated as final ADR figures.

## 9.3 Preliminary runtime estimates

Approximate worker compute cost:

| Runtime | Worker compute |
|---|---:|
| 20 hours/month | $1.34 |
| 40 hours/month | $2.68 |
| 80 hours/month | $5.36 |
| 160 hours/month | $10.72 |
| 240 hours/month | $16.08 |
| 730 hours/month | $48.92 |

These figures exclude separately billed networking, storage, logging, and other resources.

A preliminary combined active-resource planning estimate of approximately $0.074/hour was discussed for one worker, disk, and external IP.

This is not a complete or guaranteed GCP billing rate.

## 9.4 Runtime policy

**Selected lifecycle:** On-demand provisioning.

Operating policy:

- Provision only when needed for development, testing, or demonstrations.
- Prefer 20–40 cluster hours per month.
- Use 80 hours/month as the initial maximum planned runtime.
- Keep individual deployment sessions to approximately four hours.
- Assign a responsible operator to every session.
- Destroy disposable resources at the end of each session.
- Do not leave the cluster running overnight without explicit approval.

These are manual operating policies, not automated enforcement.

## 9.5 Cost exclusions and risks

The final cost estimate must account for:

- GKE management fees and credit eligibility.
- Worker compute.
- Boot disks.
- External IPv4 addresses.
- Network egress.
- Load balancers if later introduced.
- Cloud Logging and Monitoring usage.
- GCS backend storage and operations.
- Any resources retained after cluster destruction.
- Taxes and billing adjustments where applicable.

The $20 target must not be represented as guaranteed.

---

# 10. Billing Alerts

## 10.1 Budget configuration

Create a monthly GCP billing budget of **$20 USD**, scoped to the project's spending.

Configured thresholds:

| Threshold | Amount |
|---|---:|
| 25% | $5 |
| 50% | $10 |
| 75% | $15 |
| 100% | $20 |

A forecasted-spend alert should also be evaluated.

## 10.2 Notification recipients

**All four teammates must receive budget notifications.**

Preferred implementation:

- Individual Cloud Monitoring email notification channels.
- Budget connected to the appropriate notification channels.
- Recipients verified before live deployment.
- No unnecessary external notification services.

The team members' email addresses should be supplied through protected configuration or account-level setup, not unnecessarily exposed in the public repository.

## 10.3 Alert testing

The acceptance test must distinguish:

1. Budget resource successfully configured.
2. Notification channel successfully tested.
3. Real budget-threshold notification actually triggered and received.

A test message from Cloud Monitoring verifies notification delivery but does not prove that a budget threshold has been crossed.

Actual budget-threshold notification evidence must be collected separately if required.

No unnecessary spending should be generated solely to trigger a billing threshold.

## 10.4 Budget limitation

Google Cloud budget alerts do not automatically stop billing.

Notifications can be delayed.

The selected teardown policy remains manual.

No automated budget-triggered cluster shutdown is included in the initial scope.

**Reference:** https://cloud.google.com/billing/docs/how-to/budgets

---

# 11. Cluster Lifecycle and Makefile

## 11.1 Lifecycle policy

The cluster is disposable.

The Terraform backend and approved persistent bootstrap infrastructure remain available between experiments.

## 11.2 Makefile requirements

The repository must expose clear commands for:

- Terraform formatting and validation.
- Cluster provisioning.
- Kubernetes readiness verification.
- Cluster destruction.
- Optional non-destructive Terraform planning.

The create and destroy targets must be clearly distinguishable from the repository's local `kind` lifecycle targets.

Existing Makefile functionality must be preserved.

The final Makefile should not silently provision billable resources.

## 11.3 Safety requirements

Before provisioning:

- Confirm the active GCP project.
- Confirm the active account or impersonated identity.
- Confirm the selected Terraform workspace/state.
- Review the Terraform plan.
- Confirm expected spending.
- Confirm a responsible operator.
- Confirm the planned teardown time.

Before destroying:

- Confirm the intended project and cluster.
- Review the destroy plan.
- Ensure no other teammate is running experiments.
- Obtain explicit operator confirmation.

After destruction:

- Verify Terraform completed successfully.
- Inspect remaining resources.
- Confirm the GKE cluster is deleted.
- Confirm worker VMs and associated disks are deleted.
- Confirm no unintended load balancers or reserved IPs remain.
- Confirm disposable networking resources are deleted.
- Record the audit evidence.

Persistent backend and administrative resources must be inventoried separately.

---

# 12. Acceptance-Test Plan

## Test A — Architecture decision

**Requirement:** ADR-002 exists and documents the selected infrastructure.

Evidence:

- Provider and region.
- Credit source and eligibility assumptions.
- Hourly and monthly cost estimate.
- Billing and teardown policy.
- Relevant official documentation references.

## Test B — Budget notification

**Requirement:** Team notification mechanism is operational.

Evidence:

- Configured budget.
- Four intended recipients.
- Test notification delivery.
- Actual threshold-triggered notification, when available.

## Test C — Shared remote state

**Requirement:** Two teammates use the same Terraform backend.

Evidence:

- Two independently authenticated operators.
- Successful Terraform initialization.
- Plans referencing the same backend and state.
- No accidental separate local states.

## Test D — State locking

**Requirement:** Concurrent state-modifying operations cannot proceed.

Evidence:

- Controlled first operation holding the state lock.
- Second operation blocked or rejected.
- Lock information recorded.
- No use of `-lock=false`.
- No unintended infrastructure changes.

## Test E — Provisioning

**Requirement:** Terraform apply creates the cluster from empty cluster state.

Evidence:

- Successful Terraform plan.
- Successful Terraform apply.
- GKE cluster exists in the intended project and zone.
- Expected worker node exists.
- Kubernetes node reports `Ready`.
- Basic Kubernetes smoke test succeeds.

## Test F — Destruction

**Requirement:** Terraform destroy removes disposable infrastructure.

Evidence:

- Successful Terraform destroy.
- Empty disposable Terraform state.
- GKE cluster absent.
- Node VMs and disposable disks absent.
- No unintended billable network resources.
- Console inventory checked.
- Persistent backend remains available.

All evidence should be attached to the relevant Linear subissues or referenced in the project's documentation.

---

# 13. Recommended Linear Subissues

The original Linear issue should be divided into five subissues.

## Subissue 1 — Cloud provider evaluation and ADR-002

**Label:** Research

Scope:

- Document GCP selection.
- Document alternatives considered.
- Confirm region and cluster architecture.
- Record official pricing assumptions.
- Document monthly budget and teardown policy.
- Document limitations and project relevance.

Deliverable:

`docs/adr/002-cloud-provider.md`

## Subissue 2 — GCP account, billing, and IAM

**Label:** Feature

Scope:

- Establish GCP project.
- Activate billing.
- Configure budget thresholds.
- Establish four individual identities.
- Assign two infrastructure operators.
- Configure notification recipients.
- Verify notification delivery.

Deliverables:

- Account configuration documentation.
- IAM permissions matrix.
- Budget configuration.
- Redacted acceptance evidence.

## Subissue 3 — Terraform bootstrap and remote state

**Label:** Feature

Scope:

- Prepare development container tooling.
- Create persistent backend infrastructure.
- Configure GCS versioning.
- Configure state access permissions.
- Migrate bootstrap state.
- Configure separate cluster state.
- Verify two-person backend access.
- Verify locking.
- Document recovery.

Deliverables:

- Bootstrap Terraform configuration.
- Backend configuration.
- Tooling updates.
- Bootstrap documentation.
- State and locking test evidence.

## Subissue 4 — Network and managed Kubernetes cluster

**Label:** Feature

Scope:

- Configure custom VPC.
- Configure subnet and secondary IP ranges.
- Provision GKE Standard zonal cluster.
- Configure independent node pool.
- Set one `e2-standard-2` worker.
- Apply appropriate networking and IAM restrictions.
- Validate Kubernetes readiness.

Deliverables:

- Cluster Terraform configuration.
- Terraform variables and outputs.
- Kubernetes smoke-test evidence.

## Subissue 5 — Makefile lifecycle and teardown validation

**Label:** Improvement

Scope:

- Add cloud-specific Makefile targets.
- Preserve local development targets.
- Document deployment workflow.
- Document teardown procedure.
- Validate resource deletion.
- Collect cost and lifecycle evidence.

Deliverables:

- Updated Makefile.
- Operator runbook.
- Teardown checklist.
- Acceptance-test evidence.

---

# 14. Out-of-Scope Work

The following are not part of the initial cloud infrastructure issue:

- Implementing the incident agent.
- Training or reproducing baseline models.
- Implementing the application.
- Deploying the entire monitoring platform.
- Configuring production-grade multi-zone high availability.
- Deploying managed databases.
- Provisioning GPU compute.
- Building automated self-healing logic.
- Automatically applying Terraform from pull requests.
- Automatically destroying infrastructure based on billing thresholds.
- Implementing the final model comparison framework.
- Guaranteeing the initial worker can host the complete final platform.

These belong to separate project workstreams or later integration stages.

---

# 15. Outstanding Prerequisites

The architecture is established, but the following remain incomplete.

| Item | Status |
|---|---|
| GCP provider selected | Confirmed |
| GKE Standard zonal selected | Confirmed |
| Region and zone | Confirmed |
| Worker configuration | Confirmed |
| On-demand lifecycle | Confirmed |
| Manual teardown policy | Confirmed |
| Persistent backend policy | Confirmed |
| Four-person IAM model | Confirmed |
| Two local Terraform operators | Confirmed in principle |
| Second operator identity | Not selected |
| GCP billing account | Not created |
| GCP project | Not created |
| GCP project ID | Not assigned |
| Four alert recipient addresses | Not collected |
| Terraform version | Not finalized |
| Google Cloud CLI version | Not finalized |
| Development container tooling | Requires changes |
| Exact VPC and subnet CIDRs | Not finalized |
| GKE API and quota verification | Pending |
| Terraform code | Not implemented |
| Remote backend | Not provisioned |
| Billing alerts | Not configured |
| Live apply/destroy tests | Not executed |
| Cost estimate | Preliminary; final verification required |

---

# 16. Implementation Governance

No cloud provisioning or Terraform implementation was authorized during the architecture-discovery discussions.

The implementation handoff to Codex remains deferred until the remaining technical and operational decisions are resolved.

When implementation is authorized, Codex should work within the established architecture and avoid introducing additional cloud services or costs without explicit approval.

Changes should be:

- Minimal and project-relevant.
- Reproducible.
- Reviewed through GitHub pull requests.
- Traceable to Linear issues.
- Secure by default.
- Cost-conscious.
- Compatible with the existing development container.
- Compatible with the existing repository structure.
- Designed for repeatable Terraform creation and destruction.

**Final architectural position:** Use a small, disposable GKE Standard zonal cluster managed by Terraform, backed by persistent GCS remote state with locking, operated by two individually authenticated teammates, with all four teammates receiving billing notifications and a preferred monthly spending target below $20.

**Current phase:** Final implementation-readiness validation. No Codex handoff has been issued.