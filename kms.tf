resource "aws_kms_key" "notification_handler" {
  description = "SES Notification Handler"

  enable_key_rotation = true
  policy = templatefile(
    "${path.module}/resources/kms/key_policy.json",
    {
      account_id                 = data.aws_caller_identity.current.account_id,
      region                     = data.aws_region.current.name,
      iam_role_name              = "${var.iam_role_prefix}-${data.aws_region.current.name}",
      dynamodb_table             = var.ddb_tbl_name,
      cloudwatch_logs_group_name = var.cloudwatch_logs_group_name
    }
  )

  tags = var.resource_tags
}
