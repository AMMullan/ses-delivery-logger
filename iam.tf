resource "aws_iam_role" "delivery_logger" {
  name = "${var.iam_role_prefix}-${data.aws_region.current.name}"

  assume_role_policy = file("${path.module}/resources/iam/delivery_logger_trust.json")

  inline_policy {
    name = "SESDeliveryLoggerPermissions"

    policy = templatefile(
      "${path.module}/resources/iam/delivery_logger_policy.json",
      {
        account_id                  = data.aws_caller_identity.current.account_id,
        region                      = data.aws_region.current.name,
        cloudwatch_logs_group_name  = "/aws/lambda/${var.lambda_name}",
        cloudwatch_logs_destination = var.cloudwatch_logs_destination,
        sqs_dlq_arn                 = aws_sqs_queue.dlq.arn
      }
    )
  }

  tags = var.resource_tags
}
