import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    event_id = event.get("event_id", "unknown")
    simulate_failure = event.get("simulate_failure", False)

    logger.info(
        "LAB12_START event_id=%s request_id=%s",
        event_id,
        context.aws_request_id
    )

    if simulate_failure:
        logger.error(
            "LAB12_PROCESSING_FAILED event_id=%s",
            event_id
        )

        raise RuntimeError(
            f"Simulated order processing failure: {event_id}"
        )

    logger.info(
        "LAB12_PROCESSING_SUCCESS event_id=%s",
        event_id
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Event processed successfully",
            "event_id": event_id
        })
    }
