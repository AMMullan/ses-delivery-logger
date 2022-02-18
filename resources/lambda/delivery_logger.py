import os
import logging
import json
import time
import datetime
from collections import OrderedDict
import sys
import traceback

import boto3

logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
TTL_DAYS = os.environ.get('DYNAMODB_TTL', 30)
LOGS_DESTINATION = os.environ.get('LOGS_DESTINATION')
LOG_STREAM = datetime.datetime.today().strftime('%Y-%m-%d')

# TODO:
#   - Work out best way of NOT duplicating messages to DynamoDB if
#     Feedback Notifications and Configuration Set are both sending to this...


def lambda_handler(event, context):
    try:
        message = json.loads(event['Records'][0]['Sns']['Message'])
    except Exception:  # Not valid JSON, likely an SNS message.
        exception_type, exception_value, exception_traceback = sys.exc_info()
        traceback_string = traceback.format_exception(
            exception_type,
            exception_value,
            exception_traceback
        )
        err_msg = json.dumps({
            "errorType": exception_type.__name__,
            "errorMessage": str(exception_value),
            "stackTrace": traceback_string
        })
        logger.error(err_msg)
        return

    # Ignore any event that doesn't have valid mail items.
    if 'mail' not in message:
        return

    message_time = event['Records'][0]['Sns']['Timestamp']

    type_key = 'eventType' if 'eventType' in message.keys() else 'notificationType'
    event_type = message.get(type_key)

    ddb_item = OrderedDict()
    logs_item = OrderedDict()

    ddb_item['MessageId'] = {'S': message.get('mail').get('messageId')}
    ddb_item["MessageTime"] = {'S': message_time}
    ddb_item["EventType"] = {'S': event_type}

    logs_item['MessageId'] = message.get('mail').get('messageId')
    logs_item["MessageTime"] = message_time
    logs_item["EventType"] = event_type

    # Record the subject if the Headers are included
    eml_subject = message.get('mail', {}).get('commonHeaders', {}).get('subject')
    if eml_subject:
        ddb_item['Subject'] = {'S': eml_subject}
        logs_item['Subject'] = eml_subject

    # Get unique destinations
    destination_address = list(set(message.get('mail').get('destination')))

    config_set = message.get('mail').get('tags', {}).get('ses:configuration-set')
    if config_set:
        ddb_item['ConfigSet'] = {'S': next(iter(config_set or []), None)}
        logs_item['ConfigSet'] = next(iter(config_set or []), None)

    iam_user = message.get('mail').get('tags', {}).get('ses:caller-identity')
    if iam_user:
        ddb_item['IAMUser'] = {'S': next(iter(iam_user or []), None)}
        logs_item['IAMUser'] = next(iter(iam_user or []), None)

    from_address = message.get('mail').get('source')
    ddb_item['FromAddress'] = {'S': from_address}
    logs_item['FromAddress'] = from_address

    if event_type == 'Bounce':
        bounce_detail = message.get('bounce')

        ddb_item['BounceSummary'] = {'S': json.dumps(bounce_detail.get('bouncedRecipients'))}
        ddb_item['DestinationAddress'] = {'SS': destination_address}
        ddb_item['ReportingMTA'] = {'S': bounce_detail.get('reportingMTA', '')}
        ddb_item['BounceType'] = {'S': bounce_detail.get('bounceType')}
        ddb_item['BounceSubType'] = {'S': bounce_detail.get('bounceSubType')}
        ddb_item['MessageTime'] = {'S': bounce_detail.get('timestamp')}

        logs_item['BounceSummary'] = json.dumps(bounce_detail.get('bouncedRecipients'))
        logs_item['DestinationAddress'] = destination_address
        logs_item['ReportingMTA'] = bounce_detail.get('reportingMTA', '')
        logs_item['BounceType'] = bounce_detail.get('bounceType')
        logs_item['BounceSubType'] = bounce_detail.get('bounceSubType')
        logs_item['MessageTime'] = bounce_detail.get('timestamp')

    elif event_type == 'Complaint':
        complaint_detail = message.get('complaint')

        ddb_item['ComplaintSummary'] = {'S': json.dumps(complaint_detail.get('complainedRecipients'))}
        ddb_item['DestinationAddress'] = {'SS': destination_address}
        ddb_item['FeedbackId'] = {'S': complaint_detail.get('feedbackId')}
        ddb_item['FeedbackType'] = {'S': complaint_detail.get('complaintFeedbackType')}
        ddb_item['MessageTime'] = {'S': complaint_detail.get('arrivalDate')}

        logs_item['ComplaintSummary'] = json.dumps(complaint_detail.get('complainedRecipients'))
        logs_item['DestinationAddress'] = destination_address
        logs_item['FeedbackId'] = complaint_detail.get('feedbackId')
        logs_item['FeedbackType'] = complaint_detail.get('complaintFeedbackType')
        logs_item['MessageTime'] = complaint_detail.get('arrivalDate')

    elif event_type == 'Delivery':
        delivery_detail = message.get('delivery')

        ddb_item['DestinationAddress'] = {'SS': delivery_detail.get('recipients')}
        ddb_item['ReportingMTA'] = {'S': delivery_detail.get('reportingMTA', '')}
        ddb_item['SMTPResponse'] = {'S': delivery_detail.get('smtpResponse')}
        ddb_item['MessageTime'] = {'S': delivery_detail.get('timestamp')}

        logs_item['DestinationAddress'] = delivery_detail.get('recipients')
        logs_item['ReportingMTA'] = delivery_detail.get('reportingMTA', '')
        logs_item['SMTPResponse'] = delivery_detail.get('smtpResponse')
        logs_item['MessageTime'] = delivery_detail.get('timestamp')

    elif event_type == 'DeliveryDelay':
        delay_detail = message.get('deliveryDelay')

        ddb_item['DelayedRecipients'] = {'S': str(delay_detail.get('delayedRecipients'))}
        ddb_item['ExpirationTime'] = {'S': delay_detail.get('expirationTime')}
        ddb_item['DelayType'] = {'S': delay_detail.get('delayType')}
        ddb_item['MessageTime'] = {'S': delay_detail.get('timestamp')}

        logs_item['DelayedRecipients'] = str(delay_detail.get('delayedRecipients'))
        logs_item['ExpirationTime'] = delay_detail.get('expirationTime')
        logs_item['DelayType'] = delay_detail.get('delayType')
        logs_item['MessageTime'] = delay_detail.get('timestamp')

    elif event_type == 'Reject':
        ddb_item['DestinationAddress'] = {'SS': destination_address}
        ddb_item['Reason'] = {'S': message.get('reject').get('reason')}

        logs_item['DestinationAddress'] = destination_address
        logs_item['Reason'] = message.get('reject').get('reason')

    elif event_type == 'Click':
        click_detail = message.get('click')

        ddb_item['DestinationAddress'] = {'SS': destination_address}
        ddb_item['IPAddress'] = {'S': click_detail.get('ipAddress')}
        ddb_item['Link'] = {'S': click_detail.get('link')}
        ddb_item['LinkTags'] = {'S': json.dumps(click_detail.get('linkTags'))}
        ddb_item['UserAgent'] = {'S': click_detail.get('userAgent')}
        ddb_item['MessageTime'] = {'S': click_detail.get('timestamp')}

        logs_item['DestinationAddress'] = destination_address
        logs_item['IPAddress'] = click_detail.get('ipAddress')
        logs_item['Link'] = click_detail.get('link')
        logs_item['LinkTags'] = json.dumps(click_detail.get('linkTags'))
        logs_item['UserAgent'] = click_detail.get('userAgent')
        logs_item['MessageTime'] = click_detail.get('timestamp')

    elif event_type == 'Open':
        open_detail = message.get('open')

        ddb_item['DestinationAddress'] = {'SS': destination_address}
        ddb_item['IPAddress'] = {'S': open_detail.get('ipAddress')}
        ddb_item['UserAgent'] = {'S': open_detail.get('userAgent')}
        ddb_item['MessageTime'] = {'S': open_detail.get('timestamp')}

        logs_item['DestinationAddress'] = destination_address
        logs_item['IPAddress'] = open_detail.get('ipAddress')
        logs_item['UserAgent'] = open_detail.get('userAgent')
        logs_item['MessageTime'] = open_detail.get('timestamp')

    elif event_type == 'Rendering Failure':
        failure_detail = message.get('failure')

        ddb_item['ErrorMessage'] = {'S': failure_detail.get('errorMessage')}
        ddb_item['TemplateName'] = {'S': failure_detail.get('templateName')}

        logs_item['ErrorMessage'] = failure_detail.get('errorMessage')
        logs_item['TemplateName'] = failure_detail.get('templateName')

    else:
        logger.critical(f'Unhandled Message Type: {event_type} - Message Content: {json.dumps(message)}')
        return

    dynamodb = boto3.client("dynamodb")

    # Add TTL Attribute
    current_epoch = datetime.datetime.fromtimestamp(int(time.time()))
    ttl_epoch = int((current_epoch + datetime.timedelta(days=30)).timestamp())
    ddb_item['RecordTTL'] = {'N': str(ttl_epoch)}

    try:
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=ddb_item
        )
    except Exception:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        traceback_string = traceback.format_exception(
            exception_type,
            exception_value,
            exception_traceback
        )
        err_msg = json.dumps({
            "errorType": exception_type.__name__,
            "errorMessage": str(exception_value),
            "stackTrace": traceback_string
        })
        logger.error(err_msg)

    logs = boto3.client('logs')
    # Get Upload Sequence Token
    try:
        streams = logs.describe_log_streams(
            logGroupName=LOGS_DESTINATION,
            logStreamNamePrefix=LOG_STREAM
        ).get('logStreams')
    except logs.exceptions.ResourceNotFoundException:
        # Log Group Doesn't Exist
        return
    except logs.exceptions.AccessDeniedException:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        traceback_string = traceback.format_exception(
            exception_type,
            exception_value,
            exception_traceback
        )
        err_msg = json.dumps({
            "errorType": exception_type.__name__,
            "errorMessage": str(exception_value),
            "stackTrace": traceback_string
        })
        logger.warning(err_msg)
        return
        return
    else:
        sequence_token = next(
            iter(
                [
                    sequence.get('uploadSequenceToken')
                    for sequence in streams
                ] or []
            ), None
        )

        try:
            logs.create_log_stream(
                logGroupName=LOGS_DESTINATION,
                logStreamName=LOG_STREAM
            )
        except logs.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception:
            exception_type, exception_value, exception_traceback = sys.exc_info()
            traceback_string = traceback.format_exception(
                exception_type,
                exception_value,
                exception_traceback
            )
            err_msg = json.dumps({
                "errorType": exception_type.__name__,
                "errorMessage": str(exception_value),
                "stackTrace": traceback_string
            })
            logger.error(err_msg)
            return

        log_event_args = {
            'logGroupName': LOGS_DESTINATION,
            'logStreamName': LOG_STREAM,
            'logEvents': [
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': json.dumps(logs_item)
                }
            ]
        }
        if sequence_token:
            log_event_args.update({
                'sequenceToken': sequence_token
            })

        logs.put_log_events(**log_event_args)
