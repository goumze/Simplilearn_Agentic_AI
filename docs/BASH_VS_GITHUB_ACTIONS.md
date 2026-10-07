# Bash Scripts vs GitHub Actions Workflows

This guide compares the original bash scripts (`bootstrap.sh` and `teardown.sh`) with the automated GitHub Actions workflows.

## 📊 Overview

| Aspect | Bash Script | GitHub Actions |
|--------|-------------|-----------------|
| **Execution** | Local machine or CI/CD server | GitHub cloud infrastructure |
| **Trigger** | Manual command line | GitHub UI / CLI / webhook |
| **Logs** | Terminal output / local files | GitHub Actions UI / artifacts |
| **State Management** | Local Terraform state | Local/S3 Terraform state + artifacts |
| **Authentication** | AWS credentials on machine | AWS OIDC (no stored keys) |
| **Environment Vars** | Shell env vars or .env file | GitHub Secrets + Workflow inputs |
| **Error Handling** | Bash error handling (`set -e`) | GitHub job conditions + continue-on-error |
| **Parallelization** | Sequential (bash) | Parallel + sequential (GitHub jobs) |
| **Artifacts** | Must save manually | Auto-saved with retention policy |

---

## 🔄 Deployment Comparison

### Original: bootstrap.sh

```bash
# Run locally:
./scripts/bootstrap.sh

# Or with custom vars:
AWS_REGION=us-west-2 CLUSTER_NAME=my-cluster ./scripts/bootstrap.sh
```

**Execution Flow:**
```
User runs bootstrap.sh
    ↓
Set variables (REGION, CLUSTER)
    ↓
terraform apply cluster/      (~15 min)
    ↓
aws eks update-kubeconfig
    ↓
terraform apply bootstrap/    (~3 min)
    ↓
Wait for ArgoCD controller
    ↓
Wait for Applications (loop with timeout)
    ↓
Wait for ACK capabilities (loop)
    ↓
Wait for RGDs (loop)
    ↓
Wait for financial-services resources (loop)
    ↓
Wait for AgentCore IDs (nested loop)
    ↓
kubectl rollout restart agents
    ↓
Print credentials and next steps
```

**Key Features:**
- ✅ Runs from local machine
- ✅ Direct access to kubeconfig
- ✅ Real-time output to terminal
- ❌ Requires AWS credentials locally
- ❌ Must handle errors manually
- ❌ Logs not persisted
- ❌ No audit trail

---

### New: deploy-eks.yml (GitHub Actions)

```yaml
# Trigger:
# 1. GitHub UI → Actions → Deploy Multi-Agent Platform → Run workflow
# 2. GitHub CLI:
gh workflow run deploy-eks.yml \
  -f aws_region=us-west-2 \
  -f cluster_name=finops-agents \
  -f environment=dev
```

**Execution Flow:**
```
GitHub Actions starts workflow
    ↓
Job 1: Validate
    - Check terraform directories exist
    ↓
Job 2: Provision Cluster
    - AWS credentials via OIDC
    - terraform init + plan + apply
    ↓
Job 3: Update kubeconfig
    - aws eks update-kubeconfig
    - kubectl get nodes
    ↓
Job 4: Install ArgoCD
    - terraform apply bootstrap/
    - kubectl wait argocd-application-controller
    ↓
Job 5: Wait for Capabilities
    - aws eks describe-capability loop
    - kubectl wait resourcegraphdefinition loop
    ↓
Job 6: Wait for Add-ons
    - kubectl wait application loop
    ↓
Job 7: Wait for Financial Services
    - kubectl wait application/financial-services
    - kubectl wait ACK resources
    - kubectl wait PodIdentityAssociations
    - Verify AgentCore IDs populated
    ↓
Job 8: Restart Agents
    - kubectl rollout restart per agent
    ↓
Job 9: Post-Deployment
    - Generate deployment report
    - Upload artifacts
    - Summary to workflow
    ↓
Workflow complete (success or failure)
```

**Key Features:**
- ✅ No AWS credentials on local machine
- ✅ Runs in GitHub cloud
- ✅ All logs saved to GitHub
- ✅ Artifacts auto-retained
- ✅ Audit trail of all runs
- ✅ Easy to repeat/re-run
- ✅ Environment isolation (dev/staging/prod)
- ✅ Automatic cleanup on failure (dev)
- ❌ Slower feedback (GitHub cloud latency)
- ❌ Can't modify during execution

---

## 💀 Teardown Comparison

### Original: teardown.sh

```bash
# Run locally:
./scripts/teardown.sh

# Or with custom vars:
AWS_REGION=us-west-2 CLUSTER_NAME=my-cluster ./scripts/teardown.sh
```

