# GitHub Actions Deployment Guide

This guide explains how to use the GitHub Actions workflow (`deploy-eks.yml`) to automate the EKS cluster provisioning and multi-agent platform deployment.

## 📋 Prerequisites

Before you can use this workflow, you need to set up the following:

### 1. AWS Account & Permissions

You'll need:
- AWS Account with appropriate permissions
- IAM role for GitHub Actions (using OIDC)
- Permissions for:
  - EKS (Create/Delete clusters)
  - VPC (Create/Delete VPCs, subnets, security groups)
  - IAM (Create roles, policies)
  - ACK Services (Bedrock, etc.)

### 2. GitHub Repository Setup

#### Option A: Using AWS OIDC Provider (Recommended)

1. **Create OIDC Provider in AWS:**
   ```bash
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --client-id-list sts.amazonaws.com
   ```

2. **Create IAM Role for GitHub Actions:**
   ```bash
   cat > trust-policy.json << EOF
   {
     "Version": "2012-10-17",
     "Statement": [
       {
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
       }
     ]
   }
   EOF

   aws iam create-role \
     --role-name github-actions-eks-role \
     --assume-role-policy-document file://trust-policy.json
   ```

3. **Attach Permissions Policy:**
   ```bash
   cat > eks-policy.json << EOF
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "eks:*",
           "ec2:*",
           "iam:*",
           "logs:*",
           "s3:*"
         ],
         "Resource": "*"
       }
     ]
   }
   EOF

   aws iam put-role-policy \
     --role-name github-actions-eks-role \
     --policy-name eks-deployment-policy \
     --policy-document file://eks-policy.json
   ```

#### Option B: Using AWS Access Keys

1. Create an IAM user with EKS permissions
2. Generate access keys
3. Add to GitHub Secrets (see below)

### 3. GitHub Secrets Setup

Add the following secrets to your GitHub repository:

**For OIDC (Option A):**
- `AWS_ROLE_TO_ASSUME`: `arn:aws:iam::YOUR_ACCOUNT_ID:role/github-actions-eks-role`

**For Access Keys (Option B):**
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

**Navigate to:**
Settings → Secrets and variables → Actions → New repository secret

### 4. Terraform Backend Configuration

The workflow uses Terraform to provision resources. Configure the backend:

**Option A: Local State (For Testing)**
- No additional setup needed
- State stored in workflow artifacts

**Option B: Remote State (Recommended)**
- Create S3 bucket for Terraform state
- Create DynamoDB table for state locking
- Add backend configuration to `terraform/cluster/main.tf` and `terraform/bootstrap/main.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "eks-deployment/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## 🚀 Using the Workflow

### Trigger the Workflow

The workflow is manually triggered via GitHub Actions UI:

1. Go to **Actions** tab in your repository
2. Select **Deploy Multi-Agent Platform to EKS** workflow
3. Click **Run workflow**
4. Fill in the parameters:
   - **AWS Region**: `us-west-2` (or your preferred region)
   - **Cluster Name**: `finops-agents` (or your preferred name)
   - **GitOps Repo URL**: (optional, leave blank to use default)
   - **Environment**: `dev`, `staging`, or `prod`
5. Click **Run workflow**

### Workflow Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `aws_region` | `us-west-2` | AWS region for EKS cluster |
| `cluster_name` | `finops-agents` | Name of the EKS cluster |
| `gitops_repo_url` | (optional) | GitOps repository URL for ArgoCD |
| `environment` | `dev` | Deployment environment (dev/staging/prod) |

### Monitor the Workflow

1. Watch the workflow run in the **Actions** tab
2. Each job shows its progress:
   - ✅ Green = Success
   - 🔴 Red = Failed
   - 🟡 Yellow = In Progress
3. Click on a job to see detailed logs

### Workflow Jobs

The workflow runs the following jobs in sequence:

1. **Validate** - Validate configuration
2. **Provision Cluster** - Create EKS cluster (~15 mins)
3. **Update kubeconfig** - Configure kubectl access
4. **Install ArgoCD** - Set up GitOps controller
5. **Wait for Capabilities** - Wait for ACK and kro (~5-10 mins)
6. **Wait for Add-ons** - Wait for platform add-ons to sync (~5-10 mins)
7. **Wait for Financial Services** - Wait for agent resources (~5-10 mins)
8. **Restart Agents** - Restart agent deployments
9. **Post-Deployment** - Generate deployment report

**Total Time:** ~45-60 minutes

## 📊 Accessing Your Deployment

After the workflow completes successfully, you'll get:

### 1. From Workflow Summary

The workflow generates a deployment report with:
- Cluster information
- ArgoCD admin password
- Access commands
- Verification steps

### 2. Manual Access

**Update kubeconfig:**
```bash
aws eks update-kubeconfig --region us-west-2 --name finops-agents
```

**Verify nodes:**
```bash
kubectl get nodes
```

**Check agents:**
```bash
kubectl get pods -n financial-services
```

**Access ArgoCD UI:**
```bash
kubectl port-forward -n argocd svc/argocd-server 8080:80
# Open http://localhost:8080
# Username: admin
# Password: (from workflow summary)
```

## 🧪 Test the Deployment

Once deployed, test the multi-agent system:

```bash
# Port-forward to agent gateway
kubectl port-forward -n agentgateway-system svc/agent-gateway-proxy 8080:8080 &

