import os
import logging
import json
import time
import datetime

import boto3

logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
TTL_DAYS = os.environ.get('DYNAMODB_TTL', 30)

# TODO:
#   - Work out best way of NOT duplicating messages to DynamoDB if
#     Feedback Notifications and Configuration Set are both sending to me...


def lambda_handler(event, context):
    try:
        message = json.loads(event['Records'][0]['Sns']['Message'])
    except json.JSONDecodeError:  # Not valid JSON, likely an SNS message.
        return

    # Ignore any event that doesn't have valid mail items.
    if 'mail' not in message:
        return

    message_time = message.get('mail').get('timestamp')

    type_key = 'eventType' if 'eventType' in message.keys() else 'notificationType'
    notification_type = message.get(type_key)

    ddb_item = {
        'MessageId': {'S': message.get('mail').get('messageId')},
        "MessageTime": {'S': message_time},
        "NotificationType": {'S': notification_type}
    }

    # Record the subject if the Headers are included
    eml_subject = message.get('mail').get('commonHeaders').get('subject')
    if eml_subject:
        ddb_item['Subject'] = {'S': eml_subject}

    if notification_type == 'Bounce':
        bounce_detail = message.get('bounce')

        ddb_item['Recipients'] = {'SS': bounce_detail.get('bouncedRecipients')}
        ddb_item['ReportingMTA'] = {'S': bounce_detail.get('reportingMTA')}
        ddb_item['BounceType'] = {'S': bounce_detail.get('bounceType')}
        ddb_item['BounceSubType'] = {'S': bounce_detail.get('bounceSubType')}
        ddb_item['Timestamp'] = {'S': bounce_detail.get('timestamp')}

    elif notification_type == 'Complaint':
        complaint_detail = message.get('complaint')

        ddb_item['Recipients'] = {'SS': complaint_detail.get('complainedRecipients')}
        ddb_item['UserAgent'] = {'S': complaint_detail.get('userAgent')}
        ddb_item['FeedbackId'] = {'S': complaint_detail.get('feedbackId')}
        ddb_item['FeedbackType'] = {'S': complaint_detail.get('complaintFeedbackType')}
        ddb_item['Timestamp'] = {'S': complaint_detail.get('arrivalDate')}

    elif notification_type == 'Delivery':
        delivery_detail = message.get('delivery')

        ddb_item['Recipients'] = {'SS': delivery_detail.get('recipients')}
        ddb_item['ReportingMTA'] = {'S': delivery_detail.get('reportingMTA')}
        ddb_item['SMTPResponse'] = {'S': delivery_detail.get('smtpResponse')}
        ddb_item['Timestamp'] = {'S': delivery_detail.get('timestamp')}

    elif notification_type == 'DeliveryDelay':
        delay_detail = message.get('deliveryDelay')

        ddb_item['Recipients'] = {'S': delay_detail.get('delayedRecipients')}
        ddb_item['ExpirationTime'] = delivery_detail.get('expirationTime')
        ddb_item['DelayType'] = delivery_detail.get('delayType')
        ddb_item['Timestamp'] = delivery_detail.get('timestamp')

    elif notification_type == 'Reject':
        ddb_item['Reason'] = message.get('reject').reason()

    elif notification_type == 'Click':
        click_detail = message.get('click')

        ddb_item['IPAddress'] = click_detail.get('ipAddress')
        ddb_item['Link'] = click_detail.get('link')
        ddb_item['LinkTags'] = click_detail.get('linkTags')
        ddb_item['UserAgent'] = click_detail.get('userAgent')
        ddb_item['Timestamp'] = click_detail.get('timestamp')

    elif notification_type == 'Open':
        open_detail = message.get('open')

        ddb_item['IPAddress'] = open_detail.get('ipAddress')
        ddb_item['UserAgent'] = open_detail.get('userAgent')
        ddb_item['Timestamp'] = open_detail.get('timestamp')

    elif notification_type == 'Rendering Failure':
        failure_detail = message.get('failure')

        ddb_item['ErrorMessage'] = failure_detail.get('errorMessage')
        ddb_item['TemplateName'] = failure_detail.get('templateName')

    else:
        logger.critical(f'Unknown message type: {notification_type} - Message Content: {json.dumps(message)}')
        return

    dynamodb = boto3.client("dynamodb")

    # Add TTL Attribute
    current_epoch = datetime.datetime.fromtimestamp(int(time.time()))
    ttl_epoch = int((current_epoch + datetime.timedelta(days=30)).timestamp())
    ddb_item['RecordTTL'] = {'N': str(ttl_epoch)}

    dynamodb.put_item(
        TableName=DYNAMODB_TABLE,
        Item=ddb_item
    )
