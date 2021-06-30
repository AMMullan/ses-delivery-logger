resource "aws_iam_role" "notification_handler" {
  name = "${var.iam_role_prefix}-${data.aws_region.current.name}"

  assume_role_policy = file("${path.module}/resources/iam/notification_handler_trust.json")

  inline_policy {
    name = "SESNotificationHandlerPermissions"

    policy = templatefile(
      "${path.module}/resources/iam/notification_handler_policy.json",
      {
        account_id                 = data.aws_caller_identity.current.account_id,
        region                     = data.aws_region.current.name,
        dynamodb_table             = var.ddb_tbl_name,
        cloudwatch_logs_group_name = var.cloudwatch_logs_group_name,
        kms_cmk_key_id             = aws_kms_key.notification_handler.key_id
      }
    )
  }

  tags = var.resource_tags
}
