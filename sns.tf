#tfsec:ignore:AWS016
resource "aws_sns_topic" "delivery_logger" {
  name = var.sns_topic_name
  policy = templatefile(
    "${path.module}/resources/sns/access_policy.json",
    {
      account_id = data.aws_caller_identity.current.account_id,
      region     = data.aws_region.current.name,
      topic_name = var.sns_topic_name
    }
  )

  tags = var.resource_tags
}

resource "aws_sns_topic_subscription" "delivery_logger_lambda" {
  topic_arn = aws_sns_topic.delivery_logger.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.delivery_logger.arn
}
