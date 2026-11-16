import json
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_SLEEP_SECONDS = 8


def lambda_handler(event, context):
    request_id = event.get("request_id", "unknown")
    sleep_seconds = int(event.get("sleep_seconds", 6))

    if not 1 <= sleep_seconds <= MAX_SLEEP_SECONDS:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "sleep_seconds must be between 1 and 8"
            })
        }

    logger.info(
        "LAB11_START request=%s sleep=%s",
        request_id,
        sleep_seconds
    )

    start = time.monotonic()

    time.sleep(sleep_seconds)

    duration = round(time.monotonic() - start, 3)

    logger.info(
        "LAB11_COMPLETE request=%s duration=%s",
        request_id,
        duration
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Order processed successfully",
            "request_id": request_id,
            "duration_seconds": duration
        })
    }
