# Lab 11 — AWS Lambda Concurrency Throttling

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve AWS Lambda concurrency throttling using AWS CLI, Python, Linux Bash, IAM, and Amazon CloudWatch.

AWS Lambda automatically scales applications by running multiple execution environments when requests arrive simultaneously. However, concurrency settings and account-level quotas determine how many invocations can execute at the same time.

In production, insufficient concurrency can cause application requests to fail even when the Lambda function itself is healthy and its application code has no errors.

In this lab, we deploy a Python Lambda function that simulates customer order processing. Each invocation sleeps for six seconds to represent an application operation that takes time to complete.

We intentionally configure the function's reserved concurrency to **2**, then generate **12 approximately simultaneous synchronous invocations** using a Python load-test script that calls AWS CLI.

Because the function can execute at most two requests simultaneously, the additional requests may be rejected with `TooManyRequestsException`.

We investigate the failure using AWS CLI, Lambda concurrency configuration, CloudWatch Logs, and CloudWatch metrics including `Throttles`, `ConcurrentExecutions`, and `Invocations`.

After identifying the reserved concurrency limit as the root cause, we increase the setting to **12**.

We then repeat the same controlled workload to verify successful processing without changing the Lambda application code.

Finally, we remove the function's reserved concurrency setting and clean up the Lambda function, IAM execution role, and CloudWatch log group.

This lab represents a realistic production troubleshooting scenario involving application capacity, serverless scaling, throttling, and operational monitoring.

### Troubleshooting Workflow

```text
Create Lambda Execution Role
             |
             v
Configure CloudWatch Logs
             |
             v
Create Python Order Processor
             |
             v
Deploy Lambda Function
             |
             v
Verify Baseline Invocation
             |
             v
Set Reserved Concurrency = 2
             |
             v
Generate 12 Parallel Requests
             |
             v
Concurrency Limit Reached
             |
             v
Some Invocations Throttled
             |
             v
TooManyRequestsException
             |
             v
Investigate Invocation Results
             |
             v
Inspect CloudWatch Logs
             |
             v
Inspect Throttles Metric
             |
             v
Inspect ConcurrentExecutions
             |
             v
Identify Reserved Concurrency Limit
             |
             v
Increase Reserved Concurrency to 12
             |
             v
Repeat the Same Load Test
             |
             v
Verify Successful Invocations
             |
             v
Remove Reserved Concurrency
             |
             v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-011 |
| Lab Name | Lambda Concurrency Throttling |
| Difficulty | Intermediate |
| Primary Service | AWS Lambda |
| Supporting Services | IAM, Amazon CloudWatch |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Tools | AWS CLI v2, Bash, Python |
| Runtime | Python 3.13 |
| Architecture | x86_64 |
| Function Name | `lambda-lab11-concurrency` |
| Execution Role | `lambda-lab11-execution-role` |
| Lambda Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Function Timeout | 20 seconds |
| Workload Duration | 6 seconds per request |
| Total Load-Test Requests | 12 |
| Broken Reserved Concurrency | 2 |
| Recovery Reserved Concurrency | 12 |
| Invocation Type | Synchronous — RequestResponse |
| Error Type | `TooManyRequestsException` |
| HTTP Error Code | 429 |
| CloudWatch Metric | `Throttles` |
| Concurrency Metric | `ConcurrentExecutions` |
| Root Cause | Function-level concurrency restriction |
| Remediation | Increase reserved concurrency |
| Application Code Changes | None |
| VPC | Not required |
| NAT Gateway | Not required |
| RDS | Not required |
| Cleanup | Lambda, IAM, CloudWatch |

### Learning Objectives

- Understand AWS Lambda concurrency.
- Understand reserved concurrency.
- Distinguish reserved and provisioned concurrency.
- Reproduce synchronous invocation throttling.
- Understand `TooManyRequestsException`.
- Identify HTTP 429 responses.
- Run controlled concurrent workloads.
- Use Python ThreadPoolExecutor with AWS CLI.
- Disable automatic CLI retries during controlled tests.
- Inspect Lambda concurrency settings.
- Analyze CloudWatch `Throttles` metrics.
- Analyze `ConcurrentExecutions` and `Invocations`.
- Distinguish throttling from handler errors.
- Understand account concurrency quotas.
- Increase function concurrency safely.
- Compare broken and recovered workloads.
- Understand queueing and retry strategies.
- Practice production root cause analysis.
- Clean up AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company operates a serverless order-processing application using AWS Lambda.

The Lambda function processes customer orders and communicates with application services.

During normal traffic, the application operates correctly.

However, during a period of increased demand, customers begin receiving failed responses.

Some synchronous Lambda invocations are rejected with:

```text
TooManyRequestsException
Rate Exceeded
```

The Cloud Engineering team investigates the incident.

The engineer verifies that the Lambda function is deployed, Active, and capable of processing a single order successfully.

CloudWatch application logs show normal processing for accepted requests.

However, other requests have no corresponding handler logs.

The engineer inspects the Lambda concurrency configuration and discovers that reserved concurrency is configured to only two simultaneous executions.

When more than two requests arrive while both execution slots are occupied, Lambda can throttle the additional requests.

The engineer examines the CloudWatch `Throttles` and `ConcurrentExecutions` metrics and confirms that requests were rejected while the function-level concurrency limit was reached.

The engineer determines that the concurrency limit is insufficient for the application's traffic pattern.

The reserved concurrency setting is increased from 2 to 12, provided the AWS account has sufficient capacity.

The same workload is executed again.

The additional capacity allows the requests to complete successfully under the lab's expected conditions.

The engineer then reviews retry policies, queueing strategies, downstream service limits, and production concurrency planning.

### Incident Symptoms

- Lambda is Active.
- Individual requests succeed.
- Requests fail during traffic bursts.
- AWS CLI returns `TooManyRequestsException`.
- HTTP 429 errors occur.
- CloudWatch `Throttles` increases.
- `ConcurrentExecutions` reaches the configured cap.
- Some requests have no handler execution logs.
- Increasing concurrency improves capacity.

### Business Impact

Lambda throttling may cause:

- Customer order failures.
- API request errors.
- Failed synchronous integrations.
- Increased response latency.
- Delayed processing.
- Retry storms.
- Backlogs in event-driven applications.
- Reduced application availability.
- Additional operational work.

### Objective

Identify function-level concurrency throttling, restore sufficient concurrent execution capacity, and verify that the original workload completes without throttling.

---

## 3. AWS Architecture

### Broken Architecture

```text
                  12 Client Requests
                          |
                          v
                  Python Load Tester
                          |
                          v
                       AWS CLI
                          |
                          v
                    AWS Lambda
                          |
                          v
              Reserved Concurrency = 2
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Available Slots        Concurrency Full
              |                       |
              v                       v
        2 Executions            Other Requests
              |                       |
              v                       v
        Python Handler          Throttling
              |                       |
              v                       v
        Sleep 6 Seconds          HTTP 429
              |                       |
              v                       v
           SUCCESS          TooManyRequestsException
              |                       |
              +-----------+-----------+
                          |
                          v
                  CloudWatch Metrics
