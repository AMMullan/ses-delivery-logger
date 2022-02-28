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

LOGS_DESTINATION = os.environ.get('LOGS_DESTINATION')
DMY = datetime.datetime.today().strftime('%Y/%m/%d')
MAX_PUT_ATTEMPTS = 3

# TODO:
#   - Work out best way of NOT duplicating messages to DynamoDB if
#     Feedback Notifications and Configuration Set are both sending to this...

# IMPORTANT:
# You may see errors in Lambda if you have a high traffic volume. This has been known
# to be with Throttling on the describe_log_streams/create_log_stream API calls.
# You can simply request to increase these limits in Quotas until you iron out
# the issue.


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

    logs_item = OrderedDict()

    message_id = message.get('mail').get('messageId')
    logs_item['MessageId'] = message_id
    logs_item["MessageTime"] = message_time
    logs_item["EventType"] = event_type

    # Record the subject if the Headers are included
    eml_subject = message.get('mail', {}).get('commonHeaders', {}).get('subject')
    if eml_subject:
        logs_item['Subject'] = eml_subject

    # Get unique destinations
    destination_address = list(set(message.get('mail').get('destination')))

    config_set = message.get('mail').get('tags', {}).get('ses:configuration-set')
    if config_set:
        logs_item['ConfigSet'] = next(iter(config_set or []), None)

    iam_user = message.get('mail').get('tags', {}).get('ses:caller-identity')
    if iam_user:
        logs_item['IAMUser'] = next(iter(iam_user or []), None)

    from_address = message.get('mail').get('source')
    logs_item['FromAddress'] = from_address

    if event_type == 'Bounce':
        bounce_detail = message.get('bounce')

        logs_item['BounceSummary'] = json.dumps(bounce_detail.get('bouncedRecipients'))
        logs_item['DestinationAddress'] = destination_address
        logs_item['ReportingMTA'] = bounce_detail.get('reportingMTA', '')
        logs_item['BounceType'] = bounce_detail.get('bounceType')
        logs_item['BounceSubType'] = bounce_detail.get('bounceSubType')
        logs_item['MessageTime'] = bounce_detail.get('timestamp')

    elif event_type == 'Complaint':
        complaint_detail = message.get('complaint')

        logs_item['ComplaintSummary'] = json.dumps(complaint_detail.get('complainedRecipients'))
        logs_item['DestinationAddress'] = destination_address
        logs_item['FeedbackId'] = complaint_detail.get('feedbackId')
        logs_item['FeedbackType'] = complaint_detail.get('complaintFeedbackType')
        logs_item['MessageTime'] = complaint_detail.get('arrivalDate')

    elif event_type == 'Delivery':
        delivery_detail = message.get('delivery')

        logs_item['DestinationAddress'] = delivery_detail.get('recipients')
        logs_item['ReportingMTA'] = delivery_detail.get('reportingMTA', '')
        logs_item['SMTPResponse'] = delivery_detail.get('smtpResponse')
        logs_item['MessageTime'] = delivery_detail.get('timestamp')

    elif event_type == 'DeliveryDelay':
        delay_detail = message.get('deliveryDelay')

        logs_item['DelayedRecipients'] = str(delay_detail.get('delayedRecipients'))
        logs_item['ExpirationTime'] = delay_detail.get('expirationTime')
        logs_item['DelayType'] = delay_detail.get('delayType')
        logs_item['MessageTime'] = delay_detail.get('timestamp')

    elif event_type == 'Reject':
        logs_item['DestinationAddress'] = destination_address
        logs_item['Reason'] = message.get('reject').get('reason')

    elif event_type == 'Click':
        click_detail = message.get('click')

        logs_item['DestinationAddress'] = destination_address
        logs_item['IPAddress'] = click_detail.get('ipAddress')
        logs_item['Link'] = click_detail.get('link')
        logs_item['LinkTags'] = json.dumps(click_detail.get('linkTags'))
        logs_item['UserAgent'] = click_detail.get('userAgent')
        logs_item['MessageTime'] = click_detail.get('timestamp')

    elif event_type == 'Open':
        open_detail = message.get('open')

        logs_item['DestinationAddress'] = destination_address
        logs_item['IPAddress'] = open_detail.get('ipAddress')
        logs_item['UserAgent'] = open_detail.get('userAgent')
        logs_item['MessageTime'] = open_detail.get('timestamp')

    elif event_type == 'Rendering Failure':
        failure_detail = message.get('failure')

        logs_item['ErrorMessage'] = failure_detail.get('errorMessage')
        logs_item['TemplateName'] = failure_detail.get('templateName')

    else:
        logger.critical(f'Unhandled Message Type: {event_type} - Message Content: {json.dumps(message)}')
        return

    logs = boto3.client('logs')

    # Using this log stream name to hopefully fix sequence issues
    log_stream_name = f'{DMY}/{message_id}'

    try:
        # Create Log Stream
        logs.create_log_stream(
            logGroupName=LOGS_DESTINATION,
            logStreamName=log_stream_name
        )
    except logs.exceptions.ResourceAlreadyExistsException:
        # Doesn't matter if stream exists
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

    # Build put_log_events arguments
    log_event_args = {
        'logGroupName': LOGS_DESTINATION,
        'logStreamName': log_stream_name,
        'logEvents': [
            {
                'timestamp': int(round(time.time() * 1000)),
                'message': json.dumps(logs_item)
            }
        ]
    }

    # Get Upload Sequence Token
    try:
        streams = logs.describe_log_streams(
            logGroupName=LOGS_DESTINATION,
            logStreamNamePrefix=log_stream_name
        ).get('logStreams')
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
        logger.warning(err_msg)
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

        if sequence_token:
            log_event_args.update({
                'sequenceToken': sequence_token
            })

        count = 0
        while count < MAX_PUT_ATTEMPTS:
            count += 1

            try:
                logs.put_log_events(**log_event_args)

            except logs.exceptions.InvalidSequenceTokenException as exception:
                log_event_args['sequenceToken'] = exception.response['expectedSequenceToken']

                if count == MAX_PUT_ATTEMPTS:
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
