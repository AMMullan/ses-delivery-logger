import datetime
import json
import logging
import os
import sys
import time
import traceback
from collections import OrderedDict

import boto3

logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOGS_DESTINATION = os.environ.get('LOGS_DESTINATION')
DMY = datetime.datetime.now().strftime('%Y/%m/%d')
MAX_PUT_ATTEMPTS = 3

# Initialise the boto3 clients early in the Lambda warmup
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    logs = boto3.client('logs')

# TODO:
#   - Work out best way of NOT duplicating messages to DynamoDB if
#     Feedback Notifications and Configuration Set are both sending to this...

# IMPORTANT:
# You may see errors in Lambda if you have a high traffic volume. This has been known
# to be with Throttling on the describe_log_streams/create_log_stream API calls.
# You can simply request to increase these limits in Quotas until you iron out
# the issue.

def handle_bounce(message):
    bounce_detail = message.get('bounce')

    return {
        'BounceSummary': json.dumps(bounce_detail.get('bouncedRecipients')),
        'ReportingMTA': bounce_detail.get('reportingMTA', ''),
        'BounceType': bounce_detail.get('bounceType'),
        'BounceSubType': bounce_detail.get('bounceSubType'),
        'MessageTime': bounce_detail.get('timestamp')
    }


def handle_complaint(message):
    complaint_detail = message.get('complaint')

    return {
        'ComplaintSummary': json.dumps(complaint_detail.get('complainedRecipients')),
        'FeedbackId': complaint_detail.get('feedbackId'),
        'FeedbackType': complaint_detail.get('complaintFeedbackType'),
        'MessageTime': complaint_detail.get('arrivalDate')
    }


def handle_delivery(message):
    delivery_detail = message.get('delivery')

    return {
        'DestinationAddress': delivery_detail.get('recipients'),
        'ReportingMTA': delivery_detail.get('reportingMTA', ''),
        'SMTPResponse': delivery_detail.get('smtpResponse'),
        'MessageTime': delivery_detail.get('timestamp')
    }


def handle_delivery_delay(message):
    delay_detail = message.get('deliveryDelay')

    return {
        'DelayedRecipients': str(delay_detail.get('delayedRecipients')),
        'ExpirationTime': delay_detail.get('expirationTime'),
        'DelayType': delay_detail.get('delayType'),
        'MessageTime': delay_detail.get('timestamp')
    }


def handle_reject(message):
    return {
        'Reason': message.get('reject').get('reason')
    }


def handle_click(message):
    click_detail = message.get('click')

    return {
        'IPAddress': click_detail.get('ipAddress'),
        'Link': click_detail.get('link'),
        'LinkTags': json.dumps(click_detail.get('linkTags')),
        'UserAgent': click_detail.get('userAgent'),
        'MessageTime': click_detail.get('timestamp')
    }


def handle_open(message):
    open_detail = message.get('open')

    return {
        'IPAddress': open_detail.get('ipAddress'),
        'UserAgent': open_detail.get('userAgent'),
        'MessageTime': open_detail.get('timestamp')
    }


def handle_rendering_failure(message):
    failure_detail = message.get('failure')

    return {
        'ErrorMessage': failure_detail.get('errorMessage'),
        'TemplateName': failure_detail.get('templateName')
    }


def publish_to_cloudwatch(message_id, log_detail):
    # Using this log stream name to hopefully fix sequence issues
    log_stream_name = f'{DMY}/{message_id}'

    try:
        # Create Log Stream
        logs.create_log_stream(
            logGroupName=LOGS_DESTINATION,
            logStreamName=log_stream_name
        )
    except logs.exceptions.ResourceAlreadyExistsException:
        pass  # Doesn't matter if stream exists
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

    # Build put_log_events arguments
    log_event_args = {
        'logGroupName': LOGS_DESTINATION,
        'logStreamName': log_stream_name,
        'logEvents': [
            {
                'timestamp': int(round(time.time() * 1000)),
                'message': json.dumps(log_detail)
            }
        ]
    }

    count = 0
    while count < MAX_PUT_ATTEMPTS:
        count += 1

        try:
            logs.put_log_events(**log_event_args)

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
                "stackTrace": traceback_string,
                "log_event_args": log_event_args
            })
            logger.error(err_msg)
            return

        else:
            return


def lambda_handler(event, context):
    try:
        event_message = event['Records'][0]['Sns']['Message']
    except (KeyError, IndexError):
        return
    else:
        message = json.loads(event_message)

    mail_properties = message.get('mail', {})
    mail_tags = mail_properties.get('tags', {})

    # Ignore any event that doesn't have valid mail items.
    if not mail_properties:
        return

    message_time = event['Records'][0]['Sns']['Timestamp']

    type_key = (
        'eventType'
        if 'eventType' in message.keys()
        else 'notificationType'
    )
    event_type = message.get(type_key)

    log_detail = OrderedDict()

    message_id = mail_properties['messageId']
    log_detail['MessageId'] = message_id
    log_detail["MessageTime"] = message_time
    log_detail["EventType"] = event_type
    log_detail['FromAddress'] = mail_properties.get('source')
    log_detail['Subject'] = mail_properties.get('commonHeaders', {}).get('subject')

    # Get unique destinations
    log_detail['DestinationAddress'] = list(set(mail_properties.get('destination')))

    if source_ip := mail_tags.get('ses:source-ip'):
        log_detail['SourceIp'] = next(iter(source_ip or []), None)
    elif source_ip := mail_properties.get('sourceIp'):
        log_detail['SourceIp'] = source_ip

    if config_set := mail_tags.get('ses:configuration-set'):
        log_detail['ConfigSet'] = next(iter(config_set or []), None)
    else:
        log_detail['ConfigSet'] = None

    if iam_user := mail_tags.get('ses:caller-identity'):
        log_detail['IAMUser'] = next(iter(iam_user or []), None)
    elif iam_user := mail_properties.get('callerIdentity'):
        log_detail['IAMUser'] = iam_user

    event_actions = {
        'Bounce': lambda: handle_bounce(message),
        'Complaint': lambda: handle_complaint(message),
        'Delivery': lambda: handle_delivery(message),
        'DeliveryDelay': lambda: handle_delivery_delay(message),
        'Reject': lambda: handle_reject(message),
        'Click': lambda: handle_click(message),
        'Open': lambda: handle_open(message),
        'Rendering Failure': lambda: handle_rendering_failure(message)
    }
    if event_type in event_actions:
        log_detail.update(event_actions[event_type]())
    else:
        logger.critical(f'Unhandled Message Type: {event_type}')
        return

    publish_to_cloudwatch(message_id, log_detail)
