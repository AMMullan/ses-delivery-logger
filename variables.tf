variable "account_id" {
  description = "AWS Account ID"
}

variable "region" {
  description = "AWS Region where handler is provisioned"
}

variable "iam_role_prefix" {
  description = "Lambda IAM Execution Role Prefix - Will have var.region appended to it"
  default     = "SESNotificationHandler"
}

variable "lambda_name" {
  description = "Lambda Function Name"
  default     = "SESNotificationHandler"
}

variable "ddb_tbl_name" {
  description = "DynamoDB Table Name"
  default     = "SESNotificationHandler"
}

variable "cloudwatch_logs_group_name" {
  description = "Log Group Name for CloudWatch Logs"
  default     = "/aws/lambda/SESNotificationHandler"
}

variable "cloudwatch_logs_retention" {
  description = "How many days to retain CloudWatch Logs"
  default     = 180
}
