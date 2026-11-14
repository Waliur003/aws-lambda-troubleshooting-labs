import json


def lambda_handler(event, context):
    print("Lambda Lab 01 started")

    number = event.get("number", 100)
    divisor = event.get("divisor", 2)

    print(f"Number: {number}")
    print(f"Divisor: {divisor}")

    if (
        not isinstance(number, (int, float))
        or isinstance(number, bool)
        or not isinstance(divisor, (int, float))
        or isinstance(divisor, bool)
    ):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Number and divisor must be numeric"
            })
        }

    if divisor == 0:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Divisor cannot be zero"
            })
        }

    result = number / divisor

    print(f"Calculated result: {result}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "result": result
        })
    }
