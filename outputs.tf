output "sns_topic_arn" {
  value = aws_sns_topic.delivery_logger.arn
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.delivery_logger.arn
}
