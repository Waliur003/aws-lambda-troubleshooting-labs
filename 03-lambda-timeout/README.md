# Lab 03 — AWS Lambda Timeout

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda timeout using AWS CLI, Python, Linux Bash, Amazon CloudWatch Logs, and CloudWatch Metrics.

AWS Lambda runs application code for a configured amount of time. If a function does not complete within its timeout limit, Lambda terminates the execution.

In production environments, function timeouts can interrupt API requests, background processing, automated workflows, and integrations with external services.

In this lab, we deploy a Python Lambda function that simulates a six-second processing workload.

However, the function is initially configured with a three-second timeout.

The deployment succeeds, but the function terminates before completing its work.

We investigate the invocation response, CloudWatch execution logs, function configuration, and Lambda metrics.

After identifying the root cause, we increase the timeout to 10 seconds using AWS CLI.

We invoke the function again with the exact same six-second workload to verify that the configuration change resolves the failure.

We also test a faster one-second workload to demonstrate the difference between increasing the timeout and optimizing application execution time.

Finally, we remove the temporary Lambda, IAM, and CloudWatch resources.

### Troubleshooting Workflow

```text
Create Lambda Execution Role
           |
           v
Configure CloudWatch Logs
           |
           v
Create Python Lambda Function
           |
           v
Simulate 6-Second Workload
           |
           v
Configure 3-Second Timeout
           |
           v
Deploy Lambda
           |
           v
Invoke Function
           |
           v
Execution Timeout
           |
           v
Inspect Lambda Response
           |
           v
Investigate CloudWatch Logs
           |
           v
Analyze Duration and Errors
           |
           v
Identify Root Cause
           |
           v
Increase Timeout to 10 Seconds
           |
           v
Repeat Original Invocation
           |
           v
Verify Successful Execution
           |
           v
Test Faster Workload
           |
           v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-003 |
| Lab Name | AWS Lambda Timeout |
| Difficulty | Beginner to Intermediate |
| Primary AWS Service | AWS Lambda |
| Supporting Services | IAM, CloudWatch Logs, CloudWatch Metrics |
| Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Programming Language | Python |
| Runtime | Python 3.13 |
| Function | `lambda-lab03-timeout` |
| Handler | `lambda_function.lambda_handler` |
| Execution Role | `lambda-lab03-execution-role` |
| CloudWatch Log Group | `/aws/lambda/lambda-lab03-timeout` |
| Memory | 128 MB |
| Architecture | x86_64 |
| Broken Timeout | 3 seconds |
| Workload Duration | 6 seconds |
| Recovery Timeout | 10 seconds |
| Optimized Test | 1 second |
| Root Cause | Insufficient execution timeout |
| Remediation | Increase configured timeout |
| Verification | Repeat the same six-second workload |
| Cleanup | Lambda, IAM role, and CloudWatch log group |

### Lab Objectives

- Understand Lambda execution timeouts.
- Deploy a Python Lambda function using AWS CLI.
- Create a dedicated IAM execution role.
- Configure CloudWatch logging.
- Reproduce a function timeout.
- Inspect Lambda invocation errors.
- Understand `FunctionError`.
- Interpret CloudWatch REPORT entries.
- Investigate execution Duration and Errors metrics.
- Understand `context.get_remaining_time_in_millis()`.
- Distinguish Lambda timeout from AWS CLI read timeout.
- Modify Lambda timeout settings.
- Verify successful execution after remediation.
- Understand performance optimization versus timeout increases.
- Clean up temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company uses AWS Lambda to process background application tasks.

One Lambda function performs an operation that normally takes about six seconds.

The function is deployed with a timeout of only three seconds.

The deployment succeeds, and AWS reports that the function is Active.

However, when the application invokes the function, execution stops before the task completes.

The application does not receive its expected processing result.

CloudWatch Logs indicate that the Lambda execution exceeded its configured timeout.

The Cloud Engineer investigates the issue.

First, the engineer checks the function configuration and confirms that the timeout is set to three seconds.

Next, the engineer examines the application code and determines that the simulated workload requires six seconds.

The engineer then reviews CloudWatch Logs and execution-duration metrics.

The evidence shows that the function reaches its configured time limit before returning a result.

The root cause is an insufficient timeout configuration for the workload.

The engineer increases the timeout to 10 seconds and repeats the same invocation.

The function now completes successfully.

### Incident Symptoms

- Lambda function is Active.
- Deployment succeeds.
- Invocation starts successfully.
- Application logs indicate processing has begun.
- Function does not complete.
- Execution terminates near three seconds.
- CloudWatch reports a timeout.
- Function execution error is returned.
- Expected application result is missing.

### Business Impact

Lambda timeout incidents can cause:

- Failed application requests.
- Interrupted background processing.
- Incomplete event workflows.
- Delayed automated operations.
- Repeated asynchronous processing attempts.
- Increased function error rates.
- Unnecessary retries and duplicated work.
- Higher operational costs.

### Objective

Identify why the function exceeds its execution limit, correct the timeout configuration, and verify successful completion using the same original workload.

---

## 3. AWS Architecture

### Broken Architecture

```text
                  Cloud Engineer
                        |
                        v
                     AWS CLI
                        |
                        v
                   Lambda Invoke
                        |
                        v
                 lambda-lab03-timeout
                        |
                        v
                  Python 3.13
                        |
                        v
                   Lambda Handler
                        |
                        v
                    time.sleep(6)
                        |
                        v
                3 Seconds Elapse
                        |
                        v
               Timeout Limit Reached
                        |
                        v
             Lambda Terminates Execution
                        |
            +-----------+-----------+
            |                       |
            v                       v
      FunctionError            CloudWatch Logs
            |                       |
            v                       v
     Failed Invocation         Timeout Evidence
