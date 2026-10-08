# GitHub Actions Workflow Quick Reference

## 📌 One-Time Setup

### 1. Create AWS OIDC Provider
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --region us-west-2
```

### 2. Create GitHub Actions IAM Role
```bash
# Replace YOUR_ACCOUNT_ID and YOUR_GITHUB_ORG/YOUR_REPO
ROLE_ARN=$(aws iam create-role \
  --role-name github-actions-eks-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO:*"
        }
      }
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

echo "Role ARN: $ROLE_ARN"
```

### 3. Attach Permissions
```bash
aws iam put-role-policy \
  --role-name github-actions-eks-role \
  --policy-name eks-deployment \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "eks:*",
        "ec2:*",
        "iam:*",
        "logs:*",
        "s3:*"
      ],
      "Resource": "*"
    }]
  }' \
  --region us-west-2
```

### 4. Add GitHub Secret
In your GitHub repository:
- Go to **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Name: `AWS_ROLE_TO_ASSUME`
- Value: `arn:aws:iam::YOUR_ACCOUNT_ID:role/github-actions-eks-role`

## 🚀 Running the Workflow

### Option 1: GitHub UI
1. Go to **Actions** tab
2. Select **Deploy Multi-Agent Platform to EKS**
3. Click **Run workflow**
4. Enter parameters and click **Run workflow**

### Option 2: GitHub CLI
```bash
gh workflow run deploy-eks.yml \
  -f aws_region=us-west-2 \
  -f cluster_name=finops-agents \
  -f environment=dev
```

## 📊 Workflow Status

### Check Deployment Progress
```bash
# Watch workflow (requires GitHub CLI)
gh run watch

# List recent runs
gh run list --workflow deploy-eks.yml --limit 5
```

### View Logs
```bash
# List jobs
gh run view <run-id>

# View specific job logs
gh run view <run-id> --log --job <job-id>
```

## 🔍 Monitor Resources

### After Deployment Success
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name finops-agents

# Check cluster
kubectl cluster-info
kubectl get nodes

# Check agents
kubectl get pods -n financial-services

# Check ArgoCD
kubectl get applications -n argocd

# ArgoCD UI
kubectl port-forward -n argocd svc/argocd-server 8080:80
```

## 🧪 Test Deployment

```bash
# 1. Port-forward to agent gateway
kubectl port-forward -n agentgateway-system svc/agent-gateway-proxy 8080:8080 &

# 2. Get auth token
TOKEN=$(kubectl create token financial-advisor-sa \
  -n financial-services \
  --duration=1h \
  --audience=agent-gateway)

# 3. Test advisor
curl -X POST http://localhost:8080/agents/financial-advisor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"I have 100 AAPL and 50 GOOGL. Is my portfolio balanced?"}' \
  | jq .result
```

## 🛑 Cleanup / Teardown

### Option 1: GitHub Actions (Recommended)

```bash
# Via GitHub UI:
1. Go to Actions → "Teardown Multi-Agent Platform from EKS"
2. Click "Run workflow"
3. Enter cluster name, region, environment
4. In "Confirm Deletion" field type: yes-delete-all
5. Click "Run workflow"

# Via GitHub CLI:
gh workflow run teardown-eks.yml \
  -f aws_region=us-west-2 \
  -f cluster_name=finops-agents \
  -f environment=dev \
  -f confirm_deletion=yes-delete-all
```

### Option 2: Manual Teardown

```bash
# Destroy in reverse order
cd terraform/bootstrap && terraform destroy -auto-approve
cd ../cluster && terraform destroy -auto-approve
```

**⚠️ WARNING**: Teardown is destructive and irreversible. See [Teardown Guide](GITHUB_ACTIONS_TEARDOWN.md) for details.

## 🔑 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Permission denied" | Check IAM role permissions |
| "Terraform state lock" | Wait 5 mins or delete lock in S3 |
| "Kubectl not found" | Workflow installs it automatically |
| "Agents not starting" | Check `kubectl logs -n financial-services` |
| "ArgoCD not syncing" | Check network policies, try `kubectl describe application` |

## 📝 Workflow Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| `aws_region` | Any valid AWS region | us-west-2 |
| `cluster_name` | Any valid cluster name | finops-agents |
| `environment` | dev, staging, prod | dev |
| `gitops_repo_url` | GitHub repo URL | (optional) |

## ⏱️ Expected Timing

- **Provision Cluster**: ~15 minutes
- **Update kubeconfig**: ~1 minute
- **Install ArgoCD**: ~3 minutes
- **Wait for Capabilities**: ~5-10 minutes
- **Wait for Add-ons**: ~5-10 minutes
- **Wait for Financial Services**: ~5-10 minutes
- **Restart Agents**: ~2 minutes
- **Total**: ~45-60 minutes

## 📋 Files Created

```
.github/
└── workflows/
    ├── deploy-eks.yml          # Deployment workflow
    └── teardown-eks.yml        # Teardown workflow

docs/
├── GITHUB_ACTIONS_SETUP.md     # Detailed deploy setup
├── GITHUB_ACTIONS_TEARDOWN.md  # Detailed teardown guide
└── GITHUB_ACTIONS_QUICK_REF.md # This file (quick reference)
```

## 🔗 Useful Links

- [Deploy Workflow](.github/workflows/deploy-eks.yml)
- [Teardown Workflow](.github/workflows/teardown-eks.yml)
- [Deploy Setup Guide](GITHUB_ACTIONS_SETUP.md)
- [Teardown Guide](GITHUB_ACTIONS_TEARDOWN.md)
- [Main README](../README.md)
- [QuickStart](../QUICKSTART.md)

## 💡 Tips

1. **Start with dev environment** for testing
2. **Check workflow logs** if something fails
3. **Keep terraform state backed up** in S3
4. **Use consistent cluster names** across deployments
5. **Monitor AWS costs** during long-running workflows
6. **Save deployment artifacts** (kubeconfig, credentials)

---

For detailed setup instructions, see [GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)
