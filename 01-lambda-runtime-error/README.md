# Lab 01 — AWS Lambda Runtime Error

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda runtime error using AWS CLI, Python, Linux Bash, and Amazon CloudWatch Logs.

AWS Lambda is a serverless compute service that allows applications to execute code without managing servers.

Although AWS handles the underlying infrastructure, engineers are responsible for troubleshooting problems inside the application code.

A Lambda function may deploy successfully and enter the `Active` state but still fail during execution because of a programming error.

In production environments, these runtime failures can interrupt automated workflows, prevent event processing, and cause application failures.

In this lab, we simulate a production incident involving a Python Lambda function that attempts to divide a number by zero.

The function deploys successfully, but invocation fails with a `ZeroDivisionError`.

We investigate the Lambda invocation response, inspect CloudWatch Logs, examine the Python stack trace, and identify the failing line of code.

After identifying the root cause, we correct the function by adding input validation and safe error handling.

We then redeploy the corrected application and verify successful execution.

Finally, we test invalid input to confirm the function returns a controlled response instead of crashing.

The lab concludes with resource cleanup and incident documentation.

### Troubleshooting Workflow

```text
Create Lambda Execution Role
            |
            v
Configure CloudWatch Logs
            |
            v
Create Broken Python Function
            |
            v
Package and Deploy Lambda
            |
            v
Invoke Function
            |
            v
ZeroDivisionError
            |
            v
Inspect Invocation Response
            |
            v
Investigate CloudWatch Logs
            |
            v
Identify Root Cause
            |
            v
Fix Python Application Code
            |
            v
Redeploy Lambda
            |
            v
Verify Successful Execution
            |
            v
Test Invalid Input Handling
            |
            v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-001 |
| Lab Name | AWS Lambda Runtime Error |
| Difficulty | Beginner |
| Primary AWS Service | AWS Lambda |
| Supporting Services | IAM, CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Programming Language | Python |
| Lambda Runtime | Python 3.13 |
| Function Name | `lambda-lab01-runtime-error` |
| Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Timeout | 10 seconds |
| Architecture | x86_64 |
| Execution Role | `lambda-lab01-execution-role` |
| CloudWatch Log Group | `/aws/lambda/lambda-lab01-runtime-error` |
| CloudWatch Retention | 7 days |
| Initial Fault | Division by zero |
| Expected Exception | `ZeroDivisionError` |
| Invocation Error | `FunctionError=Unhandled` |
| Root Cause | Missing divisor validation |
| Remediation | Input validation and safe division |
| Recovery Verification | Successful Lambda invocation |
| Cleanup | Lambda, IAM role, and log group |

### Lab Objectives

- Understand AWS Lambda runtime errors.
- Create a Lambda function using AWS CLI.
- Configure an IAM execution role.
- Understand Lambda trust policies.
- Attach CloudWatch logging permissions.
- Create and configure CloudWatch log groups.
- Package Python code into a ZIP archive.
- Deploy a Python Lambda function.
- Reproduce an unhandled Python exception.
- Understand the Lambda Invoke API response.
- Investigate `FunctionError`.
- Analyze CloudWatch runtime logs.
- Read Python stack traces.
- Identify the exact failing code.
- Correct application logic.
- Redeploy Lambda using AWS CLI.
- Test successful execution.
- Handle invalid input safely.
- Verify recovery using real invocation results.
- Delete temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company uses AWS Lambda to process application requests.

One Lambda function performs a simple calculation and returns the result to another application.

The engineering team successfully deploys a new version of the function.

AWS reports that the function is active and ready to receive requests.

However, when the application invokes the function, execution fails.

The Lambda Invoke API returns a successful invocation status, but the function response contains an error.

The application does not receive the expected calculation result.

The Cloud Engineering team investigates the incident.

The engineer reviews the Lambda configuration and confirms that the function has the correct handler, runtime, memory, and timeout settings.

The engineer then invokes the function using AWS CLI and examines the response payload.

The response identifies a Python `ZeroDivisionError`.

Further investigation in CloudWatch Logs reveals a stack trace pointing to the division operation.

The application's code contains:

```python
number = 100
divisor = 0

