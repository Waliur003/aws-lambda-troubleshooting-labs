# Lab 04 — AWS Lambda Missing Environment Variable

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve a missing environment variable in AWS Lambda using AWS CLI, Python, Linux Bash, and Amazon CloudWatch Logs.

AWS Lambda environment variables allow engineers to configure application behavior without changing the source code.

Applications commonly use environment variables for deployment environments, feature flags, logging levels, resource identifiers, and other non-sensitive settings.

However, a Lambda function can deploy successfully and still fail during execution when a required environment variable is missing.

In this lab, we simulate a production incident involving a Python Lambda function that processes customer orders.

The application requires an environment variable called `APP_ENV`.

The function is intentionally deployed without this variable.

When invoked, the application attempts to access `APP_ENV` using Python's `os.environ` dictionary and raises a `KeyError`.

We investigate the Lambda invocation response, CloudWatch Logs, function configuration, and Python code to identify the root cause.

After identifying the missing configuration, we update the Lambda environment variables using AWS CLI.

We then invoke the same event again and verify successful order processing.

An additional exercise demonstrates how updating the environment configuration incorrectly can remove existing environment variables.

Finally, we restore the correct configuration, verify the function, and delete the temporary AWS resources.

### Troubleshooting Workflow

```text
Create Lambda Execution Role
             |
             v
Configure CloudWatch Logs
             |
             v
Create Python Application
             |
             v
Application Requires APP_ENV
             |
             v
Deploy Without APP_ENV
             |
             v
Invoke Lambda Function
             |
             v
KeyError: 'APP_ENV'
             |
             v
Inspect Invocation Response
             |
             v
Investigate CloudWatch Logs
             |
             v
Inspect Environment Configuration
             |
             v
Identify Missing Variable
             |
             v
Update Lambda Configuration
             |
             v
Verify APP_ENV Exists
             |
             v
Invoke Function Again
             |
             v
Successful Order Processing
             |
             v
Test Environment Map Replacement
             |
             v
Restore Configuration
             |
             v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-004 |
| Lab Name | Lambda Missing Environment Variable |
| Difficulty | Beginner to Intermediate |
| Primary Service | AWS Lambda |
| Supporting Services | IAM, CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Programming Language | Python |
| Runtime | Python 3.13 |
| Function Name | `lambda-lab04-missing-env` |
| Execution Role | `lambda-lab04-execution-role` |
| Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Timeout | 10 seconds |
| Architecture | x86_64 |
| CloudWatch Log Group | `/aws/lambda/lambda-lab04-missing-env` |
| Log Retention | 7 days |
| Required Variable | `APP_ENV` |
| Initial Configuration | APP_ENV missing |
| Recovery Value | `production` |
| Additional Variable | `LOG_LEVEL=INFO` |
| Expected Exception | `KeyError` |
| Expected FunctionError | `Unhandled` |
| Root Cause | Missing application configuration |
| Remediation | Add required environment variable |
| Code Redeployment | Not required |
| Verification | Successful Lambda invocation |
| Cleanup | Lambda, IAM role, CloudWatch Logs |

### Lab Objectives

- Understand Lambda environment variables.
- Learn how Python accesses environment variables.
- Identify configuration-related runtime failures.
- Reproduce a `KeyError`.
- Inspect Lambda invocation responses.
- Investigate CloudWatch error logs.
- Inspect function configuration with AWS CLI.
- Identify missing environment settings.
- Update environment variables without redeploying code.
- Understand environment-variable map replacement.
- Verify the application after remediation.
- Understand safe configuration management.
- Apply basic cloud security practices.
- Perform root cause analysis and resource cleanup.

---

## 2. Production Incident Scenario

### Incident Description

A company uses an AWS Lambda function to process customer orders.

The application receives an order identifier and uses the `APP_ENV` environment variable to determine its deployment environment.

The function is expected to process orders and return a successful response.

During a deployment, the engineer forgets to configure `APP_ENV`.

AWS Lambda reports that the deployment was successful, and the function enters the Active state.

However, the application fails whenever it receives an invocation.

The Lambda invocation response contains a Python `KeyError`.

CloudWatch Logs show that the application started processing an order but failed when accessing the required environment variable.

The Cloud Engineering team investigates the issue.

The engineer verifies the deployed Python code, Lambda configuration, and application log messages.

The code contains:

```python
app_env = os.environ["APP_ENV"]
```

However, the function's environment-variable configuration does not contain `APP_ENV`.

Python raises a `KeyError` because the key is missing.

The engineer determines that the failure is caused by incomplete Lambda configuration rather than a missing IAM permission or incorrect handler.

The engineer adds the required environment variable using AWS CLI.

After the configuration update completes, the function processes the same order successfully.

### Incident Symptoms

- Lambda function is successfully deployed.
- Function state is Active.
- Python handler exists and starts executing.
- Application receives a valid event.
- `APP_ENV` is missing from Lambda configuration.
- Python raises `KeyError`.
- Lambda reports an unhandled execution error.
- CloudWatch Logs contain a traceback.
- Application does not complete order processing.

### Business Impact

Missing environment variables can cause:

- Failed application requests.
- Broken background jobs.
- Interrupted event processing.
- Incorrect application behavior.
- Production deployment failures.
- Unavailable serverless endpoints.
- Delayed order processing.
- Increased error rates.
- Additional engineering investigation time.

### Objective

Identify the missing application environment variable, update the Lambda configuration, and verify that the application executes successfully without changing its source code.

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
            lambda-lab04-missing-env
                      |
                      v
                 Python Handler
                      |
                      v
              Read Customer Order
                      |
                      v
            os.environ["APP_ENV"]
                      |
                      v
             APP_ENV Not Configured
                      |
                      v
                 Python KeyError
                      |
             +--------+--------+
             |                 |
             v                 v
       FunctionError      CloudWatch Logs
         Unhandled         Error Traceback
```

