import json
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 09 invoked")

    records = event.get("Records", [])

    # S3 may send a test event when configuring notifications.
    if event.get("Event") == "s3:TestEvent":
        logger.info("S3 notification test event received")
        return {
            "statusCode": 200,
            "message": "S3 test event received"
        }

    processed = []

    for record in records:
        bucket = record["s3"]["bucket"]["name"]

        encoded_key = record["s3"]["object"]["key"]

        object_key = unquote_plus(encoded_key)

        event_name = record.get("eventName", "unknown")

        logger.info(
            "LAB09_OBJECT_EVENT bucket=%s key=%s event=%s",
            bucket,
            object_key,
            event_name
        )

        processed.append({
            "bucket": bucket,
            "key": object_key,
            "event": event_name
        })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "S3 event processed",
            "processed_records": processed
        })
    }
