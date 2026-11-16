import concurrent.futures
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

FUNCTION_NAME = os.environ["FUNCTION_NAME"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

TOTAL_REQUESTS = 12
SLEEP_SECONDS = 6

if len(sys.argv) != 2 or sys.argv[1] not in ("broken", "recovered"):
    raise SystemExit(
        "Usage: python3 load_test.py broken|recovered"
    )

MODE = sys.argv[1]
OUTPUT_DIR = Path(f"results-{MODE}")
OUTPUT_DIR.mkdir(exist_ok=True)

barrier = threading.Barrier(TOTAL_REQUESTS)


def invoke_lambda(request_number):
    request_id = f"{MODE}-{request_number:02d}"

    payload = json.dumps({
        "request_id": request_id,
        "sleep_seconds": SLEEP_SECONDS
    })

    output_file = OUTPUT_DIR / f"{request_id}.json"

    command = [
        "aws", "lambda", "invoke",
        "--function-name", FUNCTION_NAME,
        "--invocation-type", "RequestResponse",
        "--cli-binary-format", "raw-in-base64-out",
        "--payload", payload,
        "--region", AWS_REGION,
        "--cli-connect-timeout", "10",
        "--cli-read-timeout", "25",
        "--output", "json",
        str(output_file)
    ]

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_RETRY_MODE"] = "standard"
    environment["AWS_MAX_ATTEMPTS"] = "1"

    # Release workers at approximately the same time.
    barrier.wait(timeout=30)

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=environment,
        timeout=40
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip()

        throttled = (
            "TooManyRequestsException" in stderr
            or "ThrottlingException" in stderr
        )

        return {
            "request_id": request_id,
            "result": "THROTTLED" if throttled else "ERROR",
            "cli_returncode": completed.returncode,
            "error": stderr[-1200:]
        }

    try:
        metadata = json.loads(completed.stdout)

        with open(output_file) as f:
            response = json.load(f)

        if metadata.get("FunctionError"):
            result = "FUNCTION_ERROR"
        elif response.get("statusCode") == 200:
            result = "SUCCESS"
        else:
            result = "APPLICATION_ERROR"

        return {
            "request_id": request_id,
            "result": result,
            "invoke_status": metadata.get("StatusCode"),
            "function_error": metadata.get("FunctionError"),
            "response": response
        }

    except (ValueError, OSError) as exc:
        return {
            "request_id": request_id,
            "result": "ERROR",
            "error": str(exc)
        }


with concurrent.futures.ThreadPoolExecutor(
    max_workers=TOTAL_REQUESTS
) as executor:
    futures = [
        executor.submit(invoke_lambda, number)
        for number in range(1, TOTAL_REQUESTS + 1)
    ]

    results = [
        future.result()
        for future in concurrent.futures.as_completed(futures)
    ]

results.sort(key=lambda x: x["request_id"])

summary = {
    "mode": MODE,
    "total_requests": TOTAL_REQUESTS,
    "success": sum(r["result"] == "SUCCESS" for r in results),
    "throttled": sum(r["result"] == "THROTTLED" for r in results),
    "function_errors": sum(
        r["result"] == "FUNCTION_ERROR" for r in results
    ),
    "other_errors": sum(
        r["result"] in ("ERROR", "APPLICATION_ERROR")
        for r in results
    ),
    "results": results
}

summary_file = OUTPUT_DIR / "summary.json"
summary_file.write_text(json.dumps(summary, indent=2))

print(f"\nLab 11 — {MODE.upper()} concurrency test")
print("-" * 48)

for result in results:
    print(
        f"{result['request_id']}: "
        f"{result['result']}"
    )

print("-" * 48)
print("Total requests:", summary["total_requests"])
print("Successful:", summary["success"])
print("Throttled:", summary["throttled"])
print("Function errors:", summary["function_errors"])
print("Other errors:", summary["other_errors"])
print("Saved:", summary_file)