### Recovered Architecture

```text
                Cloud Engineer
                      |
                      v
                   AWS CLI
                      |
                      v
       Update Lambda Environment
                      |
                      v
           APP_ENV = production
           LOG_LEVEL = INFO
                      |
                      v
                Lambda Invoke
                      |
                      v
            lambda-lab04-missing-env
                      |
                      v
                 Python Handler
                      |
                      v
              Read Customer Order
                      |
                      v
             Read APP_ENV Variable
                      |
                      v
               Process Order
                      |
                      v
                statusCode: 200
                      |
                      v
             Successful Execution
```

### AWS Components

| Component | Purpose |
|---|---|
| AWS Lambda | Executes Python application code |
| Environment Variables | Store runtime application configuration |
| Python `os` Module | Accesses environment values |
| IAM Execution Role | Grants CloudWatch logging permissions |
| IAM Trust Policy | Allows Lambda to assume the role |
| CloudWatch Logs | Records runtime errors and execution output |
| AWS CLI | Deploys and updates Lambda configuration |
| Bash | Automates troubleshooting commands |
| JSON Files | Store deployment configuration and test events |

---

## 4. Understanding Lambda Environment Variables

### What Are Environment Variables?

Environment variables are key-value pairs made available to the application during execution.

Example:

```text
APP_ENV=production
LOG_LEVEL=INFO
```

They allow an application to change behavior without modifying its source code.

### Why Are They Useful?

Common use cases include:

- Deployment environment identification.
- Application logging levels.
- Feature flags.
- External service identifiers.
- Resource names.
- Non-sensitive application configuration.

### How Does Python Access Environment Variables?

Python provides the `os` module.

Example:

```python
import os

app_env = os.environ["APP_ENV"]
```

### What Happens if the Variable Is Missing?

Using:

```python
os.environ["APP_ENV"]
```

raises:

```text
KeyError: 'APP_ENV'
```

if `APP_ENV` is not defined.

### What Is the Difference Between os.environ and os.getenv?

Direct dictionary access:

```python
os.environ["APP_ENV"]
```

raises `KeyError` when the variable is missing.

Optional lookup:

```python
os.getenv("APP_ENV")
```

returns `None` if it is missing.

A default can also be provided:

```python
os.getenv("APP_ENV", "development")
```

### Should Every Missing Variable Have a Default?

No.

Required configuration should generally be validated explicitly.

Using defaults for critical configuration can hide deployment mistakes.

For optional settings, documented defaults may be appropriate.

### Can Environment Variables Be Updated Without Redeploying Code?

Yes.

For a conventional Lambda function's unpublished configuration, use:

```bash
aws lambda update-function-configuration
```

The Lambda service applies the configuration update separately from the deployment package.

Published Lambda versions have immutable configuration.

### What Happens When Updating the Variables Map?

The entire user-defined environment-variable map is replaced.