```

Illustrative result:

```text
12 requests
 2 successful
10 throttled
```

The exact counts can vary depending on request timing and environment behavior.

### Recovered Architecture

```text
                  12 Client Requests
                          |
                          v
                  Python Load Tester
                          |
                          v
                       AWS CLI
                          |
                          v
                    AWS Lambda
                          |
                          v
             Reserved Concurrency = 12
                          |
                          v
               Up to 12 Concurrent Slots
                          |
                          v
                 Lambda Execution
                          |
                          v
                 Python Order Handler
                          |
                          v
                 Process Each Request
                          |
                          v
                  statusCode: 200
                          |
                          v
                Successful Processing
                          |
                          v
                   CloudWatch Logs
```

### AWS Components

| Component | Purpose |
|---|---|
| AWS Lambda | Processes simulated order requests |
| Reserved Concurrency | Defines the function's concurrency allocation and ceiling |
| IAM Execution Role | Grants CloudWatch logging permissions |
| CloudWatch Logs | Records accepted invocations |
| CloudWatch Throttles | Records rejected invocation attempts |
| ConcurrentExecutions | Measures simultaneous active executions |
| Invocations | Measures function invocation activity |
| Python ThreadPoolExecutor | Launches concurrent AWS CLI commands |
| AWS CLI | Performs Lambda invocations |
| Linux Bash | Creates, deploys, and cleans resources |

---

## 4. Understanding Lambda Concurrency

### What Is Lambda Concurrency?

Lambda concurrency is the number of executions running simultaneously.

For example, if five requests are actively running, the function uses five concurrent execution slots.

### What Is Reserved Concurrency?

Reserved concurrency allocates a maximum number of concurrent executions to a specific Lambda function.

It also reserves that capacity from the account's shared unreserved concurrency pool.

Example:

```text
Reserved Concurrency = 2
```

The function can run a maximum of two concurrent executions.

### What Happens When Reserved Concurrency Is Reached?

Additional synchronous requests can be rejected with:

```text
TooManyRequestsException
```

The associated HTTP status is 429.

### What Is Provisioned Concurrency?

Provisioned concurrency maintains pre-initialized execution environments to reduce cold-start latency.

It is different from reserved concurrency.

### Reserved vs. Provisioned Concurrency

| Feature | Reserved | Provisioned |
|---|---|---|
| Guarantees concurrency allocation | Yes | Uses allocated capacity |
| Sets function concurrency ceiling | Yes | Not independently |
| Pre-initializes environments | No | Yes |
| Helps reduce cold starts | Not directly | Yes |
| Separate capacity charge | No | Yes |
| Primary purpose | Capacity control | Startup latency reduction |

### What Is an Account Concurrency Limit?

AWS Lambda applies concurrency quotas at the account and Region level.

Function-level reserved concurrency must fit within the account's quota.

AWS keeps 100 concurrency units available for functions without reserved concurrency.

### What Is TooManyRequestsException?

An AWS Lambda invocation error indicating that a request was throttled due to an applicable concurrency or request-rate limit.

### Do Throttled Invocations Execute the Handler?

No.

A request rejected by Lambda throttling does not reach the handler.

Therefore, it will not produce the application's `LAB11_START` and `LAB11_COMPLETE` log messages.

### Are Throttles Counted as Lambda Errors?

Not in the ordinary `Errors` metric.

The `Throttles` metric separately records throttled invocation requests.

### What Is ConcurrentExecutions?

A CloudWatch metric describing the number of simultaneously executing Lambda invocations.

Use the `Maximum` statistic to inspect peaks.

### Can Increasing Concurrency Overload Downstream Services?

Yes.

Increasing Lambda concurrency can also increase simultaneous requests to databases, third-party APIs, or internal services.

Production concurrency limits should consider downstream capacity.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- Bash.
- ZIP and unzip.
- IAM role management permissions.
- Lambda management permissions.
- CloudWatch Logs and metrics access.

### Relevant AWS Permissions

```text
sts:GetCallerIdentity

iam:CreateRole
iam:GetRole
iam:ListRoleTags
iam:AttachRolePolicy
iam:ListAttachedRolePolicies
iam:DetachRolePolicy
iam:DeleteRole
iam:PassRole

lambda:CreateFunction
lambda:GetFunction
lambda:GetFunctionConfiguration
lambda:InvokeFunction
lambda:GetFunctionConcurrency
lambda:PutFunctionConcurrency
lambda:DeleteFunctionConcurrency
lambda:GetAccountSettings
lambda:ListTags
lambda:DeleteFunction

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup

cloudwatch:GetMetricStatistics
```

### Safety Rules

- Use only the dedicated lab Lambda function.
- Do not run the test against production functions.
- Limit the workload to 12 requests.
- Limit each handler's processing time.
- Avoid repeated load tests without a reason.
- Do not modify concurrency reservations belonging to other applications.
- Check account concurrency availability before increasing reservations.
- Verify project ownership before cleanup.
- Remove reserved concurrency after testing.

### Cost Considerations

The lab uses short Lambda executions and CloudWatch logging.

No dedicated EC2, RDS, NAT Gateway, or VPC resources are created.

Reserved concurrency itself has no separate capacity reservation charge. Provisioned concurrency has different pricing.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 11-lambda-concurrency-throttling

cd 11-lambda-concurrency-throttling
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
zip -v

aws sts get-caller-identity
```

Install missing ZIP utilities:

```bash
sudo apt update
sudo apt install -y zip unzip
```

### Step 3 — Configure Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab11"

export FUNCTION_NAME="lambda-lab11-concurrency"

export ROLE_NAME="lambda-lab11-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export BROKEN_CONCURRENCY="2"
export RECOVERY_CONCURRENCY="12"

export TOTAL_REQUESTS="12"
export SLEEP_SECONDS="6"
```

### Step 4 — Save Configuration

```bash
cat > lab11-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export BROKEN_CONCURRENCY="$BROKEN_CONCURRENCY"
export RECOVERY_CONCURRENCY="$RECOVERY_CONCURRENCY"
export TOTAL_REQUESTS="$TOTAL_REQUESTS"
export SLEEP_SECONDS="$SLEEP_SECONDS"
EOF
```

Restore later:

```bash
source lab11-resources.env
```

### Step 5 — Check Existing Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected for a fresh lab: not found.

---

## 7. Verify AWS Account Concurrency Quotas

### Step 1 — Inspect Account Limits

```bash
aws lambda get-account-settings \
  --query 'AccountLimit.{Total:ConcurrentExecutions,Unreserved:UnreservedConcurrentExecutions}' \
  --output table \
  --region "$AWS_REGION"
```

A typical account may have a higher concurrency quota, but your actual quota can vary.

### Step 2 — Check Available Capacity

```bash
python3 - <<'PY'
import json
import subprocess

result = subprocess.check_output([
    "aws", "lambda", "get-account-settings",
    "--region", "us-east-1",
    "--output", "json"
])

limits = json.loads(result)["AccountLimit"]
unreserved = limits["UnreservedConcurrentExecutions"]

print("Unreserved concurrency:", unreserved)

if unreserved < 112:
    print("WARNING: Recovery reservation may exceed available capacity.")
else:
    print("PASS: Account appears to have enough concurrency.")
PY
```

The example check assumes that 12 units would be allocated from an unreserved pool before the lab's function reservation exists.

Once the function already reserves two units, increasing its reservation to 12 consumes only ten additional units.

The account must still maintain the required 100 unreserved units.

Do not change other Lambda functions' reservations to make this lab work.

---

## 8. Create Lambda Execution Role

### Step 1 — Create Trust Policy

Save as `lambda-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Step 2 — Create IAM Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Lambda concurrency troubleshooting Lab 11 execution role" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach CloudWatch Logging Policy

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 4 — Verify Role

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaBasicExecutionRole
```

---

## 9. Configure CloudWatch Logs

### Step 1 — Create Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Set Retention

```bash
aws logs put-retention-policy \
  --log-group-name "$LOG_GROUP" \
  --retention-in-days 7 \
  --region "$AWS_REGION"
```

### Step 3 — Verify

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query "logGroups[?logGroupName=='${LOG_GROUP}'].{Name:logGroupName,Retention:retentionInDays}" \
  --output table \
  --region "$AWS_REGION"
```

---

## 10. Create the Python Lambda Workload

### Step 1 — Create `lambda_function.py`

```python
import json
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_SLEEP_SECONDS = 8


def lambda_handler(event, context):
    request_id = event.get("request_id", "unknown")
    sleep_seconds = int(event.get("sleep_seconds", 6))

    if not 1 <= sleep_seconds <= MAX_SLEEP_SECONDS:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "sleep_seconds must be between 1 and 8"
            })
        }

    logger.info(
        "LAB11_START request=%s sleep=%s",
        request_id,
        sleep_seconds
    )

    start = time.monotonic()

    time.sleep(sleep_seconds)

    duration = round(time.monotonic() - start, 3)

    logger.info(
        "LAB11_COMPLETE request=%s duration=%s",
        request_id,
        duration
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Order processed successfully",
            "request_id": request_id,
            "duration_seconds": duration
        })
    }
```

### Step 2 — Understand the Sleep Workload

```python
time.sleep(sleep_seconds)
```

This simulates an application operation that takes six seconds.

Each active invocation continues consuming one concurrency unit while it sleeps.

### Step 3 — Understand Application Logs

```text
LAB11_START
LAB11_COMPLETE
```

These markers allow us to identify accepted requests.

Throttled requests never reach this logging code.

### Step 4 — Validate Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 5 — Create Deployment ZIP

```bash
zip function.zip lambda_function.py
```

Verify:

```bash
unzip -l function.zip
```

### Step 6 — Create Baseline Event

Save as `baseline-event.json`:

```json
{
  "request_id": "baseline-001",
  "sleep_seconds": 1
}
```

---

## 11. Deploy Lambda

### Step 1 — Create Function

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13 \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --memory-size 128 \
  --timeout 20 \
  --architectures x86_64 \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,Runtime:Runtime,Memory:MemorySize,Timeout:Timeout}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State: Active
Runtime: python3.13
Memory: 128
Timeout: 20
```

---

## 12. Verify Baseline Function Execution

### Step 1 — Invoke Baseline

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://baseline-event.json \
  --region "$AWS_REGION" \
  baseline-response.json \
  > lab11-baseline-invocation.json
```

### Step 2 — Inspect Response

```bash
python3 -m json.tool baseline-response.json
```