result = number / divisor
```

Python raises an exception because division by zero is not allowed.

The engineer determines that the problem is caused by missing application input validation.

The function is corrected, packaged, and redeployed.

After remediation, the application returns the expected result and handles invalid divisors without crashing.

### Incident Symptoms

- Lambda function successfully deployed.
- Function state is `Active`.
- Handler configuration is correct.
- AWS CLI invocation completes.
- `StatusCode=200` is returned by the Invoke API.
- `FunctionError=Unhandled` appears in the invocation metadata.
- Function payload contains `ZeroDivisionError`.
- CloudWatch Logs show a Python traceback.
- The application does not return its expected result.

### Business Impact

Runtime errors in production Lambda applications may cause:

- Failed API requests.
- Interrupted serverless workflows.
- Failed background jobs.
- Incomplete event processing.
- Increased application error rates.
- Delays in automated business operations.
- Unsuccessful downstream integrations.
- Operational incidents requiring investigation.

### Objective

Identify the unhandled Python exception, determine its root cause, correct the function, and confirm successful execution through AWS CLI and CloudWatch Logs.

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
          lambda-lab01-runtime-error
                     |
                     v
             Python 3.13 Runtime
                     |
                     v
                Lambda Handler
                     |
                     v
                 number = 100
                 divisor = 0
                     |
                     v
             result = number / divisor
                     |
                     v
               ZeroDivisionError
                     |
          +----------+----------+
          |                     |
          v                     v
   FunctionError=Unhandled   CloudWatch Logs
          |                     |
          v                     v
    Failed Execution       Python Traceback
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
          lambda-lab01-runtime-error
                     |
                     v
             Python 3.13 Runtime
                     |
                     v
                Lambda Handler
                     |
                     v
              Input Validation
                     |
          +----------+----------+
          |                     |
          v                     v
     Valid Input           Invalid Divisor
          |                     |
          v                     v
    Safe Calculation       Controlled Error
          |                     |
          v                     v
     statusCode 200         statusCode 400
          |                     |
          +----------+----------+
                     |
                     v
            Successful Execution
                     |
                     v
               CloudWatch Logs
```

### Architecture Components

| Component | Purpose |
|---|---|
| AWS Lambda | Executes Python application code |
| Lambda Handler | Entry point for function execution |
| Lambda Runtime | Provides the Python execution environment |
| IAM Execution Role | Provides AWS permissions to the function |
| IAM Trust Policy | Allows the Lambda service to assume the role |
| CloudWatch Logs | Stores application logs and runtime errors |
| AWS CLI | Deploys, invokes, and investigates the function |
| Python | Implements application logic and validation |
| ZIP Deployment | Packages application code |
| Bash | Automates deployment and investigation |

---

## 4. Understanding AWS Lambda Runtime Errors

### What Is an AWS Lambda Runtime Error?

A runtime error occurs when a function encounters a problem while executing.

Examples include:

```text
ZeroDivisionError
TypeError
ValueError
KeyError
IndexError
AttributeError
```

Some errors happen after the handler starts, while others can occur during application initialization.

### What Is ZeroDivisionError?

`ZeroDivisionError` is a Python exception raised when code attempts to divide a number by zero.

Example:

```python
result = 100 / 0
```

### What Is a Lambda Handler?

The Lambda handler is the function that AWS Lambda invokes when an event is received.

Example:

```python
def lambda_handler(event, context):
    return {
        "statusCode": 200
    }
```

Our handler configuration is:

```text
lambda_function.lambda_handler
```

The first part identifies the Python module.

The second part identifies the function.

### What Is FunctionError?

`FunctionError` is a field in the Lambda Invoke API response that indicates a function execution error.

For this incident:

```text
FunctionError = Unhandled
```

### Why Can StatusCode Be 200 During an Error?

A synchronous Lambda Invoke API request can succeed even when the function code fails.

For example:

```text
StatusCode = 200
FunctionError = Unhandled
```

The status code describes the invocation API request, while `FunctionError` reports an execution problem.

### What Is CloudWatch Logs?

Amazon CloudWatch Logs stores application and runtime log events.

Lambda functions can send print statements and errors to CloudWatch using their execution role.

### What Is a Stack Trace?

A stack trace shows the path of execution leading to an exception.

It helps engineers identify the file, function, and line where an error occurred.

### What Is an Unhandled Exception?

An exception that is not caught or handled by application code.

When an unhandled exception occurs, the function invocation fails rather than returning its normal application response.

### What Is a Controlled Validation Error?

A controlled validation error occurs when the application identifies invalid input and returns a structured response.

For example:

```json
{
  "statusCode": 400
}
```

For a direct Lambda invocation, this is an application-defined status value inside the response payload.

It does not change the Lambda Invoke API HTTP status.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Bash.
- Python 3.
- ZIP and unzip utilities.
- IAM role creation permissions.
- Lambda management permissions.
- CloudWatch Logs permissions.
- Git and GitHub.

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
lambda:UpdateFunctionCode
lambda:DeleteFunction
lambda:ListTags

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