Existing variables omitted from the update are removed.

For example:

Before:

```json
{
  "APP_ENV": "production",
  "LOG_LEVEL": "INFO"
}
```

Update:

```text
Variables={APP_ENV=staging}
```

After:

```json
{
  "APP_ENV": "staging"
}
```

`LOG_LEVEL` is no longer configured.

### Are Environment Variables Suitable for Secrets?

Use appropriate secret storage for credentials and other sensitive information.

AWS Secrets Manager is generally preferred for passwords, API keys, and tokens.

Avoid exposing sensitive values in logs, command history, or Git repositories.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Bash.
- Python 3.
- ZIP and unzip.
- Lambda management permissions.
- IAM role creation permissions.
- CloudWatch Logs permissions.

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
lambda:UpdateFunctionConfiguration
lambda:ListTags
lambda:DeleteFunction

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

### Safety Rules

- Use only dedicated Lab 04 resources.
- Never modify production Lambda configurations.
- Do not store secrets in this lab's environment variables.
- Verify resource ownership before deletion.
- Do not publish raw AWS configuration evidence.
- Do not expose AWS credentials.
- Preserve existing variables during production updates.
- Use a dedicated IAM role with minimal permissions.

### Cost Considerations

This lab uses short Lambda invocations and CloudWatch logging.

Possible costs include Lambda requests, execution duration, and CloudWatch log ingestion or storage.

No EC2 instances, RDS databases, or NAT Gateways are required.

---

## 6. Prepare the Environment

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 04-missing-environment-variable

cd 04-missing-environment-variable
```

### Step 2 — Verify Installed Tools

```bash
aws --version
python3 --version
zip -v
```

Install ZIP if missing:

```bash
sudo apt update
sudo apt install -y zip unzip
```

### Step 3 — Verify AWS Identity

```bash
aws sts get-caller-identity
```

### Step 4 — Configure Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab04"

export FUNCTION_NAME="lambda-lab04-missing-env"

export ROLE_NAME="lambda-lab04-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export RUNTIME="python3.13"

export REQUIRED_ENV_NAME="APP_ENV"

export REQUIRED_ENV_VALUE="production"
```

### Step 5 — Save Variables

```bash
cat > lab04-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export RUNTIME="$RUNTIME"
export REQUIRED_ENV_NAME="$REQUIRED_ENV_NAME"
export REQUIRED_ENV_VALUE="$REQUIRED_ENV_VALUE"
EOF
```

Restore:

```bash
source lab04-resources.env
```

### Step 6 — Check Existing Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

For a new lab, both resources should be absent.

If they already exist, verify ownership before modifying them.

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

### Step 2 — Verify JSON

```bash
python3 -m json.tool lambda-trust-policy.json
```

### Step 3 — Create IAM Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Execution role for Lambda Lab 04" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 4 — Attach CloudWatch Permissions

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

### Step 6 — Verify Attached Policies

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

### Step 3 — Verify Log Group

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query "logGroups[?logGroupName=='${LOG_GROUP}'].{Name:logGroupName,Retention:retentionInDays}" \
  --output table \
  --region "$AWS_REGION"
```

Expected: the lab log group exists with seven-day retention.

---

## 9. Create the Python Application

### Step 1 — Create `lambda_function.py`

```python
import json
import os


def lambda_handler(event, context):
    print("Lambda Lab 04 started")

    order_id = event.get("order_id", "ORDER-1001")

    print(f"Processing order: {order_id}")

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
```

### Step 2 — Understand the Fault

The critical line is:

```python
app_env = os.environ["APP_ENV"]
```

The application requires this variable to exist.

The initial Lambda deployment intentionally omits it.

Therefore, invoking the function produces:

```text
KeyError: 'APP_ENV'
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

### Step 4 — Create the ZIP Package

```bash
zip function.zip lambda_function.py
```

Verify:

```bash
unzip -l function.zip
```

### Step 5 — Create Test Event

Save as `test-event.json`:

```json
{
  "order_id": "ORDER-1001"
}
```

---

## 10. Deploy Lambda Without the Required Variable

### Step 1 — Create Function

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --memory-size 128 \
  --architectures x86_64 \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

The command deliberately omits the environment-variable configuration.

If the IAM role is newly created, IAM propagation may delay successful function creation.

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Inspect Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,Runtime:Runtime,Handler:Handler,State:State,Environment:Environment,Timeout:Timeout}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 4 — Check APP_ENV Directly

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables.APP_ENV' \
  --output text \
  --region "$AWS_REGION"
