resource "aws_cloudwatch_log_group" "notification_handler_lambda" {
  name              = "${var.cloudwatch_logs_group_name}-${data.aws_region.current.name}"
  retention_in_days = var.cloudwatch_logs_retention

  kms_key_id = aws_kms_key.notification_handler.arn

  tags = var.resource_tags
}