### Safety Rules

- Use a dedicated Lambda function.
- Never modify production functions.
- Use a dedicated IAM execution role.
- Avoid unnecessary wildcard permissions.
- Do not log credentials or secrets.
- Keep generated response and evidence files private.
- Verify resource ownership before cleanup.
- Delete the dedicated CloudWatch log group after testing.
- Do not delete shared CloudWatch or IAM resources.

### Cost Considerations

This lab uses a small Python Lambda function with short execution time.

Potential charges include Lambda requests, execution duration, and CloudWatch log ingestion or storage.

No EC2 instances, RDS databases, NAT Gateways, or S3 buckets are required.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Navigate to the Repository

```bash
cd ~/aws-lambda-troubleshooting-labs
```

### Step 2 — Create the Lab Directory

```bash
mkdir -p 01-lambda-runtime-error

cd 01-lambda-runtime-error
```

### Step 3 — Verify Tools

```bash
aws --version
python3 --version
zip -v
```

If ZIP is missing:

```bash
sudo apt update

sudo apt install -y zip unzip
```

### Step 4 — Verify AWS Credentials

```bash
aws sts get-caller-identity
```

### Step 5 — Configure Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab01"

export FUNCTION_NAME="lambda-lab01-runtime-error"

export ROLE_NAME="lambda-lab01-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export RUNTIME="python3.13"
```

### Step 6 — Verify Variables

```bash
echo "$AWS_REGION"
echo "$FUNCTION_NAME"
echo "$ROLE_NAME"
echo "$LOG_GROUP"
echo "$RUNTIME"
```

### Step 7 — Save Resource Identifiers

```bash
cat > lab01-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export RUNTIME="$RUNTIME"
EOF
```

Restore variables using:

```bash
source lab01-resources.env
```

### Step 8 — Check Existing Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

If either resource already exists, verify ownership before using its name.

---

## 7. Create the Lambda IAM Execution Role

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

### Step 2 — Verify the JSON File

```bash
python3 -m json.tool lambda-trust-policy.json
```

### Step 3 — Create the Execution Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Execution role for AWS Lambda troubleshooting Lab 01" \
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
  --query 'Role.{Name:RoleName,Arn:Arn,Created:CreateDate}' \
  --output json
```

### Step 6 — Verify Attached Permissions

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected managed policy:

```text
AWSLambdaBasicExecutionRole
```

### Understanding the Role

The execution role allows the Lambda function to publish runtime logs to CloudWatch.

It does not need permission to access unrelated AWS resources in this lab.

---

## 8. Configure CloudWatch Logs

### Step 1 — Create a Dedicated Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION" \
  --tags "Project=$PROJECT_TAG"
```

### Step 2 — Configure Log Retention

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

### Why Configure Log Retention?

CloudWatch log retention controls how long the log data is kept.

Using a short retention period helps reduce unnecessary storage for temporary troubleshooting environments.

---

## 9. Create the Broken Python Lambda Function

### Step 1 — Create Application Code

Save as `lambda_function.py`:

```python
import json


def lambda_handler(event, context):
    print("Lambda Lab 01 started")

    number = 100
    divisor = 0

    print(f"Number: {number}")
    print(f"Divisor: {divisor}")

    result = number / divisor

    return {
        "statusCode": 200,
        "body": json.dumps({
            "result": result
        })
    }
```

### Step 2 — Understand the Fault

The problem is:

```python
result = number / divisor
```

Because:

```python
divisor = 0
```

The operation raises:

```text
ZeroDivisionError: division by zero
```

### Step 3 — Package the Function

```bash
zip function-broken.zip lambda_function.py
```

### Step 4 — Inspect the ZIP

```bash
unzip -l function-broken.zip
```

Expected:

```text
lambda_function.py
```

The Python module is stored at the root of the ZIP, matching the configured Lambda handler.

### Expected Behavior

The function will deploy successfully.

However, it will fail when invoked because the handler attempts division by zero.

---

## 10. Deploy the Broken Lambda Function

### Step 1 — Create the Lambda Function

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function-broken.zip \
  --timeout 10 \
  --memory-size 128 \
  --architectures x86_64 \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

New IAM roles may need time to propagate before Lambda can assume them.

If function creation fails because the role cannot be assumed, inspect the trust policy and retry after propagation.

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Inspect Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,Runtime:Runtime,Handler:Handler,State:State,LastUpdateStatus:LastUpdateStatus,Timeout:Timeout,Memory:MemorySize,Role:Role}' \
  --output json \
  --region "$AWS_REGION"
```