```

### Recovered Architecture

```text
                  Cloud Engineer
                        |
                        v
                     AWS CLI
                        |
                        v
                   Lambda Invoke
                        |
                        v
                 lambda-lab03-timeout
                        |
                        v
                  Python 3.13
                        |
                        v
                   Lambda Handler
                        |
                        v
                    time.sleep(6)
                        |
                        v
             Completes in About 6 Seconds
                        |
                        v
               Timeout Limit: 10 Seconds
                        |
                        v
               Application Result Returned
                        |
                        v
                 statusCode: 200
                        |
                        v
               Successful Execution
```

### Architecture Components

| Component | Purpose |
|---|---|
| AWS Lambda | Executes the Python workload |
| Lambda Handler | Processes the invocation event |
| Timeout Configuration | Limits maximum execution duration |
| Python `time.sleep()` | Simulates a slow operation |
| Lambda Context | Reports remaining execution time |
| IAM Execution Role | Provides CloudWatch logging permissions |
| CloudWatch Logs | Records timeout and execution information |
| CloudWatch Metrics | Measures Errors and Duration |
| AWS CLI | Deploys, invokes, and configures Lambda |
| Bash | Coordinates lab commands |

---

## 4. Understanding Lambda Timeouts

### What Is a Lambda Timeout?

A Lambda timeout is the maximum amount of time the function is allowed to execute.

When this limit is exceeded, AWS Lambda terminates the execution.

### What Is the Default Timeout?

The standard Lambda function timeout defaults to three seconds.

### What Is the Maximum Timeout?

For the conventional Lambda ZIP-based function used in this lab, the timeout can be configured from 1 to 900 seconds, or 15 minutes.

Some newer Lambda execution types have different limits.

### What Happens When a Function Times Out?

The function stops before completing its work.

For a synchronous invocation, the Lambda service can return an execution error indicating a timeout.

CloudWatch Logs can contain a timeout message or a REPORT record showing timeout status.

### What Is the Duration Metric?

CloudWatch `Duration` measures function execution time in milliseconds.

Example:

```text
3 seconds ≈ 3,000 milliseconds
6 seconds ≈ 6,000 milliseconds
```

### What Is the Errors Metric?

The `Errors` metric counts function invocations that result in an error.

Timeouts contribute to execution failures.

### What Is the REPORT Log Entry?

Lambda REPORT records provide execution information such as:

```text
Duration
Billed Duration
Memory Size
Max Memory Used
Status
```

The exact fields depend on the runtime and logging format.

### What Is `get_remaining_time_in_millis()`?

The Lambda context object provides a method that returns the approximate remaining execution time.

Example:

```python
remaining = context.get_remaining_time_in_millis()
```

Applications can use this value to manage long-running operations.

### Lambda Timeout vs. AWS CLI Read Timeout

| Setting | Purpose |
|---|---|
| Lambda `Timeout` | Maximum server-side function execution time |
| AWS CLI `--cli-read-timeout` | Maximum time the client waits while reading a response |

Increasing the AWS CLI read timeout does not change the Lambda function timeout.

### Does Increasing Timeout Make Code Faster?

No.

Increasing the timeout allows a function to run for longer.

Improving application performance requires optimizing processing logic, downstream calls, resource allocation, or architecture.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- ZIP and unzip utilities.
- AWS IAM permissions.
- Lambda permissions.
- CloudWatch Logs access.
- CloudWatch Metrics access.

### Required AWS Permissions

```text
sts:GetCallerIdentity

