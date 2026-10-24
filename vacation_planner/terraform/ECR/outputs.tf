output "repository_url" {
  description = "ECR repository URL used for docker tag/push"
  value       = aws_ecr_repository.vacation_planner.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN"
  value       = aws_ecr_repository.vacation_planner.arn
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.vacation_planner.name
}
