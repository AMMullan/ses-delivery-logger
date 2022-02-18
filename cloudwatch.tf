#tfsec:ignore:AWS089
resource "aws_cloudwatch_log_group" "delivery_logger_lambda" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = var.logs_retention

  tags = var.resource_tags
}

resource "aws_cloudwatch_log_group" "events_destination" {
  name              = var.cloudwatch_logs_destination
  retention_in_days = var.logs_retention

  tags = var.resource_tags
}
