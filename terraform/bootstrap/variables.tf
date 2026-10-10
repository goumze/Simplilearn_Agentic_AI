variable "aws_region" {
  description = "AWS region hosting the EKS cluster"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name (must match the cluster stack output)"
  type        = string
  default     = "finops-agents"
}

variable "argocd_chart_version" {
  description = "argo-cd Helm chart version (Argo CD 3.x; 2.12 cannot diff Deployments on Kubernetes 1.33+)"
  type        = string
  default     = "10.10.2"
}

variable "argocd_domain" {
  description = "Optional DNS name for the ArgoCD UI (ingress wired separately)"
  type        = string
  default     = "argocd.example.com"
}

variable "gitops_repo_url" {
  description = "Git repository URL hosting the gitops tree"
  type        = string
  default     = "https://github.com/goumze/Simplilearn_Agentic_AI"
}

variable "gitops_repo_branch" {
  description = "Branch ArgoCD should track"
  type        = string
  default     = "feature/aws_financial_services_agentic_demo"
}

variable "gitops_root_path" {
  description = "Path to the app-of-apps root within the repo"
  type        = string
  default     = "gitops/root"
}