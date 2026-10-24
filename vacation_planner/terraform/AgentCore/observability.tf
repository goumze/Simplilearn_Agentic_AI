data "aws_iam_policy_document" "transaction_search" {
  statement {
    sid     = "TransactionSearchXRayAccess"
    effect  = "Allow"
    actions = ["logs:PutLogEvents"]

    principals {
      type        = "Service"
      identifiers = ["xray.amazonaws.com"]
    }

    resources = [
      "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:aws/spans:*",
      "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/application-signals/data:*",
    ]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:xray:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

# Enables CloudWatch Transaction Search so AgentCore spans appear in GenAI Observability
resource "aws_cloudwatch_log_resource_policy" "transaction_search" {
  policy_name     = "TransactionSearchXRayAccess"
  policy_document = data.aws_iam_policy_document.transaction_search.json
}

resource "aws_xray_trace_segment_destination" "this" {
  destination = "CloudWatchLogs"

  depends_on = [aws_cloudwatch_log_resource_policy.transaction_search]
}