### Expected Configuration

| Property | Expected |
|---|---|
| State | Active |
| Runtime | python3.13 |
| Handler | lambda_function.lambda_handler |
| Timeout | 10 |
| MemorySize | 128 |
| Architecture | x86_64 |
| Execution Role | Dedicated Lab 01 role |

### Deployment Finding

The function can be active even though the application code contains a runtime error.

Deployment success does not guarantee successful execution.

---

<WritingBlock id="58322" variant="document">## 11. Fault Injection — Reproduce the Runtime Error

### Step 1 — Invoke the Broken Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  --log-type Tail \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab01-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab01-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

Additional fields such as `ExecutedVersion` and `LogResult` may be present.

### Step 3 — Inspect the Error Payload

```bash
python3 -m json.tool broken-response.json
```

Expected structure:

```json
{
  "errorMessage": "division by zero",
  "errorType": "ZeroDivisionError",
  "requestId": "ACTUAL_REQUEST_ID",
  "stackTrace": [
    "..."
  ]
}
```

The actual request ID and stack trace depend on the execution.

### Step 4 — Extract Error Details

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

Expected:

```text
Error type: ZeroDivisionError
Error message: division by zero
```

### Step 5 — Decode Lambda LogResult

```bash
python3 - <<'PY'
import base64
import json

with open("lab01-broken-invocation.json") as file:
    invocation = json.load(file)

encoded = invocation.get("LogResult")

if encoded:
    decoded = base64.b64decode(encoded).decode(
        "utf-8",
        errors="replace"
    )
    print(decoded)
else:
    print("No inline log excerpt returned")
PY
```

The `LogResult` field contains a Base64-encoded excerpt of the execution logs when `--log-type Tail` is used.

### Why StatusCode 200 Is Important

For synchronous Lambda invocation:

```text
StatusCode = 200
```

means the Lambda Invoke API request was accepted and processed.

It does not mean the application code succeeded.

The function can still return:

```text
FunctionError = Unhandled
```

### Broken-State Verification

| Check | Expected |
|---|---|
| Function deployed | Yes |
| Function active | Yes |
| Invocation API status | 200 |
| FunctionError | Unhandled |
| Exception | ZeroDivisionError |
| Error message | division by zero |
| Calculation result | Not returned |

---

## 12. Investigate CloudWatch Logs

### Step 1 — Read Recent Lambda Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected log content resembles:

```text
Lambda Lab 01 started
Number: 100
Divisor: 0

[ERROR] ZeroDivisionError: division by zero
Traceback (most recent call last):
...
```

The exact formatting depends on the Lambda runtime.