```

Expected:

```text
None
```

### Step 5 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab04-broken-configuration.json
```

### Initial Investigation

| Setting | Expected |
|---|---|
| Function state | Active |
| Python handler | Correct |
| Deployment package | Valid |
| Required APP_ENV | Missing |
| Invocation readiness | Active but application will fail |

---

<WritingBlock id="84218" variant="document">## 11. Fault Injection — Reproduce the KeyError

### Step 1 — Invoke the Broken Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab04-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab04-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

### Understanding StatusCode 200

A synchronous Lambda Invoke API request can succeed even when application execution fails.

`StatusCode=200` represents the Invoke API response.

`FunctionError` identifies the Lambda execution failure.

### Step 3 — Inspect the Error Response

```bash
python3 -m json.tool broken-response.json
```

Expected structure:

```json
{
  "errorMessage": "'APP_ENV'",
  "errorType": "KeyError",
  "requestId": "ACTUAL_REQUEST_ID",
  "stackTrace": [
    "..."
  ]
}
```

The actual request ID and traceback come from your execution.

### Step 4 — Extract the Error

```bash
python3 - <<'PY'
import json

with open("broken-response.json") as file:
    response = json.load(file)

print("Error type:", response.get("errorType"))
print("Error message:", response.get("errorMessage"))
print("Request ID:", response.get("requestId"))
PY
```

### Step 5 — Verify Fault Reproduction

```bash
python3 - <<'PY'
import json

with open("lab04-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    payload = json.load(file)

assert invocation["StatusCode"] == 200
assert invocation.get("FunctionError") == "Unhandled"
assert payload.get("errorType") == "KeyError"
assert "APP_ENV" in payload.get("errorMessage", "")

print("SUCCESS: Missing APP_ENV error reproduced")
PY
```

Expected:

```text
SUCCESS: Missing APP_ENV error reproduced
```

### Step 6 — Decode the Inline Logs

```bash
python3 - <<'PY'
import base64
import json

with open("lab04-broken-invocation.json") as file:
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

### Broken-State Verification

| Check | Expected |
|---|---|
| Lambda deployment | Successful |
| Function state | Active |
| Handler execution | Started |
| Required variable | Absent |
| Python exception | KeyError |
| FunctionError | Unhandled |
| Order completed | No |
| CloudWatch traceback | Present |

---

## 12. Investigate CloudWatch Logs

### Step 1 — View Recent Lambda Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected log structure resembles:

```text
Lambda Lab 04 started
Processing order: ORDER-1001

[ERROR] KeyError: 'APP_ENV'
Traceback (most recent call last):
...
```

### Step 2 — Search for KeyError

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"KeyError"' \
  --query 'events[].{Timestamp:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search for APP_ENV

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"APP_ENV"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Step 4 — Save Failure Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab04-broken-cloudwatch-evidence.json
```

### Step 5 — Inspect the Python File

```bash
nl -ba lambda_function.py
```

Identify:

```python
app_env = os.environ["APP_ENV"]
```

### Step 6 — Compare with Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json \
  --region "$AWS_REGION"
```

### Investigation Findings

| Evidence | Finding |
|---|---|
| Handler configuration | Correct |
| Python code | Valid |
| Function started | Yes |
| Order ID | ORDER-1001 |
| Required setting | APP_ENV |
| Lambda configuration | APP_ENV missing |
| Error type | KeyError |
| Failure location | os.environ access |
| Root cause | Incomplete configuration |

### Troubleshooting Lesson

The application handler starts successfully, but fails after accessing missing configuration.

This distinguishes Lab 04 from initialization failures such as HandlerNotFound or ImportModuleError.

---

## 13. Root Cause Analysis

### Root Cause

The application requires an environment variable named `APP_ENV`, but the function was deployed without it.

The Python handler reads the variable using:

```python
app_env = os.environ["APP_ENV"]
```

Because the variable was not configured, Python raises `KeyError`.

The application does not catch the exception.

Lambda reports an unhandled execution failure.

### Root Cause Diagram

```text
Lambda Invocation
        |
        v
Python Handler Starts
        |
        v
Read Order Identifier
        |
        v
Access APP_ENV
        |
        v
Variable Not Found
        |
        v
Python KeyError
        |
        v
Unhandled Function Error
        |
        v
CloudWatch Traceback
```

### Five Whys

**Why 1 — Why did the Lambda function fail?**

Python raised a KeyError.

**Why 2 — Why did KeyError occur?**

The application accessed a missing environment variable.

**Why 3 — Why was the variable missing?**

The deployment configuration omitted APP_ENV.

**Why 4 — Why wasn't the issue detected earlier?**

The function was deployed without validating required application configuration.

**Why 5 — How can this be prevented?**

Manage required variables through version-controlled infrastructure configuration and test the deployed function.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-004 |
| AWS Service | Lambda |
| Error | KeyError |
| Missing Key | APP_ENV |
| Fault Category | Application configuration |
| Root Cause | Missing environment variable |
| Remediation | Add APP_ENV |
| Code Redeployment | Not required |
| Verification | Successful invocation |

---

## 14. Remediation — Add the Missing Environment Variable

### Step 1 — Inspect Existing Environment

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json \
  --region "$AWS_REGION"
```

For this dedicated lab function, no user-defined variables were configured.

In production, inspect and preserve the existing variables before updating them.

### Step 2 — Create Environment Configuration

Save as `lambda-environment.json`:

```json
{
  "Variables": {
    "APP_ENV": "production",
    "LOG_LEVEL": "INFO"
  }
}
```

`APP_ENV` is required.

`LOG_LEVEL` is an additional harmless configuration setting used for the advanced experiment.

### Step 3 — Validate JSON

```bash
python3 -m json.tool lambda-environment.json
```

### Step 4 — Update Lambda Configuration

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --environment file://lambda-environment.json \
  --region "$AWS_REGION"
```

### Step 5 — Wait for Update Completion

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 6 — Verify Updated Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,LastUpdateStatus:LastUpdateStatus,Environment:Environment.Variables}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "State": "Active",
  "LastUpdateStatus": "Successful",
  "Environment": {
    "APP_ENV": "production",
    "LOG_LEVEL": "INFO"
  }
}
```

### Step 7 — Save Recovered Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab04-recovered-configuration.json
```

### Remediation Comparison

| Setting | Broken | Recovered |
|---|---|---|
| Function state | Active | Active |
| APP_ENV | Missing | production |
| LOG_LEVEL | Missing | INFO |
| Handler | Correct | Correct |
| Code | Unchanged | Unchanged |
| ZIP deployment | Unchanged | Unchanged |
| Application outcome | KeyError | Successful execution |

### Important Note

The recovery is a Lambda configuration change.

No source-code modification is required to fix this specific missing-variable incident.

---

## 15. Verify Successful Recovery

### Step 1 — Invoke the Same Event

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab04-healthy-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab04-healthy-invocation.json
```

Expected relevant field:

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
  "body": "{\"message\": \"Order processed successfully\", \"order_id\": \"ORDER-1001\", \"environment\": \"production\"}"
}
```

### Step 4 — Verify Response Programmatically

```bash
python3 - <<'PY'
import json

with open("lab04-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200

assert body["order_id"] == "ORDER-1001"
assert body["environment"] == "production"

print("SUCCESS: Missing environment variable resolved")
PY
```

Expected:

```text
SUCCESS: Missing environment variable resolved
```

### Step 5 — Verify CloudWatch Recovery Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Lambda Lab 04 started
Processing order: ORDER-1001
Application environment: production
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Application environment:"' \
  --output json \
  --region "$AWS_REGION" \
  > lab04-recovered-cloudwatch-evidence.json
```

### Before and After Verification

| Check | Broken | Recovered |
|---|---|---|
| Lambda deployed | Yes | Yes |
| APP_ENV | Missing | production |
| Python KeyError | Yes | No |
| FunctionError | Unhandled | Absent |
| Order processing | Failed | Successful |
| Response statusCode | Not returned | 200 |
| Code redeployment | Not required | Not required |
| CloudWatch evidence | Error traceback | Success logs |

**Recovery is confirmed when the required variable exists, the function executes without an unhandled error, and the original order event returns the expected result.**

---

## 16. Advanced Exercise — Environment Variable Replacement

### Production Scenario

A Lambda function contains several environment variables.

An engineer updates one setting but accidentally omits the others.

Because Lambda replaces the entire variables map, the omitted settings disappear.

This can cause additional production incidents.

### Step 1 — Inspect the Existing Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "APP_ENV": "production",
  "LOG_LEVEL": "INFO"
}
```

### Step 2 — Apply an Incomplete Update

This is safe only because the function is a dedicated disposable lab resource.

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --environment 'Variables={APP_ENV=staging}' \
  --region "$AWS_REGION"
```