iam:CreateRole
iam:GetRole
iam:AttachRolePolicy
iam:ListAttachedRolePolicies
iam:ListRoleTags
iam:DetachRolePolicy
iam:DeleteRole
iam:PassRole

lambda:CreateFunction
lambda:GetFunction
lambda:GetFunctionConfiguration
lambda:InvokeFunction
lambda:UpdateFunctionConfiguration
lambda:DeleteFunction
lambda:ListTags

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup

cloudwatch:GetMetricStatistics
```

### Safety Rules

- Use a dedicated lab Lambda function.
- Do not modify production functions.
- Use a dedicated execution role.
- Limit test invocations.
- Keep CloudWatch log retention short.
- Do not publish account-specific evidence.
- Verify project tags before cleanup.
- Do not change shared AWS resources.

### Cost Considerations

This lab uses a small Lambda function with short invocations.

Potential costs include Lambda requests, execution duration, and CloudWatch Logs.

No EC2 instances, NAT Gateways, RDS databases, or S3 buckets are required.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 03-lambda-timeout

cd 03-lambda-timeout
```

### Step 2 — Verify Installed Tools

```bash
aws --version
python3 --version
zip -v
```

Install ZIP if necessary:

```bash
sudo apt update
sudo apt install -y zip unzip
```

### Step 3 — Verify AWS Identity

```bash
aws sts get-caller-identity
```

### Step 4 — Configure Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab03"

export FUNCTION_NAME="lambda-lab03-timeout"

export ROLE_NAME="lambda-lab03-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export RUNTIME="python3.13"

export BROKEN_TIMEOUT=3

export RECOVERY_TIMEOUT=10
```

### Step 5 — Verify Variables

```bash
echo "$AWS_REGION"
echo "$FUNCTION_NAME"
echo "$ROLE_NAME"
echo "$BROKEN_TIMEOUT"
echo "$RECOVERY_TIMEOUT"
```

### Step 6 — Save Resource Identifiers

```bash
cat > lab03-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export RUNTIME="$RUNTIME"
export BROKEN_TIMEOUT="$BROKEN_TIMEOUT"
export RECOVERY_TIMEOUT="$RECOVERY_TIMEOUT"
EOF
```

Restore the environment using:

```bash
source lab03-resources.env
```

### Step 7 — Check Existing Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

For a new lab, these commands should report that the resources do not exist.

If a resource already exists, verify ownership before modifying it.

---

## 7. Create the Lambda Execution Role

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

### Step 2 — Verify Trust Policy

```bash
python3 -m json.tool lambda-trust-policy.json
```

### Step 3 — Create IAM Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Execution role for Lambda timeout troubleshooting Lab 03" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 4 — Attach CloudWatch Logging Permissions

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 5 — Verify Role

```bash
aws iam get-role \
  --role-name "$ROLE_NAME" \
  --query 'Role.{Name:RoleName,Arn:Arn}' \
  --output json
```

### Step 6 — Verify Attached Policy

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

## 8. Configure CloudWatch Logs

### Step 1 — Create Dedicated Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Configure Retention

```bash
aws logs put-retention-policy \
  --log-group-name "$LOG_GROUP" \
  --retention-in-days 7 \
  --region "$AWS_REGION"
```

### Step 3 — Verify Configuration

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query 'logGroups[].{Name:logGroupName,Retention:retentionInDays}' \
  --output table \
  --region "$AWS_REGION"
```

Expected retention:

```text
7 days
```

---

## 9. Create the Python Lambda Function

### Step 1 — Create `lambda_function.py`

```python
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
```

### Step 2 — Understand the Code

The function reads the requested processing duration:

```python
processing_seconds = event.get("processing_seconds", 6)
```

It then simulates work:

```python
time.sleep(processing_seconds)
```

During the broken deployment, the workload requires six seconds, but the function has only three seconds available.

The function also reports its remaining execution time:

```python
context.get_remaining_time_in_millis()
```

### Step 3 — Verify Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 4 — Package the Function

```bash
zip function.zip lambda_function.py
```

### Step 5 — Inspect the ZIP

```bash
unzip -l function.zip
```

Expected:

```text
lambda_function.py
```

### Step 6 — Create the Slow Test Event

Save as `slow-event.json`:

```json
{
  "processing_seconds": 6
}
```

This test event will be used before and after remediation.

---

## 10. Deploy Lambda with the Broken Timeout

### Step 1 — Create Lambda Function

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout "$BROKEN_TIMEOUT" \
  --memory-size 128 \
  --architectures x86_64 \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

The broken configuration is:

