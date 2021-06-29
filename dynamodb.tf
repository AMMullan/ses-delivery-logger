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
}
