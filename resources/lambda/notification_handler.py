import os
import logging
import json

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')


def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    message_id = message['mail']['messageId']
    publish_time = event['Records'][0]['Sns']['Timestamp']

    notification_type = message.get('notificationType')

    ddb_item = {
        "PublishTime": publish_time,
        "NotificationType": notification_type
    }

    is_bounce = notification_type == 'Bounce'
    is_complaint = notification_type == 'Complaint'
    is_delivery = notification_type == 'Delivery'

    if is_bounce:
        bounce_detail = message.get('bounce')

        addresses = [
            recipient['emailAddress']
            for recipient in bounce_detail.get('bouncedRecipients')
        ]
        ddb_item['BounceType'] = bounce_detail.get('bounceType')
        ddb_item['BounceSubType'] = bounce_detail.get('bounceSubType')

    elif is_complaint:
        complaint_detail = message.get('complaint')
        addresses = [
            recipient['emailAddress']
            for recipient in complaint_detail.get('complainedRecipients')
        ]

        ddb_item['FeedbackId'] = complaint_detail.get('feedbackId')
        ddb_item['FeedbackType'] = complaint_detail.get('complaintFeedbackType')

    elif is_delivery:
        addresses = message['mail']['destination']

    else:
        logger.critical(f'Unknown message type: {notification_type} - Message Content: {json.dumps(message)}')
        raise Exception(f'Invalid message type received: {notification_type}')

    dynamodb = boto3.resource("dynamodb")
    handler_table = dynamodb.Table(DYNAMODB_TABLE)

    for address in addresses:
        if is_bounce:
            bounce_type = ddb_item.get('BounceType')

        ddb_item['UserId'] = address
        handler_table.put_item(Item=ddb_item)