```text
Timeout = 3 seconds
```

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,Runtime:Runtime,Handler:Handler,State:State,Timeout:Timeout,Memory:MemorySize}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Timeout = 3
Memory = 128
```

### Step 4 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab03-broken-configuration.json
```

### Deployment Finding

The function is active, but its timeout configuration is too short for the six-second processing operation.

---

<WritingBlock id="63722" variant="document">## 11. Fault Injection — Reproduce Lambda Timeout

### Step 1 — Invoke the Broken Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://slow-event.json \
  --log-type Tail \
  --cli-read-timeout 30 \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab03-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab03-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

The full response may include additional metadata.

### Why Is StatusCode 200?

For synchronous Lambda invocation, StatusCode 200 indicates that the Invoke API request succeeded.

It does not guarantee that the application code completed successfully.

Execution errors are reported separately through `FunctionError` and the response payload.

### Step 3 — Inspect the Error Payload

```bash
python3 -m json.tool broken-response.json
```

Expected error message resembles:

```text
Task timed out after 3.00 seconds
```

The exact error type and payload format can vary by runtime.

### Step 4 — Verify the Failure Programmatically

```bash
python3 - <<'PY'
import json

with open("lab03-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    response = json.load(file)

assert invocation.get("StatusCode") == 200
assert invocation.get("FunctionError") is not None

print("FunctionError:", invocation["FunctionError"])
print("Error type:", response.get("errorType"))
print("Error message:", response.get("errorMessage"))

message = str(
    response.get("errorMessage", "")
).lower()

assert (
    "timed out" in message
    or "timeout" in message
)

print("SUCCESS: Lambda timeout reproduced")
PY
```

If the assertion fails, inspect the actual payload and CloudWatch logs before declaring the test successful.

### Step 5 — Decode Invocation Logs

```bash
python3 - <<'PY'
import base64
import json

with open("lab03-broken-invocation.json") as file:
    invocation = json.load(file)

encoded = invocation.get("LogResult")

if encoded:
    print(
        base64.b64decode(encoded).decode(
            "utf-8",
            errors="replace"
        )
    )
else:
    print("No inline log excerpt returned")
PY
```

Expected application logs:

```text
Lambda Lab 03 started
Requested processing time: 6 seconds
Remaining execution time: ...
```

The timed-out invocation should not reach:

```text
Processing completed successfully
```

### Broken-State Verification

| Component | Expected |
|---|---|
| Lambda deployment | Successful |
| Function state | Active |
| Timeout | 3 seconds |
| Requested workload | 6 seconds |
| Handler starts | Yes |
| Workload completes | No |
| FunctionError | Present |
| Timeout evidence | Present |
| Successful result | Absent |

---

## 12. Investigate CloudWatch Logs

### Step 1 — Read Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected log structure resembles:

```text
START RequestId: ...
Lambda Lab 03 started
Requested processing time: 6 seconds
Remaining execution time: ...
Task timed out after 3.00 seconds
REPORT RequestId: ... Duration: ... Status: timeout
```

The exact log format may vary by Lambda runtime and logging configuration.

### Step 2 — Search Timeout Messages

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Task timed out"' \
  --query 'events[].{Timestamp:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

If no matching events are returned, inspect the complete logs. Newer runtimes may report timeout status using different log formatting.

### Step 3 — Search REPORT Records

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"REPORT RequestId"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Understanding REPORT Fields

| Field | Purpose |
|---|---|
| RequestId | Identifies invocation |
| Duration | Execution duration |
| Billed Duration | Billing duration |
| Memory Size | Configured memory |
| Max Memory Used | Reported peak memory |
| Status | Execution outcome, when present |

### Step 4 — Inspect Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Timeout:Timeout,Memory:MemorySize,State:State}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "Timeout": 3,
  "Memory": 128,
  "State": "Active"
}
```

### Step 5 — Save CloudWatch Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab03-broken-cloudwatch-evidence.json
```

### Investigation Finding

The function begins execution but reaches the three-second timeout before its six-second operation finishes.

The CloudWatch logs and configuration establish the failure cause.

---

## 13. Investigate CloudWatch Metrics

### Important Metrics

| Metric | Investigation |
|---|---|
| Invocations | Confirms function activity |
| Errors | Detects failed executions |
| Duration | Measures execution time |
| Throttles | Checks for concurrency rejection |

### Step 1 — Configure Metric Time Window

```bash
export METRIC_START="$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)"

export METRIC_END="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### Step 2 — Inspect Errors Metric

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$METRIC_START" \
  --end-time "$METRIC_END" \
  --period 60 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --output json
```

### Step 3 — Inspect Duration Metric

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$METRIC_START" \
  --end-time "$METRIC_END" \
  --period 60 \
  --statistics Average Maximum \
  --region "$AWS_REGION" \
  --output json