Expected structure:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Order processed successfully\", \"request_id\": \"baseline-001\", \"duration_seconds\": 1.0}"
}
```

The duration may vary.

### Step 3 — Verify Baseline

```bash
python3 - <<'PY'
import json

with open("baseline-response.json") as f:
    response = json.load(f)

body = json.loads(response["body"])

assert response["statusCode"] == 200
assert body["request_id"] == "baseline-001"

print("SUCCESS: Baseline invocation completed")
PY
```

The baseline confirms that the function works without heavy concurrent traffic.

---

## 13. Fault Injection — Limit Reserved Concurrency

### Step 1 — Set Reserved Concurrency to 2

```bash
aws lambda put-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --reserved-concurrent-executions "$BROKEN_CONCURRENCY" \
  --region "$AWS_REGION"
```

### Step 2 — Verify the Setting

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "ReservedConcurrentExecutions": 2
}
```

### Step 3 — Save Broken Configuration

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION" \
  > lab11-broken-concurrency.json
```

### Broken Configuration

```text
Function: lambda-lab11-concurrency

Reserved concurrency: 2

Incoming requests: 12

Handler duration: 6 seconds
```

The concurrency limit is intentionally too low for the burst.

---

<WritingBlock id="81127" variant="document">## 14. Create the Concurrent Load-Test Script

### Step 1 — Create `load_test.py`

The script uses Python's `ThreadPoolExecutor` to coordinate 12 concurrent AWS CLI invocations.

Each request invokes the same Lambda function and attempts to occupy an execution slot for six seconds.

The test is intentionally limited to a small, controlled number of requests.

```python
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

        with open(output_file) as file:
            response = json.load(file)

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

results.sort(key=lambda item: item["request_id"])

summary = {
    "mode": MODE,
    "total_requests": TOTAL_REQUESTS,
    "success": sum(
        result["result"] == "SUCCESS"
        for result in results
    ),
    "throttled": sum(
        result["result"] == "THROTTLED"
        for result in results
    ),
    "function_errors": sum(
        result["result"] == "FUNCTION_ERROR"
        for result in results
    ),
    "other_errors": sum(
        result["result"] in ("ERROR", "APPLICATION_ERROR")
        for result in results
    ),
    "results": results
}

summary_file = OUTPUT_DIR / "summary.json"
summary_file.write_text(
    json.dumps(summary, indent=2)
)

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
```

### Understanding the Load Test

The test uses:

```python
TOTAL_REQUESTS = 12
```

to limit the total number of invocations.

Each request contains:

```json
{
  "request_id": "broken-01",
  "sleep_seconds": 6
}
```

The script coordinates its workers through:

```python
threading.Barrier(TOTAL_REQUESTS)
```

This helps start the subprocesses at approximately the same time.

It does not guarantee that all requests reach the Lambda service at precisely the same instant.

### Why Disable Automatic Retries?

The script uses:

```python
environment["AWS_MAX_ATTEMPTS"] = "1"
```

This prevents automatic CLI retries from hiding the initial throttling behavior.

In production, bounded retries with exponential backoff and jitter are often appropriate. We disable them only for incident reproduction.

### Expected Output Files

```text
results-broken/
├── broken-01.json
├── broken-02.json
├── ...
└── summary.json
```

The recovered test creates:

```text
results-recovered/
├── recovered-01.json
├── recovered-02.json
├── ...
└── summary.json
```

Each `summary.json` records successful, throttled, and failed requests.

---

## 15. Reproduce Lambda Concurrency Throttling

### Step 1 — Run the Broken Load Test

```bash
python3 load_test.py broken
```

### Step 2 — Expected Output

An illustrative result:

```text
Lab 11 — BROKEN concurrency test
------------------------------------------------
broken-01: SUCCESS
broken-02: THROTTLED
broken-03: THROTTLED
broken-04: SUCCESS
broken-05: THROTTLED
broken-06: THROTTLED
broken-07: THROTTLED
broken-08: THROTTLED
broken-09: THROTTLED
broken-10: THROTTLED
broken-11: THROTTLED
broken-12: THROTTLED
------------------------------------------------
Total requests: 12
Successful: 2
Throttled: 10
Function errors: 0
Other errors: 0
```

The exact counts and which requests succeed may differ.

The key objective is to observe at least one genuine Lambda throttling error under a two-execution concurrency cap.

### Step 3 — Inspect Load-Test Summary

```bash
python3 -m json.tool results-broken/summary.json
```

Important fields:

```json
{
  "mode": "broken",
  "total_requests": 12,
  "success": 2,
  "throttled": 10
}
```

These values are illustrative.

### Step 4 — Verify Throttling

```bash
python3 - <<'PY'
import json

with open("results-broken/summary.json") as file:
    summary = json.load(file)

assert summary["total_requests"] == 12

assert summary["throttled"] > 0, (
    "No throttling observed. "
    "Check concurrency settings and request overlap."
)

assert summary["other_errors"] == 0
assert summary["function_errors"] == 0

print("SUCCESS: Lambda throttling reproduced")
print("Throttled requests:", summary["throttled"])
PY
```

### Step 5 — Inspect an Individual Throttling Error

```bash
python3 - <<'PY'
import json

with open("results-broken/summary.json") as file:
    summary = json.load(file)

for result in summary["results"]:
    if result["result"] == "THROTTLED":
        print("Request:", result["request_id"])
        print(result.get("error", "")[:600])
        break
PY
```

Expected error resembles:

```text
An error occurred (TooManyRequestsException)
when calling the Invoke operation:
Rate Exceeded
```

### Important Observation

The AWS service rejects throttled invocations before the Python handler begins.

Therefore, throttled requests do not produce:

```text
LAB11_START
LAB11_COMPLETE
```

Only accepted invocations produce application execution logs.

---

## 16. Investigate Lambda Concurrency Configuration

### Step 1 — Inspect Reserved Concurrency

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "ReservedConcurrentExecutions": 2
}
```

