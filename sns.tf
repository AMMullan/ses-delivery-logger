resource "aws_sns_topic" "notification_handler" {
  name = "SESNotificationHandler"
}

resource "aws_sns_topic_subscription" "notification_handler_lambda" {
  topic_arn = aws_sns_topic.notification_handler.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.notification_handler.arn
}