### Step 2 — Filter for ZeroDivisionError

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"ZeroDivisionError"' \
  --query 'events[].{Time:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search for the Divisor Log

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Divisor:"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Step 4 — Save Broken-State Logs

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab01-broken-cloudwatch-evidence.json
```

### Step 5 — Save Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab01-broken-function-configuration.json
```

### Step 6 — Inspect the Source Code with Line Numbers

```bash
nl -ba lambda_function.py
```

Identify the line containing:

```python
result = number / divisor
```

### Investigation Findings

| Evidence | Finding |
|---|---|
| Lambda initialization | Successful |
| Handler execution | Started |
| Numerator | 100 |
| Divisor | 0 |
| Python exception | ZeroDivisionError |
| Exception type | Unhandled |
| Failure location | Division operation |
| Error evidence | Invocation response and CloudWatch |
| Root cause | Missing input validation |

### CloudWatch Troubleshooting Lesson

CloudWatch Logs helps distinguish application errors from service configuration problems.

For this incident, the logs show that the Python handler began execution and failed while performing a calculation.

The evidence points to the application code rather than a Lambda service outage.

---

## 13. Root Cause Analysis

### Root Cause

The Lambda handler attempted to divide a number by zero.

The application code contained:

```python
number = 100
divisor = 0

result = number / divisor
```

Python raised a `ZeroDivisionError` because the divisor was zero.

The application did not validate the divisor before performing the calculation.

The exception was unhandled and caused the Lambda execution to fail.

### Root Cause Flow

```text
Lambda Function Invoked
          |
          v
Python Handler Starts
          |
          v
number = 100
          |
          v
divisor = 0
          |
          v
Division Operation
          |
          v
ZeroDivisionError
          |
          v
Unhandled Exception
          |
          v
FunctionError = Unhandled
          |
          v
CloudWatch Error Logs
```

### Five Whys

**Why 1 — Why did Lambda fail?**

The handler raised a Python exception.

**Why 2 — Why did the handler raise an exception?**

The code attempted division by zero.

**Why 3 — Why did the invalid calculation occur?**

The application used a zero divisor without validating it.

**Why 4 — Why did the entire invocation fail?**

The application did not handle the exception or return a controlled validation response.

**Why 5 — How can the problem be prevented?**

Validate input values before calculations and test invalid input cases before deployment.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-001 |
| Service | AWS Lambda |
| Application | Python |
| Runtime | Python 3.13 |
| Fault | Division by zero |
| Exception | ZeroDivisionError |
| Invocation error | Unhandled |
| Root cause | Missing divisor validation |
| Remediation | Safe input validation |
| Verification | Successful calculation and graceful invalid-input handling |

---

## 14. Remediation — Correct the Python Function

### Step 1 — Preserve the Broken Source

```bash
cp lambda_function.py lambda_function_broken.py
```

### Step 2 — Replace the Lambda Handler

Save the corrected version as `lambda_function.py`:

```python
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
```

### Understanding the Fix

The corrected function reads the numerator and divisor from the invocation event.

If the event omits them, the function uses default values.

The handler first checks whether the inputs are numeric.

It then checks whether the divisor equals zero.

If the divisor is zero, the function returns:

```json
{
  "statusCode": 400,
  "body": "{\"error\": \"Divisor cannot be zero\"}"
}
```

This is an application-defined validation response.

The function does not raise an unhandled exception for this input.

For a valid divisor, the function performs the calculation and returns a successful result.

### Step 3 — Package Corrected Code

```bash
zip -j function-fixed.zip lambda_function.py
```

### Step 4 — Inspect ZIP Contents

```bash
unzip -l function-fixed.zip
```

Expected:

```text
lambda_function.py
```

### Step 5 — Redeploy Lambda

```bash
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://function-fixed.zip \
  --region "$AWS_REGION"
```

### Step 6 — Wait for Code Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 7 — Verify the Updated Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,LastUpdateStatus:LastUpdateStatus,Runtime:Runtime,Handler:Handler}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
LastUpdateStatus = Successful
```

### Remediation Summary

| Item | Before | After |
|---|---|---|
| Input handling | No validation | Numeric validation |
| Divisor handling | Divides by zero | Rejects zero |
| Error handling | Unhandled exception | Controlled response |
| Calculation | Fails | Succeeds |
| Deployment | Active | Active |

---

## 15. Verify Lambda Recovery

### Step 1 — Create a Healthy Test Event

Save as `healthy-event.json`:

```json
{
  "number": 100,
  "divisor": 2
}
```

### Step 2 — Invoke the Corrected Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://healthy-event.json \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab01-healthy-invocation.json
```

### Step 3 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab01-healthy-invocation.json
```

Expected:

```json
{
  "StatusCode": 200
}
```

There should be no `FunctionError`.

### Step 4 — Inspect Application Response

```bash
python3 -m json.tool healthy-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"result\": 50.0}"
}
```

### Step 5 — Verify Successful Calculation

```bash
python3 - <<'PY'
import json