### Step 2 — Inspect Lambda State

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,Memory:MemorySize,Timeout:Timeout,LastUpdateStatus:LastUpdateStatus}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Timeout = 20
Memory = 128
```

The handler sleeps for six seconds.

The function's 20-second timeout is sufficient for this workload.

This helps distinguish concurrency throttling from an execution timeout.

### Step 3 — Check Account Concurrency

```bash
aws lambda get-account-settings \
  --query 'AccountLimit.{Total:ConcurrentExecutions,Unreserved:UnreservedConcurrentExecutions}' \
  --output json \
  --region "$AWS_REGION"
```

Lambda may throttle due to different limits.

For this lab, the known intentionally low reserved concurrency is the principal cause.

### Step 4 — Inspect CloudWatch Application Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
LAB11_START request=broken-...
LAB11_COMPLETE request=broken-...
```

The number of application executions should be smaller than the number of attempted requests when throttling occurs.

---

## 17. Investigate CloudWatch Metrics

### Important Metrics

| Metric | Purpose | Statistic |
|---|---|---|
| Throttles | Rejected invocation requests | Sum |
| ConcurrentExecutions | Active concurrent executions | Maximum |
| Invocations | Invocation activity | Sum |
| Errors | Execution errors | Sum |
| Duration | Execution duration | Average / percentiles |

Throttled invocation requests do not count as ordinary `Invocations` or function `Errors`.

### Step 1 — Define Observation Window

```bash
export START_TIME=$(date -u -d '20 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')

export END_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
```

### Step 2 — Inspect Throttles

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION"
```

Expected: a nonzero throttling datapoint after metric publication.

Example:

```json
{
  "Datapoints": [
    {
      "Sum": 10.0,
      "Unit": "Count"
    }
  ]
}
```

CloudWatch metric delivery can be delayed. The example value does not guarantee exactly ten throttled requests.

### Step 3 — Inspect ConcurrentExecutions

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Maximum \
  --output json \
  --region "$AWS_REGION"
```

With reserved concurrency set to 2, active execution concurrency cannot exceed that function-level cap.

### Step 4 — Inspect Invocations

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION"
```

The `Invocations` metric tracks invocations that reached execution, rather than requests rejected by Lambda throttling.

### Step 5 — Save Throttle Metric Evidence

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION" \
  > lab11-broken-throttles-metric.json
```

### Step 6 — Save Concurrency Metric Evidence

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Maximum \
  --output json \
  --region "$AWS_REGION" \
  > lab11-broken-concurrency-metric.json
```

### Investigation Findings

| Component | Expected Finding |
|---|---|
| Lambda state | Active |
| Baseline execution | Successful |
| Incoming load | 12 requests |
| Function duration | Approximately 6 seconds |
| Reserved concurrency | 2 |
| Invocation failure | TooManyRequestsException |
| Throttles metric | Nonzero |
| ConcurrentExecutions | At most 2 |
| Function errors | Not the primary cause |
| Root cause | Insufficient reserved concurrency |

---

## 18. Root Cause Analysis

### Root Cause

The Lambda function was configured with reserved concurrency of two executions.

The load test generated twelve approximately simultaneous invocation requests.

While two invocations were running, additional requests could not obtain execution capacity from the function's reserved concurrency allocation.

The Lambda service rejected those requests with throttling errors.

The application itself was healthy.

The failure occurred at the Lambda invocation capacity layer rather than inside the Python handler.

### Root Cause Diagram

```text
12 Concurrent Requests
          |
          v
    AWS Lambda Service
          |
          v
Check Reserved Concurrency
          |
          v
      Limit = 2
          |
    +-----+-----+
    |           |
    v           v
Slot Free    Limit Reached
    |           |
    v           v
Execute      Reject Request
    |           |
    v           v
Handler      HTTP 429
    |           |
    v           v
Success      TooManyRequestsException
```

### Five Whys

**Why 1 — Why did some requests fail?**

Lambda rejected them with TooManyRequestsException.

**Why 2 — Why did Lambda reject them?**

The available concurrency capacity was exhausted.

**Why 3 — Why was capacity exhausted?**

Reserved concurrency was configured to only two executions.

**Why 4 — Why was the configured limit insufficient?**

The workload sent twelve requests with overlapping execution durations.

**Why 5 — How can the problem be prevented?**

Right-size concurrency, monitor throttling, plan capacity around real traffic, and use controlled retries or buffering when appropriate.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-011 |
| Service | AWS Lambda |
| Error | TooManyRequestsException |
| HTTP Code | 429 |
| Workload | 12 requests |
| Configured Concurrency | 2 |
| Root Cause | Reserved concurrency too low |
| Remediation | Increase reserved concurrency |
| Recovery Configuration | 12 |
| Application Code Changes | None |
| IAM Changes | None |

---

## 19. Remediation — Increase Reserved Concurrency

### Step 1 — Confirm Available Account Capacity

```bash
aws lambda get-account-settings \
  --query 'AccountLimit.{Total:ConcurrentExecutions,Unreserved:UnreservedConcurrentExecutions}' \
  --output table \
  --region "$AWS_REGION"
```

Increasing reserved concurrency from 2 to 12 requires ten additional concurrency units.

The change must still preserve AWS's required unreserved concurrency capacity.

### Step 2 — Increase Reserved Concurrency

```bash
aws lambda put-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --reserved-concurrent-executions "$RECOVERY_CONCURRENCY" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Configuration

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "ReservedConcurrentExecutions": 12
}
```

### Step 4 — Save Recovered Configuration

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION" \
  > lab11-recovered-concurrency.json
```

### Before and After

| Setting | Broken | Recovered |
|---|---|---|
| Reserved concurrency | 2 | 12 |
| Test requests | 12 | 12 |
| Workload duration | 6 seconds | 6 seconds |
| Lambda timeout | 20 seconds | 20 seconds |
| Expected throttling | Yes | None |
| Application code | Unchanged | Unchanged |
| IAM role | Unchanged | Unchanged |

