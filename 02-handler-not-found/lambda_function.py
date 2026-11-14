import json


def lambda_handler(event, context):
    print("Lambda Lab 02 started")

    name = event.get("name", "Cloud Engineer")

    message = f"Hello, {name}! Lambda handler executed."

    print(message)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": message,
            "status": "success"
        })
    }
