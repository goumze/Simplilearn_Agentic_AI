output "api_gateway_rest_api_id" {
  description = "ID of the REST API"
  value       = aws_api_gateway_rest_api.vacation_planner.id
}

output "api_gateway_invoke_url" {
  description = "Full URL of the vacation_planner endpoint (POST)"
  value       = "${aws_api_gateway_stage.vacation_planner.invoke_url}/${var.resource_path}"
}
