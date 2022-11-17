resource "aws_lambda_function" "delivery_logger" {
  function_name = var.lambda_name
  role          = aws_iam_role.delivery_logger.arn

  runtime     = "python3.9"
  memory_size = var.lambda_memory
  timeout     = var.lambda_timeout

  filename         = "${path.module}/resources/lambda/delivery_logger.zip"
  source_code_hash = filebase64sha256("${path.module}/resources/lambda/delivery_logger.zip")
  handler          = "delivery_logger.lambda_handler"

  environment {
    variables = {
      DYNAMODB_TABLE   = var.ddb_tbl_name
      DYNAMODB_TTL     = var.ddb_ttl_days
      LOGS_DESTINATION = var.cloudwatch_logs_destination
    }
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  tags = var.resource_tags
}

resource "aws_lambda_permission" "with_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delivery_logger.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.delivery_logger.arn
}
