import json
import logging
import socket
import time
import urllib.error
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TARGET_URL = "https://example.com"


def lambda_handler(event, context):
    logger.info("Lambda Lab 06 started")
    logger.info("Testing outbound HTTPS connectivity")

    hostname = "example.com"

    try:
        ip = socket.gethostbyname(hostname)
        logger.info("DNS resolution succeeded for %s", hostname)
        logger.info("Resolved IP: %s", ip)
    except socket.gaierror as exc:
        logger.exception("DNS resolution failed")

        return {
            "statusCode": 503,
            "body": json.dumps({
                "network_status": "failed",
                "stage": "dns",
                "error": str(exc)
            })
        }

    start = time.monotonic()

    try:
        with urllib.request.urlopen(
            TARGET_URL,
            timeout=6
        ) as response:
            status = response.status
            response.read(256)

        elapsed = round(time.monotonic() - start, 3)

        logger.info("Outbound HTTPS request succeeded")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "network_status": "success",
                "http_status": status,
                "duration_seconds": elapsed
            })
        }

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError
    ) as exc:
        elapsed = round(time.monotonic() - start, 3)

        logger.exception("Outbound HTTPS request failed")

        return {
            "statusCode": 503,
            "body": json.dumps({
                "network_status": "failed",
                "stage": "https",
                "error_type": type(exc).__name__,
                "duration_seconds": elapsed
            })
        }