**Execution Strategy:**
```
User runs teardown.sh
    ↓
Check cluster is reachable (kubectl get ns argocd)
    ↓
[IF REACHABLE] Pause ArgoCD auto-sync on all Applications
    ↓
[IF REACHABLE] Delete Applications in reverse wave order
    - For each app: kubectl delete application
    - With timeout + fallback to strip finalizers
    - Per-app timeouts: 600s → 60s
    ↓
terraform destroy bootstrap/   (~5 min)
    ↓
terraform destroy cluster/     (~15 min)
    ↓
Spot-check AWS for orphans
    - aws bedrock-agentcore-control list-*
    - aws iam list-roles
    - aws eks list-pod-identity-associations
    ↓
Print teardown summary
```

**Key Features:**
- ✅ Cluster-aware (checks if reachable before deleting)
- ✅ Graceful Application deletion (cascade-delete via finalizers)
- ✅ Fallback mechanism (strip finalizers if timeout)
- ✅ Orphan detection (AWS spot-check)
- ❌ Manual confirmation required
- ❌ Logs not persisted
- ❌ Error recovery manual

---

### New: teardown-eks.yml (GitHub Actions)

```yaml
# Trigger:
# 1. GitHub UI → Actions → Teardown → Run workflow
# 2. GitHub CLI:
gh workflow run teardown-eks.yml \
  -f aws_region=us-west-2 \
  -f cluster_name=finops-agents \
  -f environment=dev \
  -f confirm_deletion=yes-delete-all
```

**Execution Strategy:**
```
GitHub Actions starts workflow
    ↓
Job 1: Validate
    - Check confirm_deletion == "yes-delete-all"
    - Print warning message
    ↓
Job 2: Pause ArgoCD
    - Check cluster reachable
    - [IF REACHABLE] Pause auto-sync
    - [IF NOT] Log warning and continue
    ↓
Job 3: Delete Applications
    - [IF REACHABLE] delete_app helper function
    - Per-app timeouts with finalizer fallback
    - Reverse wave order (600s → 60s)
    ↓
Job 4: Terraform Destroy Bootstrap
    - terraform init + destroy
    - Upload state artifacts
    ↓
Job 5: Terraform Destroy Cluster
    - terraform init + destroy  (~15 min)
    - Upload state artifacts
    ↓
Job 6: Spot-Check
    - aws bedrock-agentcore-control list-*
    - aws iam list-roles
    - aws eks list-pod-identity-associations
    ↓
Job 7: Post-Teardown
    - Generate teardown report
    - Upload artifacts
    ↓
Workflow complete
```

**Key Features:**
- ✅ Explicit confirmation required ("yes-delete-all")
- ✅ Graceful Application deletion (same strategy as bash)
- ✅ Automatic orphan detection
- ✅ All logs persisted in GitHub
- ✅ Environment isolation (auto-cleanup dev only)
- ✅ Terraform state artifacts saved
- ✅ Audit trail of all teardowns
- ✅ Continue-on-error for fault tolerance
- ❌ Requires GitHub access to approve/run

---

## 🔀 Migration Guide: Bash to GitHub Actions

### Scenario 1: Already running with bash scripts

**Before:**
```bash
# Manual deployments
./scripts/bootstrap.sh

# Manual teardowns
./scripts/teardown.sh
```

**After:**
```bash
# GitHub Actions deployments
gh workflow run deploy-eks.yml -f environment=dev

# GitHub Actions teardowns
gh workflow run teardown-eks.yml \
  -f environment=dev \
  -f confirm_deletion=yes-delete-all
```

**Benefits:**
- ✅ No AWS credentials on local machine
- ✅ All deployments logged and auditable
- ✅ Easier to repeat/troubleshoot
- ✅ Team visibility of deployments
- ✅ Automated artifact collection

### Scenario 2: Running from CI/CD (Jenkins, GitLab CI, etc.)

**Before:**
```bash
# Jenkins Pipeline:
stage('Deploy') {
  steps {
    sh './scripts/bootstrap.sh'
  }
}
```

**After:**
```bash
# GitHub Actions (native):
- name: Trigger Deploy
  run: |
    gh workflow run deploy-eks.yml \
      -f aws_region=$AWS_REGION \
      -f environment=$ENVIRONMENT
```

**Benefits:**
- ✅ Native GitHub integration
- ✅ No external CI/CD needed (if using GitHub Actions for all)
- ✅ Unified logging and artifact storage
- ✅ GitHub OIDC for AWS (no key rotation)

### Scenario 3: Local development (bash scripts preserved)

**Option A: Keep both**
```bash
# Still have bash scripts for local work
./scripts/bootstrap.sh  # Local development

# But use GitHub Actions for cloud deployments
# (see GitHub UI / gh CLI)
```

**Option B: Use GitHub Actions everywhere**
```bash
# Use gh CLI even locally
gh workflow run deploy-eks.yml -f environment=dev

# Monitor locally
gh run watch
```

---

## 📋 Feature Comparison Matrix

