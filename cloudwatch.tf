#tfsec:ignore:AWS089
resource "aws_cloudwatch_log_group" "notification_handler_lambda" {
  name              = var.cloudwatch_logs_group_name
  retention_in_days = var.cloudwatch_logs_retention

  tags = var.resource_tags
}