---

## 20. Verify Successful Recovery

### Step 1 — Repeat the Same Load Test

```bash
python3 load_test.py recovered
```

### Step 2 — Expected Output

```text
Lab 11 — RECOVERED concurrency test
------------------------------------------------
recovered-01: SUCCESS
recovered-02: SUCCESS
recovered-03: SUCCESS
...
recovered-12: SUCCESS
------------------------------------------------
Total requests: 12
Successful: 12
Throttled: 0
Function errors: 0
Other errors: 0
```

This is the intended result under sufficient account capacity and normal scaling behavior.

If throttling remains, inspect account-level quota usage, request-rate limits, function scaling behavior, and other concurrent traffic.

### Step 3 — Inspect Recovery Summary

```bash
python3 -m json.tool results-recovered/summary.json
```

### Step 4 — Verify Programmatically

```bash
python3 - <<'PY'
import json

with open("results-recovered/summary.json") as file:
    summary = json.load(file)

assert summary["total_requests"] == 12
assert summary["success"] == 12
assert summary["throttled"] == 0
assert summary["function_errors"] == 0
assert summary["other_errors"] == 0

print("SUCCESS: Lambda throttling resolved")
print("Successful requests:", summary["success"])
PY
```

### Step 5 — Inspect CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
LAB11_START request=recovered-...
LAB11_COMPLETE request=recovered-...
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB11_COMPLETE"' \
  --output json \
  --region "$AWS_REGION" \
  > lab11-recovered-cloudwatch-evidence.json
```

### Recovery Verification

| Check | Broken | Recovered |
|---|---|---|
| Lambda state | Active | Active |
| Reserved concurrency | 2 | 12 |
| Incoming requests | 12 | 12 |
| Throttling | Observed | None expected |
| Successful requests | Partial | All expected |
| FunctionError | Absent for accepted healthy executions | Absent |
| Application logs | Accepted requests only | Successful requests |
| Code changes | None | None |

**Recovery is verified when all twelve requests complete successfully after the reserved concurrency adjustment.**

---

<WritingBlock id="81128" variant="document">## 21. Production Troubleshooting Best Practices

### Standard Investigation Checklist

1. Identify the failing Lambda function.
2. Verify AWS account and Region.
3. Confirm the function is Active.
4. Test one normal invocation.
5. Reproduce the workload.
6. Inspect failed invocation responses.
7. Identify `TooManyRequestsException`.
8. Verify function reserved concurrency.
9. Check account-level concurrency limits.
10. Inspect `Throttles`.
11. Inspect `ConcurrentExecutions`.
12. Review `Invocations` and `Errors`.
13. Review application logs.
14. Determine whether requests failed before handler execution.
15. Identify the specific concurrency constraint.
16. Review downstream system capacity.
17. Apply a safe concurrency change.
18. Repeat the original test.
19. Verify successful execution.
20. Remove lab resources.

### Common Lambda Throttling Causes

| Problem | Possible Cause | Investigation |
|---|---|---|
| TooManyRequestsException | Function-level concurrency limit | GetFunctionConcurrency |
| Account concurrency exhausted | Regional quota reached | GetAccountSettings |
| Function reserved concurrency set to 0 | Execution intentionally disabled | GetFunctionConcurrency |
| High Throttles | Invocation requests rejected | CloudWatch Throttles |
| Unreserved pool exhausted | Other functions consuming shared capacity | Account concurrency metrics |
| API burst failures | Request-rate or scaling limitations | Lambda metrics |
| SQS backlog | Processing capacity constrained | Queue depth and event source mapping |
| Database overload after scaling | Too many connections | Database metrics |
| Third-party API throttling | Downstream service rate limit | Application logs and API response |

### Why Application Logs Can Be Misleading

A throttled request is rejected before the Lambda handler executes.

Therefore, CloudWatch application logs may show normal successful processing even when clients are receiving 429 errors.

Engineers should examine Lambda metrics and caller-side errors, not only handler logs.

---

## 22. Concurrency Capacity Planning

### Basic Formula

A useful average concurrency estimate is:

```text
Concurrency ≈ Requests per Second × Average Duration
```

For example:

```text
Requests per second: 20
Average duration: 0.5 seconds

Estimated average concurrency = 20 × 0.5 = 10
```

For the lab's workload:

```text
Requests: 12
Processing duration: 6 seconds
```

If all requests overlap, approximately twelve concurrent execution slots are needed.

### Important Limitations

Actual production capacity requirements also depend on:

- Burst traffic.
- Peak rather than average workload.
- High-percentile execution duration.
- AWS concurrency quotas.
- Function scaling behavior.
- Request-rate limits.
- Retry traffic.
- Downstream service capacity.

### Why Increasing Concurrency Can Be Risky

Increasing a Lambda function's concurrency from 2 to 12 also increases the number of simultaneous requests it may send to downstream systems.

For example, a database may not support a sudden increase in concurrent connections.

Concurrency settings should therefore be chosen based on complete application capacity.

---

## 23. Retry and Queueing Strategies

### Synchronous Invocation

Synchronous callers receive a throttling response when Lambda cannot accept a request.

Clients may use bounded exponential backoff and jitter for retryable failures.

Retries should have limits to prevent excessive load.

### Asynchronous Invocation

Lambda uses an internal asynchronous event queue and retry behavior.

The exact behavior depends on the error category and invocation configuration.

### Amazon SQS

SQS can buffer incoming work when traffic arrives faster than the application can process it.

Lambda can consume SQS messages at a controlled concurrency level.

This can be more appropriate than increasing concurrency indefinitely.

### RDS Proxy

For Lambda applications that connect to RDS, RDS Proxy may help manage connection pooling under high concurrency.

### Production Recommendations

- Monitor concurrency before failures occur.
- Create CloudWatch alarms for meaningful throttling thresholds.
- Use reserved concurrency thoughtfully.
- Consider downstream capacity.
- Use buffering when workloads permit asynchronous processing.
- Implement retry limits.
- Use jitter and exponential backoff.
- Avoid retry storms.
- Test expected traffic patterns before production deployments.

---

## 24. Cloud Security Engineering Considerations

### Availability

Concurrency throttling can affect service availability.

Security engineers should understand how resource exhaustion and capacity limitations influence application resilience.

### Reserved Concurrency as a Protective Control

Reserved concurrency can intentionally protect downstream services by limiting simultaneous Lambda executions.

For example, a database may only support a certain number of concurrent connections.

### Denial-of-Service Considerations

Uncontrolled traffic can consume execution capacity and increase operational costs.

Use appropriate API authorization, rate limiting, WAF controls where applicable, and monitoring.

### IAM Least Privilege

The Lambda handler only needs basic logging permissions.

No database, S3, or EC2 permissions are required for this lab.

### Monitoring and Alerting

Monitor:

```text
Throttles
ConcurrentExecutions
Invocations
Errors
Duration
```

Also monitor application-level failures and any downstream dependency metrics.

### Cost Control

Lambda costs depend partly on requests and execution resources.

Reserved concurrency does not have a separate capacity allocation charge, but traffic volume and execution duration can affect costs.

---

## 25. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 11.

### Step 1 — Verify Lambda Tags

```bash
aws lambda list-tags \
  --resource "$(aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --query Configuration.FunctionArn \
    --output text \
    --region "$AWS_REGION")" \
  --region "$AWS_REGION"
