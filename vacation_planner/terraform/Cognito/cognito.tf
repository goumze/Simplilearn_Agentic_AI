data "aws_region" "current" {}

# User pool acts as the OAuth 2.0 authorization server / identity provider.
resource "aws_cognito_user_pool" "vacation_planner" {
  name = var.user_pool_name

  deletion_protection = var.deletion_protection

  # Machine-to-machine (client credentials) only: no self sign-up, no end users.
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = var.password_min_length
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  mfa_configuration = "OFF"

  tags = var.tags
}

# Custom scope(s) must be defined on a resource server before a client can request them.
resource "aws_cognito_resource_server" "vacation_planner" {
  user_pool_id = aws_cognito_user_pool.vacation_planner.id
  identifier   = var.resource_server_identifier
  name         = var.resource_server_name

  scope {
    scope_name        = var.scope_name
    scope_description = var.scope_description
  }
}

# App client used by the vacation planner agent (OAuth client with Client ID & Secret).
resource "aws_cognito_user_pool_client" "vacation_planner" {
  name         = var.app_client_name
  user_pool_id = aws_cognito_user_pool.vacation_planner.id

  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = ["${aws_cognito_resource_server.vacation_planner.identifier}/${var.scope_name}"]
  supported_identity_providers         = ["COGNITO"]

  prevent_user_existence_errors = "ENABLED"

  access_token_validity = var.access_token_validity_minutes

  token_validity_units {
    access_token = "minutes"
  }

  depends_on = [aws_cognito_resource_server.vacation_planner]
}

# Hosted domain exposes the /oauth2/token endpoint used for the client credentials grant.
resource "aws_cognito_user_pool_domain" "vacation_planner" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.vacation_planner.id
}
