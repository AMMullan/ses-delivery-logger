resource "aws_sqs_queue" "dlq" {
  name                      = "SESDeliveryLogger-DLQ"
}