```

Duration is measured in milliseconds.

The timed-out invocation should have execution duration near the configured timeout.

### Step 4 — Inspect Throttles Metric

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$METRIC_START" \
  --end-time "$METRIC_END" \
  --period 60 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --output json
```

Concurrency throttling is not expected in this single-request experiment.

### Metric Interpretation

| Observation | Possible Meaning |
|---|---|
| Errors increased | Function failure occurred |
| Duration near timeout | Function reached execution limit |
| Throttles absent | No observed concurrency rejection |
| Empty Datapoints | Metrics may not yet be available |

CloudWatch metric publication is asynchronous.

Do not interpret empty metric results as proof that no invocations occurred.

---

## 14. Root Cause Analysis

### Root Cause

The Lambda function was configured with a three-second timeout while its application workload required six seconds.

The relevant application code was:

```python
time.sleep(processing_seconds)
```

The event specified:

```json
{
  "processing_seconds": 6
}
```

But the Lambda configuration specified:

```text
Timeout = 3 seconds
```

The execution therefore reached its configured time limit before processing completed.

### Root Cause Diagram

```text
Lambda Invoked
      |
      v
Processing Starts
      |
      v
time.sleep(6)
      |
      v
3 Seconds Elapse
      |
      v
Configured Timeout Reached
      |
      v
Lambda Terminates Execution
      |
      v
Function Error
      |
      v
CloudWatch Timeout Evidence
```

### Five Whys

**Why 1 — Why did Lambda fail?**

The function exceeded its configured timeout.

**Why 2 — Why did execution exceed the timeout?**

The workload required six seconds.

**Why 3 — Why was the function allowed only three seconds?**

Its timeout configuration was set to three seconds.

**Why 4 — Why did the function not return the processing result?**

Lambda terminated execution before the sleep operation completed.

**Why 5 — How can the problem be prevented?**

Set an appropriate timeout based on actual workload measurements and optimize unexpectedly slow operations.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-003 |
| Service | AWS Lambda |
| Runtime | Python 3.13 |
| Workload | Six-second processing |
| Broken Timeout | Three seconds |
| Error | Execution timeout |
| Root Cause | Timeout shorter than required duration |
| Remediation | Increase timeout to 10 seconds |
| Code Redeployment | Not required |
| Verification | Repeat same workload |

### Production Consideration

Increasing the timeout is appropriate for this controlled experiment.

In a real application, engineers should investigate why execution is slow before simply increasing the limit.

Potential causes include:

- Slow database queries.
- External API latency.
- Missing network connectivity.
- DNS problems.
- CPU-intensive code.
- Inefficient algorithms.
- Large payloads.
- Blocking operations.
- Unexpected retry loops.

---

## 15. Remediation — Increase Lambda Timeout

### Step 1 — Update Function Timeout

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --timeout "$RECOVERY_TIMEOUT" \
  --region "$AWS_REGION"
```

The new timeout is:

```text
10 seconds
```

### Step 2 — Wait for Update Completion

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Updated Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Function:FunctionName,Timeout:Timeout,State:State,LastUpdateStatus:LastUpdateStatus,Memory:MemorySize}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Timeout = 10
State = Active
LastUpdateStatus = Successful
```

### Step 4 — Save Recovered Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab03-recovered-configuration.json
```

### Configuration Comparison

| Setting | Broken | Recovered |
|---|---|---|
| Runtime | Python 3.13 | Python 3.13 |
| Timeout | 3 seconds | 10 seconds |
| Memory | 128 MB | 128 MB |
| Handler | Same | Same |
| Workload | 6 seconds | 6 seconds |
| Deployment ZIP | Unchanged | Unchanged |
| Expected Result | Timeout | Successful |

The function configuration was corrected without changing or redeploying the application code.

---

## 16. Verify Successful Recovery

### Step 1 — Invoke the Same Six-Second Workload

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://slow-event.json \
  --cli-read-timeout 30 \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab03-healthy-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab03-healthy-invocation.json
```

Expected:

```json
{
  "StatusCode": 200
}
```

There should be no `FunctionError`.

### Step 3 — Inspect Application Response

```bash
python3 -m json.tool healthy-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Processing completed\", \"processing_seconds\": 6}"
}
```

### Step 4 — Verify Recovery with Python

```bash
python3 - <<'PY'
import json

with open("lab03-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["message"] == "Processing completed"
assert body["processing_seconds"] == 6

print("SUCCESS: Lambda timeout resolved")
PY
```

Expected:

```text
SUCCESS: Lambda timeout resolved
```

### Step 5 — Verify CloudWatch Recovery Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Processing completed successfully
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Processing completed successfully"' \
  --output json \
  --region "$AWS_REGION" \
  > lab03-recovery-cloudwatch-evidence.json
```

### Recovery Verification

| Check | Expected |
|---|---|
| Lambda timeout | 10 seconds |
| Workload | 6 seconds |
| Invoke API | StatusCode 200 |
| FunctionError | Absent |
| Application statusCode | 200 |
| Processing result | Completed |
| CloudWatch success log | Present |
| Incident | Resolved |

**Recovery is verified when the original six-second workload completes successfully without a Lambda execution error.**

---

<WritingBlock id="63723" variant="document">## 17. Additional Performance Optimization Test

### Purpose

Increasing Lambda timeout allows more execution time.

It does not automatically make a workload faster.

This extra test uses the same function with a shorter processing duration.

### Step 1 — Create Fast Test Event

Save as `fast-event.json`:

```json
{
  "processing_seconds": 1
}
```

### Step 2 — Invoke the Fast Workload

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://fast-event.json \
  --region "$AWS_REGION" \
  fast-response.json \
  > lab03-fast-invocation.json
```

### Step 3 — Inspect the Response

```bash
python3 -m json.tool fast-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Processing completed\", \"processing_seconds\": 1}"
}
```

### Step 4 — Verify Programmatically

```bash
python3 - <<'PY'
import json

with open("lab03-fast-invocation.json") as file:
    invocation = json.load(file)

with open("fast-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["processing_seconds"] == 1

print("SUCCESS: Fast workload completed")
PY
```

### Performance Comparison

| Observation | Broken | Recovered | Fast Test |
|---|---|---|---|
| Timeout | 3 sec | 10 sec | 10 sec |
| Workload | 6 sec | 6 sec | 1 sec |
| FunctionError | Present | Absent | Absent |
| Task Completed | No | Yes | Yes |
| Approximate Duration | 3 sec | 6 sec | 1 sec |
| Result | Timeout | Success | Success |

### Production Lesson

Timeout configuration and application performance are different concerns.

A production solution may involve increasing the timeout, optimizing code, adding caching, improving database queries, or changing how a workload is processed.

The appropriate solution depends on the root cause and business requirements.

---

## 18. Production Troubleshooting Best Practices

### Standard Investigation Checklist

1. Identify the affected Lambda function.
2. Verify the AWS account and Region.
3. Inspect the function configuration.
4. Confirm the timeout setting.
5. Reproduce the issue using a known event.
6. Inspect the Invoke API response.
7. Examine the function error payload.
8. Read CloudWatch Logs.
9. Find timeout messages and REPORT records.
10. Review the Duration metric.
11. Review the Errors metric.
12. Check whether throttling occurred.
13. Investigate application processing time.
14. Identify slow downstream dependencies.
15. Determine the root cause.
16. Apply targeted remediation.
17. Wait for the configuration update.
18. Repeat the original workload.
19. Verify successful completion.
20. Preserve evidence and clean up.

### Production Investigation Flow

```text
Lambda Execution Failure
           |
           v
Inspect Function Configuration
           |
           v
Check Timeout Setting
           |
           v
Review CloudWatch Logs
           |
           v
Inspect REPORT Duration
           |
           v
Check Errors Metric
           |
           v
Investigate Application Workload
           |
           v
Identify Root Cause
           |
           v
Optimize or Adjust Timeout
           |
           v
Repeat Invocation
           |
           v
Verify Successful Execution
```

### Common Causes of Lambda Timeouts

| Cause | Symptom | Troubleshooting |
|---|---|---|
| Timeout too short | Execution ends at configured limit | Check Timeout |
| Slow external API | HTTP request waits too long | Check network latency |
| Database query delay | Slow database response | Review RDS/query performance |
| VPC internet problem | Outbound call hangs | Check NAT and routes |
| DNS resolution failure | Hostname lookup delays | Inspect DNS/networking |
| CPU-intensive code | High execution duration | Optimize code or memory |
| Infinite loop | Repeated work until timeout | Inspect application logic |
| Large payload | Slow processing | Review data size |
| Blocking operation | Function waits unexpectedly | Trace blocking calls |

### Production Recommendations

- Use realistic timeout values.
- Measure actual execution duration.
- Keep a reasonable safety margin.
- Investigate downstream dependencies.
- Set timeouts on external HTTP and database clients.
- Validate incoming event values.
- Monitor Duration, Errors, and Throttles.
- Configure appropriate CloudWatch alarms.
- Avoid unnecessary retries.
- Consider asynchronous processing for longer workflows.
- Use idempotent operations when retries are possible.
- Test configuration changes before production deployment.

