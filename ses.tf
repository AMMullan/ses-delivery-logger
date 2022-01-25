resource "aws_ses_configuration_set" "notification_handler" {
  name = "notification_handler_set"
}

resource "aws_ses_event_destination" "notification_handler" {
  name                   = "notification-handler-sns"
  configuration_set_name = aws_ses_configuration_set.notification_handler.name
  enabled                = true
  matching_types         = ["bounce", "delivery", "complaint", "reject"]

  sns_destination {
    topic_arn = aws_sns_topic.notification_handler.arn
  }
}