with open("lab01-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["result"] == 50.0

print("SUCCESS: Lambda runtime error resolved")
PY
```

Expected:

```text
SUCCESS: Lambda runtime error resolved
```

### Step 6 — Create Invalid Test Event

Save as `invalid-event.json`:

```json
{
  "number": 100,
  "divisor": 0
}
```

### Step 7 — Invoke with Invalid Input

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://invalid-event.json \
  --region "$AWS_REGION" \
  invalid-response.json \
  > lab01-invalid-input-invocation.json
```

### Step 8 — Inspect Invalid Input Response

```bash
python3 -m json.tool invalid-response.json
```

Expected:

```json
{
  "statusCode": 400,
  "body": "{\"error\": \"Divisor cannot be zero\"}"
}
```

### Step 9 — Verify Graceful Error Handling

```bash
python3 - <<'PY'
import json

with open("lab01-invalid-input-invocation.json") as file:
    invocation = json.load(file)

with open("invalid-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 400
assert body["error"] == "Divisor cannot be zero"

print("SUCCESS: Invalid divisor handled safely")
PY
```

### Step 10 — Inspect Recovery Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Calculated result: 50.0
```

### Step 11 — Save Recovery Log Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Calculated result:"' \
  --output json \
  --region "$AWS_REGION" \
  > lab01-recovery-cloudwatch-evidence.json
```

### Before and After Verification

| Investigation | Broken | Recovered |
|---|---|---|
| Function deployed | Yes | Yes |
| Function state | Active | Active |
| Invocation API status | 200 | 200 |
| FunctionError | Unhandled | Absent |
| Runtime exception | ZeroDivisionError | None for tested cases |
| Calculation | Failed | 50.0 |
| Invalid input | Crashes | Controlled 400 |
| CloudWatch evidence | Error traceback | Successful calculation |
| Incident state | Failure | Verified recovery |

**Recovery is confirmed when the corrected Lambda returns the expected calculation, the invocation has no `FunctionError`, and invalid input is handled without an unhandled exception.**

---

## 16. Other AWS Lambda Runtime Troubleshooting Scenarios

### Scenario A — TypeError

The application attempts an operation using incompatible data types.

Example:

```python
result = "10" + 5
```

Troubleshooting:

- Inspect the exception.
- Identify the operands.
- Validate or convert data types.
- Test corrected execution.

### Scenario B — KeyError

The function attempts to access a missing dictionary key.

Example:

```python
username = event["username"]
```

If the event does not contain `username`, Python raises a `KeyError`.

Troubleshooting:

- Inspect the event structure.
- Validate required input.
- Use safe dictionary access where appropriate.

### Scenario C — IndexError

The function accesses an invalid list index.

Example:

```python
items = [1, 2, 3]
value = items[10]
```

Troubleshooting:

- Inspect list length.
- Check index boundaries.
- Handle empty or incomplete data.

### Scenario D — AttributeError

The function attempts to access an attribute or method that does not exist on an object.

Troubleshooting:

- Inspect object type.
- Verify method names.
- Validate inputs and returned objects.

### Scenario E — Unexpected Null Value

The application assumes a value exists, but receives `None`.

Troubleshooting:

- Validate external data.
- Handle missing values.
- Return controlled application errors.

### Runtime Error Matrix

| Error | Common Cause | Investigation |
|---|---|---|
| ZeroDivisionError | Division by zero | Stack trace and divisor |
| TypeError | Invalid operand types | Input types |
| KeyError | Missing dictionary key | Event payload |
| IndexError | Invalid list index | List boundaries |
| AttributeError | Invalid object attribute | Object type |
| ValueError | Invalid value | Input validation |
| Runtime.ImportModuleError | Missing module or initialization failure | Dependencies and packaging |

---

## 17. Production Troubleshooting Best Practices

### Investigation Checklist

1. Verify AWS account and Region.
2. Identify the failing Lambda function.
3. Inspect function state.
4. Confirm runtime and handler.
5. Reproduce the error with a known payload.
6. Check the Invoke API response.
7. Inspect `FunctionError`.
8. Review the returned error payload.
9. Retrieve the CloudWatch logs.
10. Find the error type and message.
11. Identify the failing code line.
12. Determine the root cause.
13. Apply input validation or correct logic.
14. Package and redeploy the code.
15. Verify successful execution.
16. Test the original failure condition.
17. Review CloudWatch recovery logs.
18. Save investigation evidence.
19. Document the incident.
20. Clean up temporary resources.

### Production Investigation Flow

```text
Lambda Invocation Failure
            |
            v
Verify Function State
            |
            v
Inspect Invocation Metadata
            |
            v
Check FunctionError
            |
            v
Read Error Payload
            |
            v
Inspect CloudWatch Logs
            |
            v
Locate Python Traceback
            |
            v
Identify Failing Line
            |
            v
Determine Root Cause
            |
            v
Correct Application Code
            |
            v
Redeploy Lambda
            |
            v
Repeat Invocation
            |
            v
Verify Successful Execution
```

### Production Recommendations

- Validate external inputs.
- Handle expected application errors.
- Avoid broad exception handling that hides real failures.
- Include useful but non-sensitive diagnostic logs.
- Use CloudWatch metrics to monitor error rates.
- Correlate logs using invocation request IDs.
- Test edge cases before deployment.
- Use automated unit tests.
- Use code reviews and deployment pipelines.
- Maintain deployment rollback procedures.
- Configure appropriate CloudWatch log retention.
- Apply least-privilege execution role permissions.

### Security Considerations

Do not include API keys, passwords, tokens, or customer-sensitive data in Lambda logs.

Avoid returning detailed internal stack traces to application clients.

Use structured error handling for expected failures and logging for unexpected exceptions.

---

## 18. AWS Resource Cleanup

**Warning:** Delete only the resources created for Lab 01.

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
Project=Lambda-Troubleshooting-Lab01
```

### Step 2 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Delete Lambda Function

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 4 — Verify Function Deletion

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
ResourceNotFoundException
```

### Step 5 — Detach CloudWatch Logging Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 6 — Delete IAM Execution Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 7 — Verify Role Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 8 — Verify Log Group Name

```bash
echo "$LOG_GROUP"
```

Expected:

```text
/aws/lambda/lambda-lab01-runtime-error
```

### Step 9 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 10 — Verify Log Group Removal

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query 'logGroups[].logGroupName' \
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
| Dedicated IAM role | Deleted |
| IAM logging policy association | Detached |
| CloudWatch log group | Deleted |
| EC2 | None created |
| RDS | None created |
| VPC | None created |
| S3 bucket | None created |

---

## 19. Interview Questions and Answers

### Q1. What is a Lambda runtime error?

An error that occurs during the execution of Lambda application code, such as an unhandled exception.

### Q2. Can Lambda deploy successfully but fail during invocation?

Yes. Deployment success does not guarantee that the function logic works.

### Q3. What does `FunctionError=Unhandled` mean?

The Lambda function encountered an unhandled execution error.

### Q4. Why can StatusCode 200 appear even when Lambda fails?

It means the synchronous Invoke API request succeeded. It does not guarantee that the application returned a successful result.

### Q5. What is ZeroDivisionError?

A Python exception raised when an application attempts division by zero.

### Q6. Where do you investigate Lambda runtime errors?

In the invocation response, error payload, and CloudWatch Logs.

### Q7. What is a Python traceback?

A record showing the call sequence and code location associated with an exception.

### Q8. What is the purpose of the Lambda execution role?

It provides AWS permissions needed by the function during execution.

### Q9. Why does Lambda need CloudWatch logging permissions?

To publish application and runtime logs.

### Q10. How do you inspect Lambda logs using AWS CLI?

```bash
aws logs tail "/aws/lambda/FUNCTION_NAME" \
  --since 10m \
  --region us-east-1
```

### Q11. What is the difference between a runtime exception and a controlled error response?

A runtime exception may fail the invocation. A controlled response is deliberately returned by the application for an expected condition.

### Q12. How do you fix ZeroDivisionError?

Validate the divisor before performing division and handle invalid input safely.

### Q13. How do you redeploy a Lambda function using AWS CLI?

Use `aws lambda update-function-code` with the corrected deployment package.

### Q14. How do you verify recovery?

Invoke the corrected function, inspect the metadata and payload, and confirm successful execution in CloudWatch.

### Q15. Why should you test invalid input after remediation?

To verify that the original failure condition is handled correctly and does not cause the same unhandled exception.

### Q16. Does raising Lambda memory automatically fix a Python logic error?

No. Increasing memory does not correct invalid application logic.

### Q17. Does increasing the timeout fix ZeroDivisionError?

No. The exception occurs because of the calculation, not because execution exceeds its time limit.

### Q18. What is a good production troubleshooting sequence?

Reproduce the problem, collect logs, identify the failing code, determine the root cause, fix the problem, and verify recovery.

### Q19. Why is CloudWatch important for Lambda troubleshooting?

It provides application logs, runtime errors, and operational data used to investigate execution problems.

### Q20. How would you explain this lab in an interview?

I created a dedicated Python Lambda function using AWS CLI and configured an IAM execution role with CloudWatch logging permissions.

I intentionally introduced a division-by-zero bug and deployed the function.

The deployment was successful, but the function failed during invocation.

I checked the AWS CLI response and observed `FunctionError=Unhandled`.

I inspected the error payload and CloudWatch Logs, which showed a Python `ZeroDivisionError`.

The stack trace identified the division operation as the failing line.

I fixed the application by validating the inputs and preventing division by zero.

I redeployed the function and invoked it using a valid test event.

The function returned the expected calculation result without an unhandled error.

I also tested a zero divisor and verified that the function returned a controlled validation response instead of crashing.

Finally, I removed the Lambda function, IAM role, and CloudWatch log group.

---

## 20. Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
│
├── 01-lambda-runtime-error/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda_function_broken.py
│   ├── lambda-trust-policy.json
│   ├── function-broken.zip
│   ├── function-fixed.zip
│   ├── lab01-resources.env
│   ├── healthy-event.json
│   ├── invalid-event.json
│   ├── broken-response.json
│   ├── healthy-response.json
│   ├── invalid-response.json
│   ├── lab01-broken-invocation.json
│   ├── lab01-healthy-invocation.json
│   ├── lab01-invalid-input-invocation.json
│   ├── lab01-broken-cloudwatch-evidence.json
│   ├── lab01-broken-function-configuration.json
│   └── lab01-recovery-cloudwatch-evidence.json
│
├── 02-handler-not-found/
├── 03-lambda-timeout/
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
| `README.md` | Complete production incident documentation |
| `lambda_function.py` | Corrected Lambda handler |
| `lambda_function_broken.py` | Original faulty handler |
| `lambda-trust-policy.json` | Lambda execution role trust policy |
| `function-broken.zip` | Original deployment package |
| `function-fixed.zip` | Corrected deployment package |
| `lab01-resources.env` | Local AWS resource identifiers |
| `healthy-event.json` | Valid test event |
| `invalid-event.json` | Zero-divisor test event |
| `broken-response.json` | Actual error payload |
| `healthy-response.json` | Successful invocation payload |
| `invalid-response.json` | Controlled validation response |
| `lab01-broken-invocation.json` | Initial Lambda API metadata |
| `lab01-healthy-invocation.json` | Recovery invocation metadata |
| `lab01-invalid-input-invocation.json` | Validation test metadata |
| `lab01-broken-cloudwatch-evidence.json` | Original error logs |
| `lab01-broken-function-configuration.json` | Original function settings |
| `lab01-recovery-cloudwatch-evidence.json` | Successful execution logs |

### Recommended GitHub Files

Commit:

```text
README.md
lambda_function.py
lambda_function_broken.py
lambda-trust-policy.json
healthy-event.json
invalid-event.json
```

Keep locally or review before publishing:

```text
function-broken.zip
function-fixed.zip
lab01-resources.env
*-response.json
lab01-*-invocation.json
lab01-*-evidence.json
lab01-broken-function-configuration.json
```

### Recommended .gitignore

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Generated Lambda packages
*.zip

# Local AWS resources
**/lab01-resources.env

# Invocation responses
**/*-response.json
**/lab01-*-invocation.json

# Raw CloudWatch and configuration evidence
**/lab01-*-evidence.json
**/lab01-broken-function-configuration.json

# Credentials
.env
.env.*
*.pem
*.key
```

Review all files before committing them to a public GitHub repository.

---

## 21. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how an AWS Lambda function can be deployed successfully but fail during application execution.

We created a dedicated Lambda execution role and configured CloudWatch logging.

We deployed a Python Lambda function with an intentional division-by-zero bug.

The function entered the Active state, but invocation failed with an unhandled exception.

We investigated the AWS CLI invocation response and identified `FunctionError=Unhandled`.

We examined the Python error payload and CloudWatch Logs to determine the exact failure.

The root cause was missing divisor validation in the application code.

We corrected the handler, redeployed the function, and verified that it returned the expected calculation result.

We also tested invalid input to confirm the function could reject a zero divisor without crashing.

Finally, we removed the temporary Lambda function, IAM execution role, and CloudWatch log group.

**Key Lesson:** A successful Lambda deployment or Invoke API response does not guarantee successful application execution. Engineers must inspect the function result, error information, and CloudWatch Logs to determine the actual outcome.

### Skills Demonstrated

- AWS Lambda
- Python 3.13
- Lambda handler configuration
- Lambda execution roles
- IAM trust policies
- AWSLambdaBasicExecutionRole
- AWS CLI v2
- Linux Bash
- ZIP deployment packages
- Lambda Invoke API
- FunctionError investigation
- Python ZeroDivisionError
- Python traceback analysis
- Amazon CloudWatch Logs
- CloudWatch log filtering
- Root cause analysis
- Input validation
- Application error handling
- Lambda code deployment
- Recovery verification
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-001 |
| Scenario | Lambda Runtime Error |
| Function | lambda-lab01-runtime-error |
| Region | us-east-1 |
| Runtime | Python 3.13 |
| Broken Exception | ZeroDivisionError |
| Broken FunctionError | Unhandled |
| Root Cause | Missing divisor validation |
| Remediation | Validate numeric inputs and divisor |
| Healthy Result | 50.0 |
| Invalid Input | Controlled 400 response |
| CloudWatch Investigation | Runtime error identified |
| Recovery | Verified after successful invocation |
| Cleanup | Lambda, IAM role, and logs deleted |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** Production Lambda troubleshooting requires examining both AWS service-level invocation results and application-level execution behavior. CloudWatch evidence and repeatable validation are essential for proving that a runtime error has been fixed.

---

## Official AWS Documentation

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)
- [Troubleshooting Lambda Execution](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)
- [AWS Lambda Python Handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [AWS Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [Sending Lambda Logs to CloudWatch](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS CLI — Lambda Invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)
- [AWS CLI — UpdateFunctionCode](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)