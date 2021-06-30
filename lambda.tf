resource "aws_lambda_function" "notification_handler" {
  function_name = var.lambda_name
  role          = aws_iam_role.notification_handler.arn

  runtime = "python3.8"

  filename         = "${path.module}/resources/lambda/notification_handler.zip"
  source_code_hash = filebase64sha256("${path.module}/resources/lambda/notification_handler.zip")
  handler          = "notification_handler.lambda_handler"

  environment {
    variables = {
      DYNAMODB_TABLE = var.ddb_tbl_name
    }
  }

  tags = var.resource_tags
}
