output "user_pool_id" {
  description = "Cognito user pool ID"
  value       = aws_cognito_user_pool.vacation_planner.id
}

output "user_pool_arn" {
  description = "Cognito user pool ARN"
  value       = aws_cognito_user_pool.vacation_planner.arn
}

output "issuer_url" {
  description = "OIDC issuer URL; JWT 'iss' claim and the value the AgentCore Gateway validates against"
  value       = "https://cognito-idp.${data.aws_region.current.region}.amazonaws.com/${aws_cognito_user_pool.vacation_planner.id}"
}

output "jwks_uri" {
  description = "JWKS endpoint used to verify JWT signatures"
  value       = "https://cognito-idp.${data.aws_region.current.region}.amazonaws.com/${aws_cognito_user_pool.vacation_planner.id}/.well-known/jwks.json"
}

output "token_endpoint" {
  description = "OAuth token endpoint for the client credentials grant"
  value       = "https://${aws_cognito_user_pool_domain.vacation_planner.domain}.auth.${data.aws_region.current.region}.amazoncognito.com/oauth2/token"
}

output "client_id" {
  description = "App client ID"
  value       = aws_cognito_user_pool_client.vacation_planner.id
}

output "client_secret" {
  description = "App client secret"
  value       = aws_cognito_user_pool_client.vacation_planner.client_secret
  sensitive   = true
}

output "oauth_scope" {
  description = "Full custom scope to request in the token call"
  value       = "${aws_cognito_resource_server.vacation_planner.identifier}/${var.scope_name}"
}
