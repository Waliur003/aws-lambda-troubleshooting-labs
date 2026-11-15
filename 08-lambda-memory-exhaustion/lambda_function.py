import gc
import json
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CHUNK_MB = 8
MAX_ALLOCATE_MB = 240


def lambda_handler(event, context):
    requested_mb = int(event.get("allocate_mb", 240))

    if not 1 <= requested_mb <= MAX_ALLOCATE_MB:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "allocate_mb must be between 1 and 240"
            })
        }

    logger.info("Lambda Lab 08 started")
    logger.info("Requested allocation: %s MiB", requested_mb)

    blocks = []
    allocated_mb = 0

    while allocated_mb < requested_mb:
        current_mb = min(
            CHUNK_MB,
            requested_mb - allocated_mb
        )

        # Allocate and touch memory pages.
        block = bytearray(current_mb * 1024 * 1024)

        for position in range(0, len(block), 4096):
            block[position] = 1

        blocks.append(block)

        allocated_mb += current_mb

        logger.info(
            "Allocated approximately %s MiB",
            allocated_mb
        )

    # Keep blocks referenced until processing completes.
    checksum = sum(block[0] for block in blocks)

    time.sleep(0.2)

    logger.info("Memory workload completed successfully")

    result = {
        "allocated_mb": allocated_mb,
        "checksum": checksum
    }

    blocks.clear()
    gc.collect()

    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }
