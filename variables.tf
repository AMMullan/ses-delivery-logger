variable "resource_tags" {
  description = "Tags to apply to all resources"

  type    = map(any)
  default = {}
}

variable "iam_role_prefix" {
  description = "Lambda IAM Execution Role Prefix - Will have var.region appended to it"

  type    = string
  default = "SESDeliveryLogger"
}

variable "lambda_name" {
  description = "Lambda Function Name"

  type    = string
  default = "SESDeliveryLogger"
}

variable "lambda_memory" {
  description = "Lambda Memory Allocation"

  type    = number
  default = 192
}

variable "lambda_timeout" {
  description = "Lambda Timeout"

  type    = number
  default = 10
}

variable "sns_topic_name" {
  description = "SNS Topic Name"

  type    = string
  default = "SESDeliveryLogger"
}

variable "cloudwatch_logs_destination" {
  description = "Name of the CloudWatch Logs Group to send events to"

  type    = string
  default = "SESDeliveryLogger"
}

variable "event_retention_days" {
  description = "How many days to retain events stored in CloudWatch Logs"

  type    = number
  default = 90
}

variable "logs_retention" {
  description = "CloudWatch Logs Retention (Days)"

  type    = number
  default = 180
}