| Feature | bootstrap.sh | deploy-eks.yml | teardown.sh | teardown-eks.yml |
|---------|--------------|----------------|-------------|-----------------|
| **Local execution** | ✅ | ❌ | ✅ | ❌ |
| **Cloud execution** | ❌ | ✅ | ❌ | ✅ |
| **AWS credentials needed** | ✅ | ❌ (OIDC) | ✅ | ❌ (OIDC) |
| **Parameterized** | ✅ (env vars) | ✅ (UI inputs) | ✅ (env vars) | ✅ (UI inputs) |
| **Logs persisted** | ❌ | ✅ | ❌ | ✅ |
| **Artifacts saved** | ❌ | ✅ | ❌ | ✅ |
| **Audit trail** | ❌ | ✅ | ❌ | ✅ |
| **Timeout handling** | ✅ (bash) | ✅ (per-job) | ✅ (per-app) | ✅ (per-app) |
| **Failure recovery** | Manual | Auto (dev) | Manual | Auto (dev) |
| **Confirmation required** | No | No | Manual | ✅ (phrase) |
| **Orphan detection** | ✅ | N/A | ✅ | ✅ |
| **Team visibility** | Low | High | Low | High |
| **Scheduling** | Manual | Manual/scheduled | Manual | Manual/scheduled |

---

## 🔗 When to Use Each

### Use bootstrap.sh when:
- Developing locally
- Testing Terraform modules
- Rapid iteration needed
- No GitHub Actions access
- Want direct terminal access
- AWS credentials available locally

### Use deploy-eks.yml when:
- Need audit trail
- Multiple team members deploying
- Want artifact collection
- No local AWS credentials
- Prefer GitHub native tools
- Want environment isolation
- Need scheduled deployments

### Use teardown.sh when:
- Developing locally
- Quick cleanup in dev
- Testing Terraform modules
- Testing teardown strategy
- AWS credentials available locally

### Use teardown-eks.yml when:
- Need destructive action audit log
- Team coordination required
- Want explicit confirmation
- Prefer GitHub native tools
- Need artifact collection
- Want environment isolation

---

## 🔧 Technical Implementation

### Parity Between Implementations

The GitHub Actions workflows were designed to maintain functional parity with the bash scripts:

**Same sequence:**
```
✅ bootstrap.sh → deploy-eks.yml (same 9 logical steps)
✅ teardown.sh → teardown-eks.yml (same 5 logical phases)
```

**Same timeouts and waits:**
```
✅ RGD wait: 5 min (both)
✅ App wait: 10-15 min (both)
✅ Capability wait: 60×10s = 10 min max (both)
✅ ACK resource wait: 10 min (both)
```

**Same error handling:**
```
✅ Finalizer stripping fallback (both)
✅ Continue-on-error for spot-check (both)
✅ Timeout escalation (both)
```

---

## 🎯 Recommended Architecture

### For Small Teams / Learning
```
Local Development:
  └─ bootstrap.sh / teardown.sh (for learning and testing)

Cloud Deployments:
  └─ GitHub Actions workflows (for consistency)
```

### For Production Teams
```
Dev Environment:
  └─ GitHub Actions (automated deployment on merge)

Staging Environment:
  └─ GitHub Actions (manual approval required)

Prod Environment:
  └─ GitHub Actions (approval + confirmation phrase required)
```

---

## 📚 Documentation Hierarchy

```
GITHUB_ACTIONS_INDEX.md (this directory)
├── GITHUB_ACTIONS_QUICK_REF.md (quick start)
├── GITHUB_ACTIONS_SETUP.md (deployment details)
└── GITHUB_ACTIONS_TEARDOWN.md (destruction details)

Workflow Files:
├── .github/workflows/deploy-eks.yml
└── .github/workflows/teardown-eks.yml

Original Bash Scripts:
├── scripts/bootstrap.sh (⚠️ not modified)
└── scripts/teardown.sh (⚠️ not modified)
```

---

## 🔄 Switching Between Approaches

### From bash to GitHub Actions
1. Verify GitHub Actions workflows work
2. Keep bash scripts for local reference
3. Migrate team deployments to GitHub Actions
4. Bash scripts remain for testing/learning

### From GitHub Actions back to bash
1. Recreate local AWS credentials
2. Update env vars for bash
3. Run bash scripts as before
4. Check artifacts from GitHub for reference

---

## ✅ Validation Checklist

When migrating from bash to GitHub Actions:

**Pre-Migration:**
- [ ] Both approaches produce same results
- [ ] GitHub Actions passes all tests
- [ ] Team trained on GitHub Actions workflow
- [ ] Rollback plan documented
- [ ] Bash scripts backed up

**Post-Migration:**
- [ ] All deployments go through GitHub Actions
- [ ] Audit logs reviewed
- [ ] Artifacts collected
- [ ] Bash scripts kept for reference
- [ ] Documentation updated

---

**Last Updated:** 2024

For workflow details, see:
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- [GITHUB_ACTIONS_TEARDOWN.md](GITHUB_ACTIONS_TEARDOWN.md)
- [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md)
