output "sns_topic_arn" {
  value = aws_sns_topic.notification_handler.arn
}
