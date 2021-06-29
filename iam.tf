resource "aws_iam_role" "notification_handler" {
  name = "${var.iam_role_prefix}-${var.region}"

  assume_role_policy = file("resources/iam/notification_handler_trust.json")

  inline_policy = templatefile(
    "resources/iam/notification_handler_policy.json",
    {
      account_id                 = var.account_id,
      region                     = var.region,
      dynamodb_table             = var.ddb_tbl_name,
      cloudwatch_logs_group_name = var.cloudwatch_logs_group_name
    }
  )
}
