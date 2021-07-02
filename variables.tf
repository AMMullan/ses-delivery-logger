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

variable "logs_retention" {
  description = "CloudWatch Logs Retention (Days)"

  type    = number
  default = 180
}

variable "point_in_time_recovery_enabled" {
  description = "Enable Point-In-Time Recovery for DynamoDB"

  type    = bool
  default = false
}

variable "retain_dynamodb_on_destroy" {
  description = "Keep DynamoDB Table if destroying the Terraform"

  type    = bool
  default = false
}