### Step 3 — Wait for Completion

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 4 — Inspect Environment Variables

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "APP_ENV": "staging"
}
```

`LOG_LEVEL` has been removed.

### Step 5 — Restore the Complete Configuration

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --environment file://lambda-environment.json \
  --region "$AWS_REGION"
```

### Step 6 — Wait for Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 7 — Verify Restoration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```json
{
  "APP_ENV": "production",
  "LOG_LEVEL": "INFO"
}
```

### Root Cause of the Secondary Incident

The configuration update replaced the entire environment-variable map.

The engineer supplied only one variable rather than the full intended set.

### Production Prevention

- Read the current environment configuration before updating.
- Preserve existing settings.
- Use Infrastructure as Code.
- Review changes before deployment.
- Consider revision-based update controls.
- Validate required configuration after deployment.
- Avoid storing secrets directly in environment-variable files.

---

<WritingBlock id="84219" variant="document">## 17. Production Troubleshooting Best Practices

### Investigation Checklist

1. Verify the AWS account and Region.
2. Identify the affected Lambda function.
3. Inspect function state and runtime.
4. Reproduce the error using a known event.
5. Inspect the Lambda Invoke response.
6. Examine `FunctionError`.
7. Read the error payload.
8. Investigate CloudWatch Logs.
9. Identify the Python exception.
10. Inspect the code's environment-variable requirements.
11. Check Lambda environment configuration.
12. Confirm which required variable is missing.
13. Preserve existing configuration values.
14. Apply the remediation.
15. Wait for configuration update completion.
16. Verify the environment variables.
17. Invoke the original event again.
18. Confirm successful execution.
19. Document the findings.
20. Clean up the temporary resources.

### Investigation Workflow

```text
Lambda Invocation Failure
             |
             v
Inspect FunctionError
             |
             v
Read CloudWatch Logs
             |
             v
Identify Python KeyError
             |
             v
Inspect Source Code
             |
             v
Identify Required Variable
             |
             v
Inspect Lambda Configuration
             |
             v
Confirm Variable Is Missing
             |
             v
Update Environment Variables
             |
             v
Verify Updated Configuration
             |
             v
Repeat Original Invocation
             |
             v
Confirm Successful Recovery
```

### Common Environment Configuration Problems

| Problem | Symptom | Investigation |
|---|---|---|
| Missing variable | KeyError | Check Environment.Variables |
| Wrong variable name | Expected key absent | Compare code and configuration |
| Wrong capitalization | Missing-key behavior | Check exact names |
| Empty value | Invalid application configuration | Validate values |
| Incorrect environment | Wrong application behavior | Check APP_ENV |
| Incomplete update | Previously configured values disappear | Compare before and after |
| Sensitive value exposed | Potential credential leak | Review configuration and logs |
| Wrong published version | Unexpected old configuration | Inspect version or alias |

### Production Recommendations

- Manage configuration using Terraform or CloudFormation.
- Validate required settings during deployment.
- Keep environment-variable names consistent.
- Avoid unnecessary defaults for required variables.
- Use Secrets Manager for sensitive credentials.
- Never log secrets.
- Preserve the complete variables map during updates.
- Validate Lambda configuration changes before deployment.
- Monitor runtime errors and unsuccessful invocations.
- Use post-deployment smoke tests.

---

## 18. Security Considerations

### Environment Variables and Secrets

Environment variables are suitable for non-sensitive configuration.

Examples:

```text
APP_ENV=production
LOG_LEVEL=INFO
FEATURE_ENABLED=true
```

For passwords, API tokens, and other credentials, prefer AWS Secrets Manager or an appropriate secure configuration service.

### Least-Privilege IAM

This lab's Lambda function only needs CloudWatch logging access.

The execution role uses the AWS-managed `AWSLambdaBasicExecutionRole` policy.

No S3, DynamoDB, RDS, or other application permissions are needed.

### CloudWatch Logging

Avoid printing credentials or sensitive configuration values.

The lab logs `APP_ENV` because it is a harmless environment label.

In production, use structured logs and include useful identifiers without exposing sensitive information.

### Deployment Security

Configuration changes should be reviewed and managed through approved deployment processes.

Unexpected changes may be investigated through AWS CloudTrail.

---

## 19. AWS Resource Cleanup

**Warning:** Delete only the AWS resources created for Lab 04.

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
Project=Lambda-Troubleshooting-Lab04
```

