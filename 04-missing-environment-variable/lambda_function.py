import json
import os


def lambda_handler(event, context):
    print("Lambda Lab 04 started")

    order_id = event.get("order_id", "ORDER-1001")

    print(f"Processing order: {order_id}")

    # Required application configuration
    app_env = os.environ["APP_ENV"]

    print(f"Application environment: {app_env}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Order processed successfully",
            "order_id": order_id,
            "environment": app_env
        })
    }
