module "ecr" {
  source = "./ECR"

  repository_name = "vacation_planner"
  force_delete    = true
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}
