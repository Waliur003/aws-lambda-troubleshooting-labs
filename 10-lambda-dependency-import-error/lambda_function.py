import json
import logging

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 10 started")

    target_url = "https://example.com/api/orders"

    logger.info("Preparing external API request")

    request = requests.Request(
        method="GET",
        url=target_url,
        params={
            "order_id": "ORDER-1001"
        }
    )

    prepared = request.prepare()

    logger.info("Python requests dependency loaded")
    logger.info("HTTP request prepared successfully")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Dependency imported successfully",
            "dependency": "requests",
            "requests_version": requests.__version__,
            "http_method": prepared.method,
            "url": prepared.url
        })
    }
