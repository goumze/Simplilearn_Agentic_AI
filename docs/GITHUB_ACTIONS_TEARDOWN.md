# GitHub Actions Teardown Guide

This guide explains how to use the GitHub Actions workflow (`teardown-eks.yml`) to safely tear down the EKS cluster and multi-agent platform deployment.

## ⚠️ Important Notes

**Teardown is destructive and irreversible.**

- All cluster resources will be deleted
- All data in the cluster will be lost
- All AWS resources will be deleted and charged
- This action **cannot be undone**

Proceed only when you're certain you want to delete the cluster.

## 🔄 Teardown Strategy

The teardown workflow uses a sophisticated ordered approach:

### Phase 1: Pause ArgoCD Auto-Sync
Prevents ArgoCD from recreating resources while deletion is in progress.

### Phase 2: Delete ArgoCD Applications (Reverse Wave Order)
Deletes Applications in reverse sync-wave order, allowing Kubernetes cascade-delete to clean up resources:

1. **financial-services** (600s timeout)
   - Agents
   - AgentCore Memory/Browser/CodeInterpreter claims
   - ACK Memory/Browser/CodeInterpreter resources
   - IAM roles and Pod Identity associations

2. **litellm** (180s) - LLM proxy and database

3. **agent-gateway-config** (120s) - Gateway configuration

4. **agent-gateway** (180s) - Agent Gateway controller

5. **agentcore-rgds** (180s) - kro ResourceGraphDefinitions

6. **auto-mode-defaults** (120s) - StorageClass, IngressClass

7. **agentgateway-crds** (120s) - CRDs

8. **gateway-api-crds** (120s) - Gateway API CRDs

9. **platform-root** (60s) - Root app-of-apps

**Finalizer Fallback**: If cascade-prune takes too long, the workflow strips the finalizer to force deletion through, flagging any orphaned resources for manual cleanup.

### Phase 3: Terraform Destroy Bootstrap
Removes ArgoCD and the platform-root Application using Terraform.

### Phase 4: Terraform Destroy Cluster
Removes the entire EKS cluster, VPC, and all AWS infrastructure (~15 minutes).

### Phase 5: Spot-Check for Orphans
Scans AWS for any remaining:
- Bedrock AgentCore resources (Memory, Browser, CodeInterpreter)
- IAM roles (starting with `fs-`)
- Pod Identity Associations

## 📋 Prerequisites

- AWS OIDC provider configured (see [Deploy Guide](GITHUB_ACTIONS_SETUP.md))
- GitHub Actions IAM role with permissions to delete resources
- `AWS_ROLE_TO_ASSUME` secret configured in repository

## 🚀 Running the Teardown

### Option 1: GitHub UI (Recommended)

1. Go to **Actions** tab
2. Select **Teardown Multi-Agent Platform from EKS**
3. Click **Run workflow**
4. Fill in parameters:
   - **AWS Region**: Region of cluster to destroy (e.g., `us-west-2`)
   - **Cluster Name**: Name of cluster to destroy (e.g., `finops-agents`)
   - **Environment**: `dev`, `staging`, or `prod`
   - **Confirm Deletion**: Type `yes-delete-all` to confirm
5. Click **Run workflow**

### Option 2: GitHub CLI

```bash
gh workflow run teardown-eks.yml \
  -f aws_region=us-west-2 \
  -f cluster_name=finops-agents \
  -f environment=dev \
  -f confirm_deletion=yes-delete-all
```

### Option 3: Manual Teardown (Not Recommended)

If GitHub Actions is not available:

```bash
cd scripts
AWS_REGION=us-west-2 CLUSTER_NAME=finops-agents ./teardown.sh
```

## 🔍 Monitoring Teardown

### Watch Workflow Progress

```bash
# With GitHub CLI
gh run watch
```

### View Specific Job Logs

```bash
# List recent runs
gh run list --workflow teardown-eks.yml --limit 5

# View specific job
gh run view <run-id> --log --job <job-name>
```

## ⏱️ Expected Timing

