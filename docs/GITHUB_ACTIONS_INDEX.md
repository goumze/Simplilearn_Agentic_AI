# GitHub Actions CI/CD Documentation Index

Complete guide to automating EKS deployment and teardown for the multi-agent platform.

## 📚 Documentation Structure

### 1. **Quick Start** (Start here!)
📄 [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md)

**Best for:**
- One-time setup commands
- Running workflows quickly
- Common issue solutions
- Quick reference lookups

**Contains:**
- AWS OIDC setup (copy-paste commands)
- Running workflows via UI or CLI
- Monitoring deployment progress
- Testing and cleanup
- Troubleshooting tips

---

### 2. **Deploy Guide** (Detailed instructions)
📄 [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)

**Best for:**
- First-time setup
- Understanding workflow concepts
- Configuring environments
- Advanced customization
- Security best practices

**Contains:**
- Complete AWS prerequisites
- GitHub repository setup (OIDC vs access keys)
- Terraform backend configuration
- Workflow parameters and jobs
- Post-deployment access
- Detailed troubleshooting

---

### 3. **Teardown Guide** (Destruction strategy)
📄 [GITHUB_ACTIONS_TEARDOWN.md](GITHUB_ACTIONS_TEARDOWN.md)

**Best for:**
- Understanding teardown strategy
- Safely destroying resources
- Recovering from failures
- Cleanup verification
- Cost management

**Contains:**
- Ordered teardown phases
- Running teardown workflows
- Monitoring progress
- Recovery procedures
- Orphan resource detection
- Safety checklist

---

## 🔧 Workflow Files

### Deploy Workflow
📄 [.github/workflows/deploy-eks.yml](.github/workflows/deploy-eks.yml)

**Purpose:** Provision EKS cluster and deploy multi-agent platform

**Triggers:** Manual (workflow_dispatch)

**Parameters:**
- `aws_region` - AWS region (default: us-west-2)
- `cluster_name` - Cluster name (default: finops-agents)
- `gitops_repo_url` - Optional GitOps repo
- `environment` - Environment tier (dev/staging/prod)

**Jobs (9 sequential):**
1. Validate configuration
2. Provision EKS cluster
3. Update kubeconfig
4. Install ArgoCD
5. Wait for EKS Capabilities
6. Wait for add-on Applications
7. Wait for Financial Services
8. Restart agent Deployments
9. Generate deployment report

**Duration:** ~45-60 minutes

**Artifacts:** kubeconfig, Terraform state, deployment report

---

### Teardown Workflow
📄 [.github/workflows/teardown-eks.yml](.github/workflows/teardown-eks.yml)

**Purpose:** Safely destroy EKS cluster and all resources

**Triggers:** Manual (workflow_dispatch)

**Parameters:**
- `aws_region` - AWS region
- `cluster_name` - Cluster name
- `environment` - Environment tier (dev/staging/prod)
- `confirm_deletion` - Confirmation phrase (must be "yes-delete-all")

**Jobs (6 sequential):**
1. Validate deletion confirmation
2. Pause ArgoCD auto-sync
3. Delete Applications (reverse wave order)
4. Terraform destroy bootstrap
5. Terraform destroy cluster
6. Spot-check for orphans

**Duration:** ~30-50 minutes

**Artifacts:** Terraform state, teardown report

---

## 🚀 Quick Navigation

### I want to...

#### **Deploy the platform**
1. Read: [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md) (One-Time Setup)
2. Go to: Actions tab → Deploy Multi-Agent Platform to EKS
3. Reference: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) if issues

