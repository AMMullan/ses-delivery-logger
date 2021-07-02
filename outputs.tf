output "sns_topic_arn" {
  value = aws_sns_topic.notification_handler.arn
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.notification_handler.arn
}
