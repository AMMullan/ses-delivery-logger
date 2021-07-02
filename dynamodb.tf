#tfsec:ignore:AWS092
resource "aws_dynamodb_table" "notification_handler" {
  name = var.ddb_tbl_name

  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  hash_key  = "UserId"
  range_key = "PublishTime"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "PublishTime"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery_enabled # tfsec:ignore:AWS086
  }

  server_side_encryption {
    enabled = false
  }

  lifecycle {
    prevent_destroy = var.retain_dynamodb_on_destroy
  }

  tags = var.resource_tags
}