| Phase | Duration | Notes |
|-------|----------|-------|
| Pause ArgoCD | 1-2 min | Quick operation |
| Delete Applications | 10-20 min | Longest phase; ACK resource deletion can take time |
| Destroy Bootstrap | 3-5 min | Terraform state cleanup |
| Destroy Cluster | 10-15 min | AWS resource deletion |
| Spot-Check | 2-3 min | Check for orphans |
| **Total** | **30-50 min** | Depends on resource complexity |

## 📊 Understanding the Logs

### Success Indicators

✅ All Applications deleted successfully
✅ Bootstrap resources destroyed
✅ Cluster destroyed
✅ Spot-check found no orphans

### Warning Indicators

⚠️ "cascade-prune ... didn't finish" → Finalizer was stripped; check spot-check for orphans
⚠️ Cluster not reachable → In-cluster cleanup skipped; check AWS manually
⚠️ Terraform warnings → Usually non-critical; review logs

### Error Indicators

❌ "Deletion not confirmed" → Did not type exact confirmation phrase
❌ "Permission denied" → IAM role lacks delete permissions
❌ Terraform errors → Resource dependency issues; may need manual intervention

## 🏥 Recovering from Issues

### Workflow Fails - Partial Teardown

**Risk**: Resources were partially deleted

**Recovery**:
1. Check the workflow logs to see what failed
2. Run spot-check commands manually:
   ```bash
   aws eks describe-cluster --name finops-agents --region us-west-2
   aws bedrock-agentcore-control list-memories --region us-west-2
   ```
3. Clean up remaining resources manually or re-run teardown workflow

### Orphan AWS Resources Remain

**If spot-check finds orphans:**

```bash
# List orphan resources
aws bedrock-agentcore-control list-memories --region us-west-2
aws bedrock-agentcore-control list-browsers --region us-west-2
aws iam list-roles --query 'Roles[?starts_with(RoleName, `fs-`)].RoleName'

# Delete them manually (if safe)
aws bedrock-agentcore-control delete-memory --id <memory-id> --region us-west-2
```

### Stuck Terraform Destroy

**If terraform destroy hangs:**

1. Cancel the workflow run (click the 3-dot menu → Cancel workflow run)
2. Check Terraform state:
   ```bash
   cd terraform/cluster
   terraform state list
   terraform state show
   ```
3. Remove problematic resources:
   ```bash
   terraform state rm 'aws_eks_cluster.cluster'  # Use with caution!
   terraform destroy -auto-approve
   ```

## 🔐 Security Considerations

1. **Minimum Permissions**: IAM role should have only necessary delete permissions
2. **Confirmation Required**: Must type exact phrase `yes-delete-all`
3. **Environment Isolation**: Dev environment auto-cleans; prod requires extra care
4. **Audit Logging**: All AWS API calls are logged
5. **State Backup**: Terraform state is uploaded as artifacts

## 📝 Teardown Checklist

Before running teardown:

- [ ] Verified you have the correct cluster name
- [ ] Verified you have the correct AWS region
- [ ] Backed up any data from the cluster (if needed)
- [ ] Notified team members about the teardown
- [ ] Confirmed you want to delete everything
- [ ] Have AWS credentials/access if manual cleanup is needed

## 🔗 Related Documentation

- [Deploy Guide](GITHUB_ACTIONS_SETUP.md)
- [Quick Reference](GITHUB_ACTIONS_QUICK_REF.md)
- [README](../README.md)

## 💡 Tips

1. **Start with dev** - Test teardown on dev cluster first
2. **Monitor AWS costs** - Verify all resources are actually deleted
3. **Keep artifacts** - Save deployment/teardown reports
4. **Document issues** - If cleanup fails, document steps for manual recovery
5. **Test redeploy** - Verify you can redeploy to same region after teardown

## ⏱️ Cost Considerations

Stopping the workflow after partial deletion means:
- EKS cluster still exists (charges continue)
- VPC resources still exist (data transfer charges)
- Terraform state may be out of sync

**Recommendation**: Let the workflow complete fully, or manually complete cleanup.

---

For quick reference, see [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md#teardown)