```

Confirm:

```text
Project = Lambda-Troubleshooting-Lab11
```

### Step 2 — Verify IAM Role Tags

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Remove Reserved Concurrency

```bash
aws lambda delete-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

This releases the function's reserved concurrency allocation.

### Step 4 — Verify Concurrency Removal

```bash
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected: no reserved concurrency allocation.

### Step 5 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 6 — Detach IAM Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 7 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 8 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 9 — Verify Lambda Deletion

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
ResourceNotFoundException
```

### Step 10 — Verify IAM Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 11 — Verify CloudWatch Cleanup

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query "logGroups[?logGroupName=='${LOG_GROUP}'].logGroupName" \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
[]
```

### Cleanup Summary

| Resource | Expected State |
|---|---|
| Reserved concurrency allocation | Removed |
| Lambda function | Deleted |
| IAM execution role | Deleted |
| IAM managed-policy attachment | Removed |
| CloudWatch log group | Deleted |
| EC2 | Not created |
| RDS | Not created |
| NAT Gateway | Not created |
| VPC | Not created |

---

## 26. Interview Questions and Answers

### Q1. What is AWS Lambda concurrency?

The number of Lambda executions running simultaneously.

### Q2. What is reserved concurrency?

A function-level setting that guarantees an allocation of concurrency and limits maximum simultaneous executions.

### Q3. What caused throttling in this lab?

Reserved concurrency was set to 2 while twelve approximately simultaneous requests were generated.

### Q4. What error indicates Lambda throttling?

`TooManyRequestsException`.

### Q5. What HTTP status corresponds to throttling?

HTTP 429.

### Q6. What is the CloudWatch Throttles metric?

It counts Lambda invocation requests rejected due to throttling.

### Q7. What does ConcurrentExecutions measure?

The number of simultaneous active Lambda executions.

### Q8. What is the difference between reserved and provisioned concurrency?

Reserved concurrency controls guaranteed and maximum capacity. Provisioned concurrency maintains pre-initialized execution environments.

### Q9. Why do throttled requests not appear in handler logs?

Because the Lambda service rejects them before running the handler.

### Q10. What is the difference between throttling and Lambda timeout?

Throttling occurs when invocation capacity is unavailable. A timeout occurs when a running invocation exceeds its execution time limit.

### Q11. Does reserved concurrency cost extra?

There is no separate charge for reserving concurrency, unlike provisioned concurrency.

### Q12. Can increasing concurrency create new problems?

Yes. It can increase load on databases, third-party APIs, and other downstream services.

### Q13. What is a retry storm?

A situation where many failed requests are retried aggressively, creating even more traffic and worsening the original incident.

### Q14. How can SQS help with throttling?

SQS can buffer work and allow consumers to process it at a controlled rate.

### Q15. How can you estimate concurrency?

Multiply average requests per second by average execution duration in seconds.

### Q16. What is the purpose of account-level concurrency quotas?

They limit the concurrency capacity that Lambda functions can consume within an AWS account and Region.

### Q17. What happens if reserved concurrency is set to zero?

The function cannot execute new invocations until the setting is changed or removed.

### Q18. Why disable automatic CLI retries in this lab?

To observe the initial throttling response directly rather than having the CLI automatically retry requests.

### Q19. What should you monitor after increasing concurrency?

Throttles, ConcurrentExecutions, Invocations, Errors, Duration, costs, and downstream service performance.

### Q20. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function that simulated customer order processing.

I intentionally configured reserved concurrency to two executions.

I created a Python load-test script that used AWS CLI to send twelve concurrent invocation requests.

Some requests failed with TooManyRequestsException because the function reached its concurrency limit.

I investigated AWS Lambda concurrency settings, the invocation results, CloudWatch Logs, Throttles, and ConcurrentExecutions.

I identified insufficient reserved concurrency as the root cause.

I increased the reserved concurrency allocation from two to twelve and repeated the same workload.

The recovery test verified that the requests could complete successfully under the updated capacity.

I also reviewed retry policies, SQS buffering, and the risks of overwhelming downstream services.

Finally, I removed the concurrency reservation and deleted the Lambda function, IAM role, and CloudWatch log group.

---

## 27. Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
│
├── 01-lambda-runtime-error/
├── 02-handler-not-found/
├── 03-lambda-timeout/
├── 04-missing-environment-variable/
├── 05-lambda-access-denied/
├── 06-lambda-no-internet-vpc/
├── 07-lambda-rds-connection-failure/
├── 08-lambda-memory-exhaustion/
├── 09-lambda-event-not-triggering/
├── 10-lambda-dependency-import-error/
│
├── 11-lambda-concurrency-throttling/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── baseline-event.json
│   ├── load_test.py
│   ├── function.zip
│   ├── lab11-resources.env
│   ├── lab11-baseline-invocation.json
│   ├── lab11-broken-concurrency.json
│   ├── lab11-recovered-concurrency.json
│   ├── lab11-broken-throttles-metric.json
│   ├── lab11-broken-concurrency-metric.json
│   ├── lab11-recovered-cloudwatch-evidence.json
│   ├── baseline-response.json
│   ├── results-broken/
│   └── results-recovered/
│
└── 12-lambda-async-retry-dlq-failure/
```

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Incident documentation and remediation |
| lambda_function.py | Simulated order-processing application |
| lambda-trust-policy.json | IAM execution-role trust policy |
| baseline-event.json | Single-invocation test |
| load_test.py | Controlled concurrent AWS CLI load test |
| function.zip | Generated Lambda deployment package |
| lab11-resources.env | Local AWS resource configuration |
| lab11-baseline-invocation.json | Baseline invocation metadata |
| lab11-broken-concurrency.json | Initial concurrency setting |
| lab11-recovered-concurrency.json | Updated concurrency setting |
| lab11-broken-throttles-metric.json | Throttling metric evidence |
| lab11-broken-concurrency-metric.json | Concurrency metric evidence |
| lab11-recovered-cloudwatch-evidence.json | Successful recovery logs |
| baseline-response.json | Baseline application response |
| results-broken/ | Broken-state request results |
| results-recovered/ | Recovered request results |

