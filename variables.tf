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

variable "ddb_tbl_name" {
  description = "DynamoDB Table Name"

  type    = string
  default = "SESDeliveryLogger"
}

variable "ddb_enable_ttl" {
  description = "Enable TTL on DynamoDB Records"

  type    = bool
  default = true
}

variable "ddb_ttl_days" {
  description = "Number of days to retain record"

  type    = number
  default = 30
}

variable "ddb_billing_mode" {
  description = "Capacity Billing - Provisioned or Pay-Per-Request"

  type    = string
  default = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.ddb_billing_mode)
    error_message = "Valid values for var: ddb_billing_mode are (PAY_PER_REQUEST, PROVISIONED)."
  }
}

variable "ddb_provisioned_read" {
  description = "DynamoDB Provisioned Read Capacity Units"

  type    = number
  default = 0
}

variable "ddb_provisioned_write" {
  description = "DynamoDB Provisioned Write Capacity Units"

  type    = number
  default = 0
}

variable "ddb_encrypted" {
  description = "Enable DynamoDB Encryption"

  type    = bool
  default = true
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
