import json
import os
import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):
    print("Lambda Lab 05 started", flush=True)

    bucket_name = os.environ["BUCKET_NAME"]

    object_key = event.get(
        "object_key",
        "orders/order-1001.json"
    )

    print(f"Reading S3 object: {object_key}", flush=True)

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key
    )

    content = response["Body"].read().decode("utf-8")

    order = json.loads(content)

    print(
        f"Successfully retrieved order: {order['order_id']}",
        flush=True
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Order retrieved successfully",
            "order_id": order["order_id"],
            "status": order["status"],
            "total": order["total"]
        })
    }