#### **Test the deployed platform**
1. Go to: [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md#-test-deployment)
2. Follow: "Test Deployment" section
3. Reference: Main [README.md](../README.md) for testing options

#### **Monitor deployment progress**
1. GitHub UI: Actions tab → your workflow run
2. CLI: `gh run watch`
3. Reference: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md#-accessing-your-deployment)

#### **Tear down the cluster**
1. Read: [GITHUB_ACTIONS_TEARDOWN.md](GITHUB_ACTIONS_TEARDOWN.md) (complete)
2. Go to: Actions tab → Teardown Multi-Agent Platform from EKS
3. Quick ref: [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md#-cleanup--teardown)

#### **Troubleshoot deployment issues**
1. Check workflow logs in GitHub Actions
2. Reference: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md#-troubleshooting)
3. Reference: [GITHUB_ACTIONS_TEARDOWN.md](GITHUB_ACTIONS_TEARDOWN.md#-recovering-from-issues) for cleanup issues

#### **Configure AWS OIDC**
1. Start: [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md#-one-time-setup)
2. Details: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md#-aws-account--permissions)

#### **Customize workflows**
1. Reference: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md#-workflow-customization)
2. Edit: `.github/workflows/deploy-eks.yml` or `.github/workflows/teardown-eks.yml`

---

## ⏱️ Timing Overview

### Deployment Timeline
```
Provision Cluster    ████████████████ ~15 min
Update kubeconfig    ██ ~1 min
Install ArgoCD       ███ ~3 min
Wait Capabilities    ████████ ~5-10 min
Wait Add-ons         ████████ ~5-10 min
Wait Services        ████████ ~5-10 min
Restart Agents       ██ ~2 min
─────────────────────────────────────
Total               ~45-60 minutes
```

### Teardown Timeline
```
Pause ArgoCD         ██ ~1-2 min
Delete Apps          ████████████ ~10-20 min
Destroy Bootstrap    ███ ~3-5 min
Destroy Cluster      ███████████ ~10-15 min
Spot-check           ██ ~2-3 min
─────────────────────────────────────
Total               ~30-50 minutes
```

---

## 🔑 Environment Setup Checklist

### One-Time Prerequisites
- [ ] AWS account with EKS permissions
- [ ] AWS OIDC provider created
- [ ] GitHub Actions IAM role created
- [ ] `AWS_ROLE_TO_ASSUME` secret added to repo
- [ ] Repository has `terraform/` directory with cluster and bootstrap modules

### Before Each Deployment
- [ ] AWS region is correct
- [ ] Cluster name is unique
- [ ] Environment variable is correct (dev/staging/prod)
- [ ] No existing cluster with same name
- [ ] AWS quota is sufficient

### Before Each Teardown
- [ ] Cluster name is correct
- [ ] AWS region is correct
- [ ] No important data needs recovery
- [ ] Confirmation phrase is correct: "yes-delete-all"

---

## 📊 Workflow Status Meanings

### Deployment Workflow
- 🟢 **Green** - Resource successfully created
- 🔵 **Running** - Step in progress
- 🟡 **Waiting** - Waiting for previous job or AWS resource
- 🔴 **Failed** - Step failed (check logs)

### Teardown Workflow
- 🟢 **Green** - Resource successfully deleted
- 🟡 **Warning** - Finalizer stripped; may have orphans
- 🔴 **Failed** - Step failed (check logs)

---

## 🔒 Security Considerations

### Best Practices
1. ✅ Use AWS OIDC (not access keys)
2. ✅ Use environment-specific roles
3. ✅ Limit IAM permissions to necessary services
4. ✅ Require confirmation for destructive operations
5. ✅ Enable audit logging
6. ✅ Rotate credentials regularly
7. ✅ Review workflow logs for sensitive data leaks

### Secret Management
- **Never** commit AWS credentials
- **Always** use GitHub Secrets for sensitive data
- **Rotate** secrets regularly
- **Audit** who has access to secrets

---

## 💾 Artifact Management

### Saved Artifacts
After each workflow run, these artifacts are saved:

**Deployment:**
- `kubeconfig` - Kubernetes config file
- `terraform-cluster-state` - Terraform state
- `deployment-report` - Summary of deployment

**Teardown:**
- `terraform-cluster-destroy-state` - Terraform state after destroy
- `terraform-bootstrap-destroy-state` - Bootstrap state after destroy
- `teardown-report` - Teardown summary

### Accessing Artifacts
1. Go to workflow run in GitHub Actions
2. Scroll to "Artifacts" section
3. Download the desired artifact
4. Artifacts are retained for 30 days

---

## 🆘 Support & Troubleshooting

### Troubleshooting Resources

| Issue | Resolution |
|-------|-----------|
| "Permission denied" | Check IAM role permissions (see Setup Guide) |
| "Terraform state lock" | Wait 5 mins or remove lock manually |
| "Kubectl not found" | Workflow installs automatically; check logs |
| "Agents not starting" | Check pod logs and Application status |
| "ArgoCD not syncing" | Check network policies; describe Application |
| "Cascade-prune timeout" | Expected; check spot-check for orphans |
| "Cluster not reachable" | EKS may be deleting; check AWS console |

See detailed troubleshooting in:
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md#-troubleshooting)
- [GITHUB_ACTIONS_TEARDOWN.md](GITHUB_ACTIONS_TEARDOWN.md#-recovering-from-issues)

---

## 📝 Common Tasks

### Task: Monitor a running deployment
```bash
# Watch with GitHub CLI
gh run watch

# Or check Actions tab manually
# View specific job: click job name → see log output
```

### Task: Access ArgoCD UI after deployment
```bash
# Port-forward to ArgoCD
kubectl port-forward -n argocd svc/argocd-server 8080:80

# Open: http://localhost:8080
# Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

### Task: Test deployed agents
```bash
# See full test commands in GITHUB_ACTIONS_QUICK_REF.md
# Or refer to QUICKSTART.md for comprehensive testing
```

### Task: Handle failed deployment
1. Check workflow logs (Actions tab)
2. Identify failing step
3. Reference troubleshooting section
4. Either fix and re-run, or run cleanup

### Task: Handle failed teardown
1. Check workflow logs
2. Look for "didn't finish" warnings (finalizer stripped)
3. Run spot-check commands manually
4. Clean up orphans if found

---

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - Local development guide
- [AWS Bedrock Agents Blog](https://aws.amazon.com/blogs/) - Original architecture
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)

---

## 📞 Getting Help

1. **Workflow failed?** Check the workflow logs in GitHub Actions
2. **AWS error?** Review AWS CloudTrail logs
3. **Terraform error?** Check Terraform debug output
4. **Documentation unclear?** Read the related guide file
5. **Still stuck?** Review both setup and teardown guides thoroughly

---

## 🎓 Learning Path

### Beginner
1. Read [GITHUB_ACTIONS_QUICK_REF.md](GITHUB_ACTIONS_QUICK_REF.md)
2. Follow one-time setup
3. Run a deployment in dev environment
4. Test the platform

### Intermediate
1. Read [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
2. Understand Terraform backend options
3. Configure environment-specific roles
4. Customize workflow parameters

### Advanced
1. Read workflow YAML files directly
2. Understand job dependencies
3. Customize Terraform modules
4. Integrate with custom CI/CD pipelines

---

**Last Updated:** 2024

For the latest information, see the individual guide files.
