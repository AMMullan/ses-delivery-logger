#tfsec:ignore:AWS092
resource "aws_dynamodb_table" "notification_handler" {
  name = var.ddb_tbl_name

  billing_mode   = var.ddb_billing_mode
  read_capacity  = var.ddb_provisioned_read
  write_capacity = var.ddb_provisioned_write

  hash_key  = "MessageId"
  range_key = "MessageTime"

  attribute {
    name = "MessageId"
    type = "S"
  }

  attribute {
    name = "MessageTime"
    type = "S"
  }

  ttl {
    attribute_name = "RecordTTL"
    enabled        = var.ddb_enable_ttl
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery_enabled # tfsec:ignore:AWS086
  }

  server_side_encryption {
    enabled = var.ddb_encrypted
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = var.resource_tags
}