### Step 2 — Verify Execution Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Verify CloudWatch Log Group

```bash
echo "$LOG_GROUP"
```

Expected:

```text
/aws/lambda/lambda-lab04-missing-env
```

### Step 4 — Delete Lambda Function

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 5 — Detach IAM Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 6 — Delete Execution Role

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

### Step 9 — Verify Role Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 10 — Verify Log Group Removal

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
| IAM execution role | Deleted |
| IAM managed policy attachment | Removed |
| CloudWatch log group | Deleted |
| EC2 | None created |
| VPC | None created |
| RDS | None created |
| NAT Gateway | None created |
| S3 bucket | None created |

---

## 20. Interview Questions and Answers

### Q1. What are Lambda environment variables?

Key-value pairs used to configure application behavior without changing source code.

### Q2. What caused the error in this lab?

The application required APP_ENV, but Lambda did not have that variable configured.

### Q3. What is Python KeyError?

An exception raised when code attempts to access a missing dictionary key.

### Q4. What is the difference between os.environ and os.getenv?

Direct `os.environ["KEY"]` access raises KeyError if the key is missing. `os.getenv("KEY")` returns None or a provided default.

### Q5. How do you inspect Lambda environment variables?

```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --query 'Environment.Variables' \
  --region us-east-1
```

### Q6. How do you update Lambda environment variables?

Use `aws lambda update-function-configuration` with the complete intended environment-variable map.

### Q7. Does updating environment variables require code redeployment?

No. Lambda configuration can be updated separately.

### Q8. What happens if existing environment variables are omitted during an update?

The omitted user-defined variables are removed because the update replaces the complete map.

### Q9. Why is Infrastructure as Code useful?

It helps manage configuration consistently and makes changes reviewable.

### Q10. Should passwords be stored directly in Lambda environment variables?

AWS generally recommends using Secrets Manager for credentials and other sensitive information.

### Q11. How would you investigate a missing configuration error?

Inspect the invocation response, traceback, application code, and Lambda configuration.

### Q12. What is the difference between KeyError and AccessDenied?

KeyError is a Python application exception. AccessDenied is an AWS authorization failure.

### Q13. Can Lambda deploy successfully with missing application configuration?

Yes. The missing variable may cause a failure when the application accesses it during execution.

### Q14. How can this problem be prevented in CI/CD?

Validate required configuration and run deployment smoke tests.

### Q15. Why should production environment updates preserve existing variables?

Because removing an unrelated setting can cause another application failure.

### Q16. What does FunctionError=Unhandled indicate?

An unhandled error occurred during the Lambda execution.

### Q17. Why might the Invoke API return StatusCode 200 during KeyError?

The API request succeeded, but the function execution failed separately.

### Q18. Would increasing Lambda memory fix a missing variable?

No. The problem is application configuration, not memory capacity.

### Q19. Would increasing Lambda timeout fix KeyError?

No. More execution time does not create the missing variable.

### Q20. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function that required an environment variable named APP_ENV.

I intentionally omitted that variable from the deployment configuration.

The function deployed successfully but failed during invocation with a Python KeyError.

I inspected the Lambda invocation response, CloudWatch traceback, and function environment configuration.

I determined that the required APP_ENV variable was missing.

I added the variable using AWS CLI without redeploying the application code.

After the update, I invoked the function again and verified that the order-processing operation completed successfully.

I also reproduced a separate configuration issue where an incomplete environment-variable update removed an existing variable.

I restored the complete configuration, verified the result, and cleaned up the temporary AWS resources.

---

