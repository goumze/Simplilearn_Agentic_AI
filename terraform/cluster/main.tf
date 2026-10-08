terraform {
  backend "s3" {
    bucket         = "goutam-terraform-state-251850081286-ap-south-1-an"
    key            = "agentic_aws_blog_key/cluster/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    # dynamodb_table = "terraform-locks"  # Uncomment after creating the table
  }

  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.43"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 3.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Generate a unique suffix to avoid KMS/resource conflicts across deployments
resource "random_string" "cluster_suffix" {
  length  = 8
  special = false
  lower   = true
  numeric = true
}

data "aws_availability_zones" "available" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  # Combine cluster name with random suffix for uniqueness
  cluster_name_with_suffix = "${var.cluster_name}-${random_string.cluster_suffix.result}"
  
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  tags = {
    Project = local.cluster_name_with_suffix
    Blog    = "finops-agents-on-eks-auto-mode"
  }
}

# ----------------------------------------------------------------------------
# VPC (3 AZs, private + public subnets, tagged for EKS LB discovery)
# ----------------------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.6"

  name = "${local.cluster_name_with_suffix}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 48)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = local.tags
}

# ----------------------------------------------------------------------------
# EKS Auto Mode cluster
#   - Auto Mode provides compute (managed NodePools), EBS CSI, VPC CNI,
#     kube-proxy, CoreDNS, AWS Load Balancer Controller, AND Pod Identity
#     out of the box — no managed addons needed.
#   - StorageClass + IngressClass still have to be created separately; see
#     gitops/addons/auto-mode-defaults/.
# ----------------------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.19"

  name               = local.cluster_name_with_suffix
  kubernetes_version = var.cluster_version

  # Auto Mode
  compute_config = {
    enabled    = true
    node_pools = ["system", "general-purpose"]
  }

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  endpoint_public_access = true

  # Give the Terraform caller cluster-admin so we can Helm-install ArgoCD
  # from the bootstrap stack.
  enable_cluster_creator_admin_permissions = true

  tags = local.tags
}