### Recommended Public GitHub Files

```text
11-lambda-concurrency-throttling/
├── README.md
├── lambda_function.py
├── lambda-trust-policy.json
├── baseline-event.json
└── load_test.py
```

Keep AWS-generated results, account-specific resource identifiers, and raw logs local unless reviewed and sanitized.

### Recommended Root .gitignore

Add the following to the root `.gitignore`:

```gitignore
# Lambda Lab 11
11-lambda-concurrency-throttling/function.zip
11-lambda-concurrency-throttling/lab11-resources.env
11-lambda-concurrency-throttling/lab11-*.json
11-lambda-concurrency-throttling/baseline-response.json
11-lambda-concurrency-throttling/results-broken/
11-lambda-concurrency-throttling/results-recovered/

# Python
__pycache__/
*.pyc
.venv/

# Secrets
.env
.env.*
*.pem
*.key
```

Files previously tracked by Git are not automatically removed from tracking by `.gitignore`.

---

## 28. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how insufficient AWS Lambda concurrency can cause application failures even when the function itself operates correctly.

We created a Python Lambda application that simulated order processing using a six-second execution delay.

We first verified that a normal invocation completed successfully.

Next, we intentionally configured reserved concurrency to two simultaneous executions.

We generated twelve approximately simultaneous requests using Python and AWS CLI.

Some requests were rejected with TooManyRequestsException because the function reached its configured concurrency limit.

We investigated the Lambda concurrency settings, CloudWatch Logs, Throttles, and ConcurrentExecutions.

The investigation identified insufficient reserved concurrency as the root cause.

We increased reserved concurrency from two to twelve and repeated the same workload.

Under sufficient account capacity, the requests completed without throttling.

We also reviewed how retry policies, queueing, account quotas, and downstream service limits affect production concurrency decisions.

Finally, we removed the reserved concurrency configuration and deleted the temporary AWS resources.

**Key Lesson:** A healthy Lambda function can still experience request failures when concurrency capacity is exhausted. Engineers must monitor service-level throttling and capacity metrics, not only application errors.

### Skills Demonstrated

- AWS Lambda
- Reserved concurrency
- Provisioned concurrency concepts
- Lambda scaling behavior
- AWS account concurrency quotas
- TooManyRequestsException
- HTTP 429 troubleshooting
- AWS CLI v2
- Linux Bash
- Python 3.13
- Python ThreadPoolExecutor
- Concurrent load testing
- AWS CLI retry configuration
- IAM execution roles
- CloudWatch Logs
- CloudWatch Throttles
- CloudWatch ConcurrentExecutions
- CloudWatch Invocations
- Capacity planning
- Root cause analysis
- Configuration remediation
- Recovery verification
- Cloud cost awareness
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-011 |
| Scenario | Lambda Concurrency Throttling |
| Function | lambda-lab11-concurrency |
| Runtime | Python 3.13 |
| Initial Reserved Concurrency | 2 |
| Recovery Reserved Concurrency | 12 |
| Test Requests | 12 |
| Simulated Duration | 6 seconds |
| Failure | TooManyRequestsException |
| HTTP Error | 429 |
| Root Cause | Insufficient concurrency |
| Remediation | Increase reserved concurrency |
| Recovery | No throttling under expected test conditions |
| Application Code Changes | None |
| Cleanup | Lambda, IAM, CloudWatch |
| Incident Status | Resolved after successful verification |

**Key Takeaway:** Production Lambda concurrency troubleshooting requires understanding function-level reservations, account quotas, CloudWatch throttling metrics, request patterns, and downstream system capacity.

---

## Official AWS Documentation

- [AWS Lambda — Configuring Reserved Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)
- [AWS Lambda — Understanding Concurrency and Scaling](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)
- [AWS Lambda — Monitoring Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-concurrency.html)
- [AWS Lambda — CloudWatch Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)
- [AWS Lambda — Invoke API](https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html)
- [AWS re:Post — Troubleshooting TooManyRequestsException](https://repost.aws/knowledge-center/lambda-troubleshoot-throttling)
- [AWS CLI — Put Function Concurrency](https://docs.aws.amazon.com/cli/latest/reference/lambda/put-function-concurrency.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)