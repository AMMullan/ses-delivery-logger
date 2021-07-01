#tfsec:ignore:AWS089
resource "aws_cloudwatch_log_group" "notification_handler_lambda" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = var.logs_retention

  tags = var.resource_tags
}