## 21. Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
│
├── 01-lambda-runtime-error/
├── 02-handler-not-found/
├── 03-lambda-timeout/
│
├── 04-missing-environment-variable/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── lambda-environment.json
│   ├── test-event.json
│   ├── function.zip
│   ├── lab04-resources.env
│   ├── lab04-broken-configuration.json
│   ├── lab04-recovered-configuration.json
│   ├── lab04-broken-invocation.json
│   ├── lab04-healthy-invocation.json
│   ├── lab04-broken-cloudwatch-evidence.json
│   ├── lab04-recovered-cloudwatch-evidence.json
│   ├── broken-response.json
│   └── healthy-response.json
│
├── 05-lambda-access-denied/
├── 06-lambda-no-internet-vpc/
├── 07-lambda-rds-connection-failure/
├── 08-lambda-memory-exhaustion/
├── 09-lambda-event-not-triggering/
├── 10-lambda-dependency-import-error/
├── 11-lambda-concurrency-throttling/
└── 12-lambda-async-retry-dlq-failure/
```

The directory tree includes locally generated evidence that should not be committed to a public GitHub repository without review.

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Incident documentation |
| lambda_function.py | Lambda application code |
| lambda-trust-policy.json | IAM execution role trust policy |
| lambda-environment.json | Corrected environment configuration |
| test-event.json | Customer order test event |
| function.zip | Generated deployment package |
| lab04-resources.env | Lab resource identifiers |
| lab04-broken-configuration.json | Initial Lambda configuration |
| lab04-recovered-configuration.json | Recovered configuration |
| lab04-broken-invocation.json | Failed invocation metadata |
| lab04-healthy-invocation.json | Successful invocation metadata |
| lab04-broken-cloudwatch-evidence.json | Error logs |
| lab04-recovered-cloudwatch-evidence.json | Recovery logs |
| broken-response.json | KeyError response |
| healthy-response.json | Successful application response |

### Public GitHub Files

Recommended for version control:

```text
README.md
lambda_function.py
lambda-trust-policy.json
lambda-environment.json
test-event.json
```

Keep raw CloudWatch logs, generated ZIP packages, AWS configuration dumps, and account-specific data local.

### Recommended .gitignore

Add the following rules to the root `.gitignore` before staging your repository:

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Generated Lambda packages
*.zip

# Local AWS environment
**/lab04-resources.env

# Lambda configuration snapshots
**/lab04-*-configuration.json

# Invocation metadata
**/lab04-*-invocation.json

# CloudWatch evidence
**/lab04-*-evidence.json

# Response payloads
04-missing-environment-variable/broken-response.json
04-missing-environment-variable/healthy-response.json

# Credentials
.env
.env.*
*.pem
*.key
```

Always review staged changes before publishing any information from a real AWS account.

---

## 22. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how missing Lambda environment variables can cause application failures even when the function deploys successfully.

We created a Python Lambda function that required APP_ENV to process an order.

The function was intentionally deployed without the required variable.

When invoked, Python raised a KeyError.

We inspected the invocation response and CloudWatch Logs to identify the exception.

We then inspected the Lambda configuration and confirmed that APP_ENV was missing.

The root cause was an incomplete environment configuration.

We added the required variable using AWS CLI and verified that the same test event completed successfully.

An additional exercise demonstrated that updating only one environment variable can remove other existing variables.

We restored the complete configuration and verified the result.

Finally, we removed the dedicated AWS resources.

**Key Lesson:** A Lambda deployment can be successful while the application remains incorrectly configured. Engineers must validate required environment settings and preserve the complete configuration during updates.

### Skills Demonstrated

- AWS Lambda
- Python 3.13
- Lambda environment variables
- AWS CLI v2
- Linux Bash
- Python os module
- KeyError investigation
- IAM execution roles
- IAM trust policies
- AWSLambdaBasicExecutionRole
- CloudWatch Logs
- Lambda Invoke API
- FunctionError analysis
- Lambda configuration updates
- Configuration validation
- Environment-variable map replacement
- Root cause analysis
- Remediation verification
- Cloud security configuration practices
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-004 |
| Scenario | Missing Environment Variable |
| Function | lambda-lab04-missing-env |
| Region | us-east-1 |
| Runtime | Python 3.13 |
| Broken Variable | APP_ENV missing |
| Error | KeyError |
| Root Cause | Incomplete Lambda configuration |
| Remediation | APP_ENV=production |
| Additional Setting | LOG_LEVEL=INFO |
| Code Changes | None |
| Recovery | Successful order processing |
| Advanced Test | Environment map replacement |
| Cleanup | Function, role, and logs deleted |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** AWS Lambda environment variables are part of application configuration. Missing or incorrectly updated variables can cause production incidents even when deployment and Lambda infrastructure are healthy.

---

## Official AWS Documentation

- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [AWS CLI — Update Function Configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-configuration.html)
- [AWS Lambda Python Logging](https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html)
- [AWS Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [AWS Lambda CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)