### Security Considerations

Lambda timeouts are usually reliability or performance problems.

However, inefficient code or unexpected input can be abused to exhaust resources.

Validate inputs, control workload sizes, restrict permissions, and monitor unexpected execution patterns.

Avoid logging credentials, tokens, or sensitive application payloads.

---

## 19. AWS Resource Cleanup

**Warning:** Delete only the resources created for Lab 03.

### Step 1 — Verify Lambda Ownership

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
Project = Lambda-Troubleshooting-Lab03
```

### Step 2 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Verify Log Group Name

```bash
echo "$LOG_GROUP"
```

Expected:

```text
/aws/lambda/lambda-lab03-timeout
```

### Step 4 — Delete Lambda Function

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 5 — Detach IAM Logging Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 6 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 7 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 8 — Verify Lambda Deletion

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
ResourceNotFoundException
```

### Step 9 — Verify IAM Role Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 10 — Verify Log Group Deletion

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
| Lambda function | Deleted |
| Dedicated IAM execution role | Deleted |
| IAM policy attachment | Removed |
| CloudWatch log group | Deleted |
| EC2 instances | None created |
| VPC | None created |
| RDS | None created |
| NAT Gateway | None created |
| S3 bucket | None created |

---

## 20. Interview Questions and Answers

### Q1. What is an AWS Lambda timeout?

A timeout occurs when Lambda execution exceeds the configured maximum duration.

### Q2. What is Lambda's default timeout?

Three seconds for the standard Lambda configuration used in this lab.

### Q3. What is the maximum conventional Lambda timeout?

900 seconds, or 15 minutes.

### Q4. How do you troubleshoot a Lambda timeout?

Inspect function configuration, CloudWatch logs, execution duration, application logic, and downstream dependencies.

### Q5. What does the Duration metric measure?

The execution duration of Lambda invocations in milliseconds.

### Q6. What is the difference between Lambda timeout and CLI read timeout?

Lambda timeout limits function execution. CLI read timeout controls how long the client waits for a response.

### Q7. Does increasing timeout improve performance?

No. It allows the function more time to complete.

### Q8. Can insufficient memory contribute to timeouts?

Yes. Lambda CPU capacity scales with configured memory, so CPU-intensive code may run more slowly with lower memory allocation.

### Q9. What is `get_remaining_time_in_millis()`?

A Lambda context method that reports the approximate remaining execution time.

### Q10. How do you update the timeout using AWS CLI?

```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --timeout 10 \
  --region us-east-1
```

### Q11. Why should you inspect CloudWatch REPORT records?

They provide execution duration, memory information, and sometimes the final execution status.

### Q12. Do timeouts count as Lambda execution errors?

Yes. Timed-out invocations are unsuccessful executions and can contribute to the Errors metric.

### Q13. What does FunctionError indicate?

It indicates that an error occurred during Lambda execution.

### Q14. Why might StatusCode 200 appear with a timeout?

The synchronous Invoke API request succeeded, while the function itself failed.

### Q15. How do you verify that increasing the timeout resolved the incident?

Invoke the exact original workload and confirm that the function completes without a FunctionError.

### Q16. Would increasing memory always fix a timeout?

No. It may help CPU-bound workloads but will not necessarily resolve slow external services, broken networking, or blocking operations.

### Q17. What should you check if Lambda times out while accessing an external API?

Check DNS resolution, VPC routing, NAT connectivity, security groups, external service latency, and HTTP client timeout settings.

### Q18. Why should application code have its own network timeouts?

To avoid consuming the entire Lambda execution window while waiting indefinitely for a dependency.

### Q19. How can you prevent future timeout incidents?

Use realistic configuration, monitoring, performance testing, client timeouts, and appropriate workload architecture.

### Q20. How would you explain this lab in an interview?

I deployed a Python Lambda function that simulated a six-second processing task.

I intentionally configured the function with a three-second timeout.

The deployment succeeded, but the function timed out when invoked.

I investigated the invocation response, CloudWatch logs, REPORT entries, and execution metrics.

The logs showed that Lambda reached its execution limit before completing the workload.

I identified the root cause as a timeout configuration shorter than the processing duration.

I changed the timeout to 10 seconds using AWS CLI and waited for the update to finish.

I then invoked the function again using the same six-second event.

The function completed successfully and returned the expected response.

I also tested a one-second workload to demonstrate the difference between allowing more execution time and reducing processing duration.

Finally, I removed the temporary Lambda function, execution role, and CloudWatch log group.

---

## 21. Repository Structure, Lessons Learned, and Skills Demonstrated

### Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
├── 01-lambda-runtime-error/
├── 02-handler-not-found/
│
├── 03-lambda-timeout/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── slow-event.json
│   ├── fast-event.json
│   ├── function.zip
│   ├── lab03-resources.env
│   ├── lab03-broken-configuration.json
│   ├── lab03-recovered-configuration.json
│   ├── lab03-broken-invocation.json
│   ├── lab03-healthy-invocation.json
│   ├── lab03-fast-invocation.json
│   ├── lab03-broken-cloudwatch-evidence.json
│   ├── lab03-recovery-cloudwatch-evidence.json
│   ├── broken-response.json
│   ├── healthy-response.json
│   └── fast-response.json
│
├── 04-missing-environment-variable/
├── 05-lambda-access-denied/
├── 06-lambda-no-internet-vpc/
├── 07-lambda-rds-connection-failure/
├── 08-lambda-memory-exhaustion/
├── 09-lambda-event-not-triggering/
├── 10-lambda-dependency-import-error/
├── 11-lambda-concurrency-throttling/
└── 12-lambda-async-retry-dlq-failure/
```

### File Descriptions

| File | Purpose |
|---|---|
| `README.md` | Production incident documentation |
| `lambda_function.py` | Lambda Python application |
| `lambda-trust-policy.json` | Execution role trust policy |
| `slow-event.json` | Six-second test payload |
| `fast-event.json` | One-second test payload |
| `function.zip` | Generated Lambda deployment package |
| `lab03-resources.env` | Local resource identifiers |
| `lab03-broken-configuration.json` | Original timeout configuration |
| `lab03-recovered-configuration.json` | Updated timeout configuration |
| `lab03-broken-invocation.json` | Failed invocation metadata |
| `lab03-healthy-invocation.json` | Recovery invocation metadata |
| `lab03-fast-invocation.json` | Optimized test metadata |
| `lab03-broken-cloudwatch-evidence.json` | Timeout investigation logs |
| `lab03-recovery-cloudwatch-evidence.json` | Successful execution logs |
| `broken-response.json` | Timeout error payload |
| `healthy-response.json` | Successful processing response |
| `fast-response.json` | One-second processing response |

### Recommended Public GitHub Files

```text
README.md
lambda_function.py
lambda-trust-policy.json
slow-event.json
fast-event.json
```

Keep generated deployment packages, account-specific environment files, and raw AWS invocation evidence local or sanitize them before publishing.

### Lessons Learned

This lab demonstrates how AWS Lambda execution timeouts can cause application failures even when the function is deployed successfully.

We created a Python Lambda application with a six-second processing workload and intentionally configured a three-second timeout.

The function became Active but terminated before completing its operation.

We investigated the Lambda invocation response, CloudWatch logs, and execution metrics.

The root cause was an execution timeout that was too short for the workload.

We updated the function timeout to 10 seconds without changing the application code.

After remediation, the original six-second workload completed successfully.

We also tested a faster workload to demonstrate that changing timeout configuration is different from optimizing application performance.

Finally, we cleaned up the temporary AWS resources.

**Key Lesson:** Production Lambda troubleshooting requires comparing actual execution duration against the configured timeout and investigating the workload before choosing the appropriate remediation.

### Skills Demonstrated

- AWS Lambda
- Python 3.13
- Lambda execution timeout
- AWS CLI v2
- Linux Bash
- IAM execution roles
- IAM trust policies
- CloudWatch Logs
- CloudWatch Metrics
- Duration and Errors investigation
- Lambda Invoke API
- FunctionError analysis
- Lambda context object
- Python time simulation
- Lambda configuration updates
- Root cause analysis
- Recovery verification
- Performance troubleshooting
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-003 |
| Scenario | Lambda Timeout |
| Function | lambda-lab03-timeout |
| Region | us-east-1 |
| Runtime | Python 3.13 |
| Broken Timeout | 3 seconds |
| Workload | 6 seconds |
| Error | Execution timeout |
| Root Cause | Insufficient timeout |
| Remediation | Increase timeout to 10 seconds |
| Recovery Result | Successful processing |
| Fast Test | 1-second workload |
| CloudWatch Evidence | Timeout and successful execution |
| Cleanup | Function, role, and logs deleted |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** A Lambda timeout is not always a code failure. Engineers must investigate the relationship between execution time, configuration, performance, and downstream service behavior.

---

## Official AWS Documentation

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Configure Lambda Timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html)
- [Troubleshooting Lambda Execution](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)
- [AWS Lambda Python Context Object](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html)
- [Viewing Lambda Logs in CloudWatch](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html)
- [AWS CLI — Lambda Invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)
- [AWS CLI — Update Function Configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-configuration.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)