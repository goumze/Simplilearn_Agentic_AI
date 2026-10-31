output "memory_id" {
  value = aws_bedrockagentcore_memory.this.id
}

output "memory_arn" {
  value = aws_bedrockagentcore_memory.this.arn
}

output "summarization_strategy_id" {
  value = aws_bedrockagentcore_memory_strategy.summarization.memory_strategy_id
}

output "log_delivery_source_arn" {
  value = aws_cloudwatch_log_delivery_source.memory_application_logs.arn
}
