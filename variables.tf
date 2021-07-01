variable "resource_tags" {
  description = "Tags to apply to all resources"

  type    = map(any)
  default = {}
}

variable "iam_role_prefix" {
  description = "Lambda IAM Execution Role Prefix - Will have var.region appended to it"

  type    = string
  default = "SESNotificationHandler"
}

variable "lambda_name" {
  description = "Lambda Function Name"

  type    = string
  default = "SESNotificationHandler"
}

variable "sns_topic_name" {
  description = "SNS Topic Name"

  type    = string
  default = "SESNotificationHandler"
}
variable "ddb_tbl_name" {
  description = "DynamoDB Table Name"

  type    = string
  default = "SESNotificationHandler"
}

variable "cloudwatch_logs_group_name" {
  description = "Log Group Name for CloudWatch Logs"

  type    = string
  default = "/aws/lambda/SESNotificationHandler"
}

variable "cloudwatch_logs_retention" {
  description = "How many days to retain CloudWatch Logs"

  type    = number
  default = 180
}

variable "point_in_time_recovery_enabled" {
  description = "Enable Point-In-Time Recovery for DynamoDB"

  type    = bool
  default = false
}
