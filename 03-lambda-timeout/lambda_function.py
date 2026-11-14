import json
import time


def lambda_handler(event, context):
    print("Lambda Lab 03 started", flush=True)

    processing_seconds = event.get("processing_seconds", 6)

    print(
        f"Requested processing time: {processing_seconds} seconds",
        flush=True
    )

    remaining_ms = context.get_remaining_time_in_millis()

    print(
        f"Remaining execution time: {remaining_ms} ms",
        flush=True
    )

    time.sleep(processing_seconds)

    print("Processing completed successfully", flush=True)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Processing completed",
            "processing_seconds": processing_seconds
        })
    }