# Create authorization token
TOKEN=$(kubectl create token financial-advisor-sa \
  -n financial-services \
  --duration=1h \
  --audience=agent-gateway)

# Test advisor agent
curl -sS -X POST http://localhost:8080/agents/financial-advisor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"I have 100 AAPL and 50 GOOGL. Is my portfolio balanced for medium risk?"}' \
  | jq .result
```

## 🛑 Cleanup

### Manual Cleanup

To destroy all resources:

```bash
# Destroy bootstrap resources
cd terraform/bootstrap
terraform destroy \
  -var "aws_region=us-west-2" \
  -var "cluster_name=finops-agents"

# Destroy cluster
cd ../cluster
terraform destroy \
  -var "aws_region=us-west-2" \
  -var "cluster_name=finops-agents"
```

### Automatic Cleanup (Dev Only)

If you deploy to the `dev` environment and the workflow fails, resources are automatically cleaned up.

## 🔧 Workflow Customization

### Custom Environment Variables

Modify `.github/workflows/deploy-eks.yml`:

```yaml
env:
  AWS_REGION: ${{ github.event.inputs.aws_region || 'us-west-2' }}
  CLUSTER_NAME: ${{ github.event.inputs.cluster_name || 'finops-agents' }}
  # Add custom variables here
  CUSTOM_VAR: "value"
```

### Custom Terraform Variables

Add to `terraform/cluster/variables.tf` and update workflow:

```yaml
- name: Apply Terraform (cluster)
  run: |
    cd terraform/cluster
    terraform apply -auto-approve tfplan \
      -var "custom_var=value"
```

### Conditional Steps

Run steps only in specific environments:

```yaml
- name: Some Step
  if: github.event.inputs.environment == 'prod'
  run: echo "This only runs in prod"
```

## 📝 Troubleshooting

### Workflow Fails During Provisioning

**Check logs:**
1. Click the failed job
2. Expand the step that failed
3. Review error message

**Common issues:**
- Insufficient AWS permissions → Add more IAM permissions
- Region doesn't support EKS Auto Mode → Use a different region
- Quota exceeded → Request AWS quota increase

### kubectl Commands Fail

**Verify kubeconfig:**
```bash
aws eks update-kubeconfig --region us-west-2 --name finops-agents
kubectl cluster-info
```

**Check context:**
```bash
kubectl config current-context
kubectl config get-contexts
```

### ArgoCD Applications Not Syncing

**Check application status:**
```bash
kubectl get applications -n argocd
kubectl describe application financial-services -n argocd
```

**Check application logs:**
```bash
kubectl logs -n argocd deployment/argocd-application-controller
```

### Agents Not Starting

**Check pod status:**
```bash
kubectl get pods -n financial-services
kubectl describe pod -n financial-services
kubectl logs -n financial-services <pod-name>
```

**Check AgentCore resources:**
```bash
kubectl get agentcorememories,agentcorebrowsers,agentcorecodeinterpreters \
  -n financial-services
```

## 🔒 Security Best Practices

1. **Use OIDC** instead of access keys
2. **Limit role permissions** to necessary AWS services
3. **Rotate credentials** regularly
4. **Use environment-specific** roles (dev/staging/prod)
5. **Enable audit logging** for Terraform state
6. **Protect secrets** in GitHub
7. **Review workflow logs** for sensitive data leaks

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)

## 🤝 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review workflow logs in detail
3. Consult AWS documentation
4. Open an issue on GitHub

---

**Last Updated**: 2024
