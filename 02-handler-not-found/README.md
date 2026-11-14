# Lab 02 — AWS Lambda Handler Not Found

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda `Runtime.HandlerNotFound` error using AWS CLI, Python, Linux Bash, and Amazon CloudWatch Logs.

AWS Lambda functions require a handler configuration that identifies the application entry point.

For Python Lambda functions, the handler setting contains the Python module name followed by the function name.

A Lambda deployment can complete successfully while referencing an incorrect handler. The issue becomes visible when Lambda attempts to initialize the function.

In this lab, we deploy a Python Lambda application with valid source code but an intentionally incorrect handler configuration.

The Python module contains a function named `lambda_handler`, but AWS Lambda is configured to invoke a nonexistent function named `process_event`.

When the function is invoked, Lambda raises `Runtime.HandlerNotFound`.

We investigate the invocation response, CloudWatch logs, deployment ZIP, and Lambda configuration to identify the mismatch.

After confirming the root cause, we correct the handler configuration using AWS CLI without modifying or redeploying the Python code.

We then invoke the function again and verify successful execution.

An optional exercise demonstrates how a missing Python module causes `Runtime.ImportModuleError`, which differs from a missing handler function.

Finally, we delete the temporary AWS resources and document the investigation.

### Troubleshooting Workflow

```text
Create Lambda Execution Role
            |
            v
Configure CloudWatch Logs
            |
            v
Write Valid Python Handler
            |
            v
Package Deployment ZIP
            |
            v
Deploy Lambda with Wrong Handler
            |
            v
Invoke Lambda Function
            |
            v
Runtime.HandlerNotFound
            |
            v
Inspect Invocation Response
            |
            v
Investigate CloudWatch Logs
            |
            v
Compare Handler and Python Source
            |
            v
Identify Configuration Mismatch
            |
            v
Update Lambda Handler Setting
            |
            v
Verify Configuration Update
            |
            v
Invoke Lambda Again
            |
            v
Successful Execution
            |
            v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-002 |
| Lab Name | Lambda Handler Not Found |
| Difficulty | Beginner |
| Primary AWS Service | AWS Lambda |
| Supporting Services | IAM, CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Programming Language | Python |
| Lambda Runtime | Python 3.13 |
| Function Name | `lambda-lab02-handler-not-found` |
| Execution Role | `lambda-lab02-execution-role` |
| CloudWatch Log Group | `/aws/lambda/lambda-lab02-handler-not-found` |
| Memory | 128 MB |
| Timeout | 10 seconds |
| Architecture | x86_64 |
| Broken Handler | `lambda_function.process_event` |
| Correct Handler | `lambda_function.lambda_handler` |
| Expected Error | `Runtime.HandlerNotFound` |
| Root Cause | Handler configuration mismatch |
| Remediation | Correct Lambda handler setting |
| Code Redeployment | Not required |
| Recovery Verification | Successful Lambda invocation |
| Cleanup | Lambda, IAM role, CloudWatch log group |

### Lab Objectives

- Understand Python Lambda handler configuration.
- Understand the difference between a module and a function.
- Create an IAM Lambda execution role.
- Configure CloudWatch logging.
- Package Python source code.
- Deploy a Lambda function using AWS CLI.
- Reproduce `Runtime.HandlerNotFound`.
- Inspect Lambda Invoke API responses.
- Analyze initialization errors in CloudWatch.
- Inspect deployment ZIP contents.
- Identify incorrect handler settings.
- Correct Lambda configuration without redeploying source code.
- Verify successful application execution.
- Understand the difference between `HandlerNotFound` and `ImportModuleError`.
- Perform root cause analysis.
- Safely clean up temporary resources.

---

## 2. Production Incident Scenario

### Incident Description

A company deploys a Python Lambda function that processes application events.

The application receives a name from an event payload, generates a greeting message, and returns a successful response.

The development team verifies the Python code and uploads a deployment package.

AWS Lambda reports that the function is active.

However, the application's first invocation fails.

The function does not return the expected response, and CloudWatch logs contain a `Runtime.HandlerNotFound` error.

The Cloud Engineering team investigates the incident.

The engineer checks the Lambda function's runtime, handler configuration, deployment package, and CloudWatch logs.

The deployed code contains:

```python
def lambda_handler(event, context):
```

But the Lambda configuration references:

```text
lambda_function.process_event
```

The `lambda_function` module exists in the deployment package, but there is no function named `process_event`.

Lambda fails before entering the actual application handler.

The engineer changes the handler setting to:

```text
lambda_function.lambda_handler
```

No application code changes are necessary.

After the configuration update, the function executes successfully and returns the expected message.

### Incident Symptoms

- Lambda deployment completes successfully.
- Function state is `Active`.
- Python source code is valid.
- Deployment ZIP contains `lambda_function.py`.
- Invocation returns a function error.
- CloudWatch reports `Runtime.HandlerNotFound`.
- Application print statements do not execute.
- Configured handler function is absent from the module.
- Correcting the handler resolves the failure.

### Business Impact

Handler configuration failures can cause:

- Failed application invocations.
- Broken serverless APIs.
- Failed background processing.
- Unavailable event handlers.
- Interrupted workflows.
- Delayed deployments.
- Application incidents immediately after releases.

### Objective

Identify the incorrect handler setting, distinguish it from a missing module or code exception, correct the configuration, and verify successful Lambda execution.

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
          lambda-lab02-handler-not-found
                         |
                         v
                Python 3.13 Runtime
                         |
                         v
                Handler Configuration
                         |
                         v
             lambda_function.process_event
                         |
                         v
              Import lambda_function.py
                         |
                         v
               Find process_event()
                         |
                         v
                 Function Missing
                         |
                         v
              Runtime.HandlerNotFound
                         |
                         v
                   CloudWatch Logs
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
          lambda-lab02-handler-not-found
                         |
                         v
                Python 3.13 Runtime
                         |
                         v
                Handler Configuration
                         |
                         v
             lambda_function.lambda_handler
                         |
                         v
              Import lambda_function.py
                         |
                         v
               Find lambda_handler()
                         |
                         v
               Execute Application
                         |
                         v
                 Generate Greeting
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
| AWS Lambda | Executes serverless Python code |
| Python Runtime | Loads the module and invokes its handler |
| Handler Configuration | Identifies the Python entry point |
| Deployment ZIP | Contains the application module |
| IAM Execution Role | Grants runtime permissions |
| IAM Trust Policy | Allows Lambda to assume the role |
| CloudWatch Logs | Records initialization errors and application output |
| AWS CLI | Deploys, invokes, and configures Lambda |
| Bash | Automates lab tasks |
| Python | Implements and verifies application behavior |

---

## 4. Understanding Lambda Handler Configuration

### What Is a Lambda Handler?

A Lambda handler is the application function AWS Lambda invokes to process an event.

Python example:

```python
def lambda_handler(event, context):
    return {"statusCode": 200}
```

### What Does `lambda_function.lambda_handler` Mean?

A Python Lambda handler is commonly configured using:

```text
MODULE_NAME.FUNCTION_NAME
```

For this lab:

```text
lambda_function.lambda_handler
```

- `lambda_function` is the Python module.
- `lambda_handler` is the function defined inside that module.

The deployment package contains:

```text
lambda_function.py
```

### What Is Runtime.HandlerNotFound?

`Runtime.HandlerNotFound` occurs when the runtime cannot find the configured handler in the imported module.

For example:

```text
Configured: lambda_function.process_event
Actual:     lambda_function.lambda_handler
```

### What Is Runtime.ImportModuleError?

`Runtime.ImportModuleError` typically occurs when Lambda cannot import the specified Python module or one of its required dependencies.

Example:

```text
nonexistent_module.lambda_handler
```

### HandlerNotFound vs. ImportModuleError

| Error | Typical Cause |
|---|---|
| Runtime.HandlerNotFound | Module imports, but configured handler is missing |
| Runtime.ImportModuleError | Module or dependency cannot be imported |
| ZeroDivisionError | Application handler performs invalid division |
| KeyError | Application accesses a missing dictionary key |

### Why Can Deployment Succeed with a Wrong Handler?

Lambda may accept a syntactically valid handler configuration during deployment.

The mismatch becomes apparent when the runtime attempts to resolve the handler during initialization or invocation.

### Does Fixing the Handler Require Code Redeployment?

Not when the correct handler already exists in the deployment package.

Updating the function configuration is sufficient.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Bash.
- Python 3.
- ZIP and unzip utilities.
- Permission to create IAM roles.
- Permission to create and update Lambda functions.
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
lambda:UpdateFunctionConfiguration
lambda:InvokeFunction
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
- Never modify production Lambda configurations.
- Create a dedicated IAM execution role.
- Use least-privilege permissions.
- Use a dedicated CloudWatch log group.
- Keep account-specific evidence private.
- Confirm resource ownership before cleanup.
- Do not delete shared IAM or CloudWatch resources.

### Cost Considerations

This lab uses a small Python Lambda function and CloudWatch Logs.

It does not require EC2, RDS, a NAT Gateway, or any VPC networking configuration.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create the Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 02-handler-not-found

cd 02-handler-not-found
```

### Step 2 — Verify Tools

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

export PROJECT_TAG="Lambda-Troubleshooting-Lab02"

export FUNCTION_NAME="lambda-lab02-handler-not-found"

export ROLE_NAME="lambda-lab02-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export RUNTIME="python3.13"

export BROKEN_HANDLER="lambda_function.process_event"

export CORRECT_HANDLER="lambda_function.lambda_handler"
```

### Step 5 — Save Variables

```bash
cat > lab02-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export RUNTIME="$RUNTIME"
export BROKEN_HANDLER="$BROKEN_HANDLER"
export CORRECT_HANDLER="$CORRECT_HANDLER"
EOF
```

Restore later using:

```bash
source lab02-resources.env
```

### Step 6 — Verify Existing Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected for a new lab: resource-not-found errors.

If a resource already exists, confirm ownership before modifying it.

---

## 7. Create the Lambda Execution Role

### Step 1 — Create the Trust Policy

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

### Step 2 — Verify the JSON

```bash
python3 -m json.tool lambda-trust-policy.json
```

### Step 3 — Create the IAM Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Temporary Lambda execution role for Lab 02" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 4 — Attach Logging Permissions

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 5 — Verify the Role

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

The role provides the basic permissions needed to publish logs.

No additional AWS service access is required by the example application.

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

### Step 3 — Verify Configuration

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query 'logGroups[].{Name:logGroupName,Retention:retentionInDays}' \
  --output table \
  --region "$AWS_REGION"
```

Expected: the dedicated log group exists with seven-day retention.

---

## 9. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
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
```

### Step 2 — Verify Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

source = Path("lambda_function.py").read_text()

ast.parse(source)

print("SUCCESS: Python syntax valid")
PY
```

### Step 3 — Verify Handler Names

```bash
python3 - <<'PY'
import lambda_function

print(
    "Correct handler exists:",
    hasattr(lambda_function, "lambda_handler")
)

print(
    "Broken handler exists:",
    hasattr(lambda_function, "process_event")
)
PY
```

Expected:

```text
Correct handler exists: True
Broken handler exists: False
```

### Step 4 — Package Deployment ZIP

```bash
zip function.zip lambda_function.py
```

### Step 5 — Inspect ZIP

```bash
unzip -l function.zip
```

Expected:

```text
lambda_function.py
```

### Finding

The deployed module and Python source code are valid.

The intentional fault will be introduced through the Lambda handler configuration, not through the application code.

---

## 10. Deploy Lambda with the Incorrect Handler

### Step 1 — Create the Lambda Function

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  --role "$ROLE_ARN" \
  --handler "$BROKEN_HANDLER" \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --memory-size 128 \
  --architectures x86_64 \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

The incorrect handler is:

```text
lambda_function.process_event
```

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

If Lambda cannot assume the execution role, verify the role trust policy and IAM propagation before retrying.

### Step 3 — Inspect Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,Runtime:Runtime,Handler:Handler,Role:Role,Timeout:Timeout,Memory:MemorySize}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Handler = lambda_function.process_event
Runtime = python3.13
```

### Step 4 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab02-broken-configuration.json
```

### Important Observation

Lambda can report an active function while its configured handler points to a nonexistent function.

---

<WritingBlock id="73185" variant="document">## 11. Fault Injection — Reproduce Runtime.HandlerNotFound

### Step 1 — Create the Test Event

Save as `test-event.json`:

```json
{
  "name": "Cloud Engineer"
}
```

### Step 2 — Invoke the Broken Lambda

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab02-broken-invocation.json
```

### Step 3 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab02-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

The response may also include `LogResult` and `ExecutedVersion`.

`StatusCode=200` means the synchronous Lambda Invoke API request succeeded. It does not indicate that the function code executed successfully.

### Step 4 — Inspect the Error Payload

```bash
python3 -m json.tool broken-response.json
```

Expected structure:

```json
{
  "errorMessage": "Handler 'process_event' missing on module 'lambda_function'",
  "errorType": "Runtime.HandlerNotFound"
}
```

The exact wording can vary by runtime.

### Step 5 — Extract the Error

```bash
python3 - <<'PY'
import json

with open("broken-response.json") as file:
    response = json.load(file)

print("Error type:", response.get("errorType"))
print("Error message:", response.get("errorMessage"))
PY
```

Expected:

```text
Error type: Runtime.HandlerNotFound
Error message: Handler 'process_event' missing on module 'lambda_function'
```

### Step 6 — Verify the Specific Failure

```bash
python3 - <<'PY'
import json

with open("lab02-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    payload = json.load(file)

assert invocation.get("StatusCode") == 200
assert invocation.get("FunctionError") is not None

assert payload.get("errorType") == \
    "Runtime.HandlerNotFound"

print("SUCCESS: HandlerNotFound reproduced")
PY
```

If the assertion fails, inspect the actual error. Do not assume the fault was reproduced if Lambda returned a different error.

### Step 7 — Decode Inline Execution Logs

```bash
python3 - <<'PY'
import base64
import json

with open("lab02-broken-invocation.json") as file:
    data = json.load(file)

encoded = data.get("LogResult")

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
| Deployment | Successful |
| Function state | Active |
| Python syntax | Valid |
| Module exists | Yes |
| Correct function exists | Yes |
| Configured function exists | No |
| Invoke API status | 200 |
| FunctionError | Present |
| Error type | Runtime.HandlerNotFound |
| Application message | Not returned |

---

## 12. Investigate CloudWatch Logs

### Step 1 — View Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected error resembles:

```text
[ERROR] Runtime.HandlerNotFound:
Handler 'process_event' missing on module 'lambda_function'
```

### Step 2 — Search for HandlerNotFound

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"HandlerNotFound"' \
  --query 'events[].{Time:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search for the Configured Function Name

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"process_event"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Step 4 — Save CloudWatch Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab02-broken-cloudwatch-evidence.json
```

### Step 5 — Inspect the Handler Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Handler:Handler,Runtime:Runtime,State:State}' \
  --output json \
  --region "$AWS_REGION"
```

Expected handler:

```text
lambda_function.process_event
```

### Step 6 — Inspect the Deployment Package

```bash
unzip -l function.zip
```

Expected:

```text
lambda_function.py
```

### Step 7 — Inspect Python Function Definitions

```bash
grep -n '^def ' lambda_function.py
```

Expected:

```text
def lambda_handler(event, context):
```

### Step 8 — Compare the Names

| Component | Configured | Present in Code |
|---|---|---|
| Python module | lambda_function | lambda_function |
| Python function | process_event | lambda_handler |
| Module matches | Yes | Yes |
| Function matches | No | No |

### Investigation Findings

The deployment package contains the correct Python module.

The source code defines `lambda_handler`.

The Lambda configuration references `process_event`, which does not exist.

The runtime cannot resolve the configured entry point.

The application handler does not execute, which explains why its expected print statements are absent from the failed invocation.

---

## 13. Root Cause Analysis

### Root Cause

The Lambda function was configured with an incorrect handler name.

The deployment package contained:

```python
def lambda_handler(event, context):
```

But the Lambda handler setting was:

```text
lambda_function.process_event
```

Because the `process_event` function did not exist in the module, Lambda raised `Runtime.HandlerNotFound`.

The Python source itself was valid.

No additional dependencies were missing.

The root cause was a configuration mismatch between the deployed code and the Lambda handler setting.

### Root Cause Diagram

```text
Lambda Invocation
        |
        v
Configured Handler
        |
        v
lambda_function.process_event
        |
        v
Import lambda_function.py
        |
        v
Resolve process_event
        |
        v
Function Does Not Exist
        |
        v
Runtime.HandlerNotFound
        |
        v
Function Execution Fails
```

### Five Whys

**Why 1 — Why did Lambda fail?**

The runtime could not locate the configured handler.

**Why 2 — Why could the handler not be located?**

The handler name referenced a function that did not exist.

**Why 3 — Why was the deployment package not the issue?**

The module was present and the correct function was defined in the Python file.

**Why 4 — Why did the function become Active?**

The incorrect handler string was accepted during deployment, and the problem surfaced when Lambda tried to resolve the handler.

**Why 5 — How can the issue be prevented?**

Validate handler configuration against the deployment package and perform test invocations after deployment.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-002 |
| AWS Service | Lambda |
| Runtime | Python 3.13 |
| Error | Runtime.HandlerNotFound |
| Configured Handler | lambda_function.process_event |
| Actual Handler | lambda_function.lambda_handler |
| Python Module | Present |
| Application Syntax | Valid |
| Root Cause | Incorrect handler configuration |
| Remediation | Update handler setting |
| Code Changes | Not required |
| ZIP Redeployment | Not required |

---

## 14. Remediation — Correct the Lambda Handler

### Step 1 — Update Handler Configuration

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --handler "$CORRECT_HANDLER" \
  --region "$AWS_REGION"
```

The corrected handler is:

```text
lambda_function.lambda_handler
```

### Step 2 — Wait for Configuration Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Updated Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Function:FunctionName,Handler:Handler,State:State,LastUpdateStatus:LastUpdateStatus,Runtime:Runtime}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Handler = lambda_function.lambda_handler
State = Active
LastUpdateStatus = Successful
```

### Step 4 — Save Recovered Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab02-recovered-configuration.json
```

### Remediation Comparison

| Property | Broken | Recovered |
|---|---|---|
| Runtime | python3.13 | python3.13 |
| Python module | lambda_function | lambda_function |
| Handler function | process_event | lambda_handler |
| Deployment package | function.zip | Same package |
| Execution role | Dedicated role | Same role |
| Application source | Valid | Unchanged |
| Function behavior | Initialization failure | Handler executes |

### Key Lesson

A Lambda handler configuration error can be resolved without changing the application code when the correct function already exists in the deployment package.

---

## 15. Verify Successful Recovery

### Step 1 — Invoke the Function Again

Use the same test event:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab02-healthy-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab02-healthy-invocation.json
```

Expected relevant field:

```json
{
  "StatusCode": 200
}
```

There should be no `FunctionError`.

### Step 3 — Inspect the Application Response

```bash
python3 -m json.tool healthy-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello, Cloud Engineer! Lambda handler executed.\", \"status\": \"success\"}"
}
```

### Step 4 — Verify the Response Programmatically

```bash
python3 - <<'PY'
import json

with open("lab02-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["status"] == "success"

assert body["message"] == (
    "Hello, Cloud Engineer! Lambda handler executed."
)

print("SUCCESS: HandlerNotFound error resolved")
PY
```

Expected:

```text
SUCCESS: HandlerNotFound error resolved
```

### Step 5 — Verify CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected application logs:

```text
Lambda Lab 02 started
Hello, Cloud Engineer! Lambda handler executed.
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Lambda Lab 02 started"' \
  --output json \
  --region "$AWS_REGION" \
  > lab02-recovered-cloudwatch-evidence.json
```

### Before and After Verification

| Check | Before | After |
|---|---|---|
| Function State | Active | Active |
| Configured Handler | Incorrect | Correct |
| Python Code | Valid | Valid |
| ZIP Package | Valid | Valid |
| FunctionError | Present | Absent |
| HandlerNotFound | Yes | No |
| Handler Code Executed | No | Yes |
| Application Response | Error | Success |
| Code Redeployment | Not needed | Not needed |

**Recovery is confirmed when the corrected handler configuration is active, the invocation has no FunctionError, and the application returns the expected response.**

---

## 16. Optional Exercise — Missing Python Module

This optional test demonstrates a different initialization failure.

### Step 1 — Set an Invalid Module Name

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --handler nonexistent_module.lambda_handler \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Invoke the Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  --region "$AWS_REGION" \
  missing-module-response.json \
  > lab02-missing-module-invocation.json
```

### Step 4 — Inspect the Error

```bash
python3 -m json.tool missing-module-response.json
```

Expected error category:

```text
Runtime.ImportModuleError
```

### Step 5 — Compare the Errors

| Scenario | Handler | Typical Error |
|---|---|---|
| Missing function | lambda_function.process_event | Runtime.HandlerNotFound |
| Missing module | nonexistent_module.lambda_handler | Runtime.ImportModuleError |

### Step 6 — Restore the Correct Handler

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --handler "$CORRECT_HANDLER" \
  --region "$AWS_REGION"
```

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Repeat the successful invocation if the optional test was performed.

---

<WritingBlock id="73186" variant="document">## 17. Production Troubleshooting Best Practices

### Standard Investigation Checklist

1. Verify the AWS account and Region.
2. Identify the failing Lambda function.
3. Confirm the function is deployed.
4. Inspect the configured runtime.
5. Inspect the configured handler.
6. Check the deployment ZIP structure.
7. Confirm the expected Python module exists.
8. Confirm the expected handler function exists.
9. Reproduce the error using a known payload.
10. Inspect the Lambda Invoke response.
11. Review the error payload.
12. Search CloudWatch Logs.
13. Identify the exact initialization error.
14. Compare configuration with source code.
15. Determine the root cause.
16. Correct the handler configuration.
17. Wait for the configuration update to finish.
18. Repeat the original invocation.
19. Verify the application response.
20. Preserve evidence and clean up.

### Investigation Flow

```text
Lambda Initialization Failure
             |
             v
Inspect Function Configuration
             |
             v
Check Handler String
             |
             v
Inspect Deployment ZIP
             |
             v
Verify Python Module Exists
             |
             v
Verify Handler Function Exists
             |
             v
Inspect Invocation Payload
             |
             v
Review CloudWatch Error
             |
             v
Identify Configuration Mismatch
             |
             v
Update Handler Setting
             |
             v
Verify Successful Invocation
```

### Common Lambda Initialization Problems

| Error | Possible Cause | Troubleshooting |
|---|---|---|
| Runtime.HandlerNotFound | Handler function missing | Compare handler and source |
| Runtime.ImportModuleError | Module or dependency missing | Inspect ZIP and imports |
| SyntaxError | Invalid Python syntax | Compile or parse source |
| AttributeError | Incorrect callable or object | Inspect module definitions |
| Dependency error | Package not included | Inspect dependencies |
| Permission error | Resource inaccessible | Inspect execution role |
| Runtime version mismatch | Incompatible deployment | Review runtime support |

### Production Recommendations

- Validate handler configuration before deployment.
- Keep the module and function names consistent.
- Include smoke tests in CI/CD pipelines.
- Verify deployment ZIP contents.
- Check Lambda `LastUpdateStatus` before testing.
- Use CloudWatch Logs to investigate initialization failures.
- Avoid unnecessary code changes when only configuration is wrong.
- Apply least-privilege execution roles.
- Keep deployment artifacts version controlled.
- Verify rollback procedures for production functions.

### Cloud Security Considerations

A handler error is generally an availability and configuration problem rather than evidence of a security breach.

However, repeated unexpected changes to Lambda configurations may require investigation.

Use CloudTrail to investigate who changed a function configuration when the change was not authorized or expected.

---

## 18. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 02.

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
Project = Lambda-Troubleshooting-Lab02
```

### Step 2 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Verify the Log Group Name

```bash
echo "$LOG_GROUP"
```

Expected:

```text
/aws/lambda/lambda-lab02-handler-not-found
```

### Step 4 — Delete the Lambda Function

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 5 — Detach the Managed Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 6 — Delete the Execution Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 7 — Delete the CloudWatch Log Group

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
| Dedicated execution role | Deleted |
| IAM managed policy attachment | Removed |
| CloudWatch log group | Deleted |
| VPC | Not created |
| NAT Gateway | Not created |
| RDS | Not created |
| EC2 | Not created |
| S3 bucket | Not created |

---

## 19. Interview Questions and Answers

### Q1. What is an AWS Lambda handler?

A handler is the application function AWS Lambda invokes when an event is received.

### Q2. What does `lambda_function.lambda_handler` represent?

`lambda_function` identifies the Python module, while `lambda_handler` identifies the function within that module.

### Q3. What causes Runtime.HandlerNotFound?

The runtime cannot find the configured handler function in the imported module.

### Q4. Can Lambda deployment succeed with an incorrect handler?

Yes. The handler mismatch can become apparent when Lambda attempts initialization or execution.

### Q5. What is Runtime.ImportModuleError?

An error indicating that Lambda cannot import the configured module or a required dependency.

### Q6. How is HandlerNotFound different from ImportModuleError?

HandlerNotFound usually means the module exists but the configured callable does not. ImportModuleError generally means the module or one of its imports could not be loaded.

### Q7. How do you inspect the Lambda handler configuration?

```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --query Handler \
  --region us-east-1
```

### Q8. How do you fix a handler configuration mismatch?

```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --handler lambda_function.lambda_handler \
  --region us-east-1
```

### Q9. Does fixing the handler always require redeploying source code?

No. If the correct function already exists in the deployment package, updating the handler configuration is sufficient.

### Q10. Why does CloudWatch show HandlerNotFound?

The Lambda runtime records the initialization failure when it cannot resolve the configured handler.

### Q11. Why may StatusCode 200 appear during the failure?

The synchronous Invoke API request succeeded, but Lambda reported the function error separately.

### Q12. What is the purpose of `LastUpdateStatus`?

It indicates the status of the latest Lambda code or configuration update.

### Q13. Why should you inspect the deployment ZIP?

To confirm that the expected Python module and package structure are present.

### Q14. Why might application logs be missing?

If the handler cannot be resolved, the application code never starts and its print statements do not execute.

### Q15. What is the difference between the execution role and the handler?

The execution role provides AWS permissions. The handler identifies the application entry point.

### Q16. Would increasing the Lambda timeout fix HandlerNotFound?

No. A timeout adjustment does not correct an invalid handler name.

### Q17. Would increasing Lambda memory fix HandlerNotFound?

No. The error is caused by configuration, not insufficient memory.

### Q18. How can CI/CD prevent handler errors?

Validate deployment package structure, check handler names, and run a post-deployment smoke test.

### Q19. How would you investigate an unexpected handler configuration change?

Inspect the current Lambda configuration and use CloudTrail to investigate the associated configuration update activity.

### Q20. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function with valid source code but intentionally configured an incorrect handler name.

The function deployed successfully and became Active.

However, when I invoked it, the runtime reported `Runtime.HandlerNotFound`.

I investigated the invocation response, CloudWatch logs, ZIP package contents, and Lambda configuration.

The deployed Python file defined `lambda_handler`, but the Lambda configuration referenced `process_event`.

I corrected the handler using AWS CLI without changing the application code or redeploying the ZIP.

After the configuration update completed, I invoked the function again and verified a successful response.

Finally, I removed the temporary Lambda function, execution role, and CloudWatch log group.

---

## 20. Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
│
├── 01-lambda-runtime-error/
│
├── 02-handler-not-found/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── test-event.json
│   ├── function.zip
│   ├── lab02-resources.env
│   ├── lab02-broken-configuration.json
│   ├── lab02-recovered-configuration.json
│   ├── lab02-broken-invocation.json
│   ├── lab02-healthy-invocation.json
│   ├── lab02-broken-cloudwatch-evidence.json
│   ├── lab02-recovered-cloudwatch-evidence.json
│   ├── broken-response.json
│   ├── healthy-response.json
│   ├── missing-module-response.json
│   └── lab02-missing-module-invocation.json
│
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
| `lambda_function.py` | Valid Python Lambda handler |
| `lambda-trust-policy.json` | Lambda service trust relationship |
| `test-event.json` | Example application invocation payload |
| `function.zip` | Generated deployment archive |
| `lab02-resources.env` | Local AWS resource identifiers |
| `lab02-broken-configuration.json` | Original incorrect handler configuration |
| `lab02-recovered-configuration.json` | Corrected handler configuration |
| `lab02-broken-invocation.json` | Failed invocation metadata |
| `lab02-healthy-invocation.json` | Successful invocation metadata |
| `lab02-broken-cloudwatch-evidence.json` | Initialization error logs |
| `lab02-recovered-cloudwatch-evidence.json` | Successful execution logs |
| `broken-response.json` | HandlerNotFound response |
| `healthy-response.json` | Successful response |
| `missing-module-response.json` | Optional import error response |
| `lab02-missing-module-invocation.json` | Optional import error metadata |

### Recommended GitHub Files

Publish:

```text
README.md
lambda_function.py
lambda-trust-policy.json
test-event.json
```

Keep private or sanitize before publishing:

```text
function.zip
lab02-resources.env
lab02-*-configuration.json
lab02-*-invocation.json
lab02-*-evidence.json
*-response.json
```

### Recommended .gitignore

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Generated packages
*.zip

# Local account configuration
**/lab02-resources.env

# Lambda invocation outputs
**/lab02-*-invocation.json
**/lab02-*-configuration.json
**/lab02-*-evidence.json
**/*-response.json

# Credentials
.env
.env.*
*.pem
*.key
```

---

## 21. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how a Lambda function can deploy successfully but fail because of an incorrect handler configuration.

We created a Python Lambda application with valid source code and deployed it with a deliberately incorrect handler name.

The function became Active but failed when invoked.

The invocation response and CloudWatch logs reported `Runtime.HandlerNotFound`.

We investigated the deployment ZIP and Python module to verify that the expected application code was present.

We compared the Lambda handler configuration with the actual function definition and identified the mismatch.

The root cause was a handler configuration that referenced a nonexistent function.

We corrected the handler using AWS CLI without modifying or redeploying the source code.

We then verified that Lambda executed the intended function and returned a successful application response.

An optional exercise demonstrated how a missing Python module produces a different initialization error.

Finally, we removed the temporary AWS resources.

**Key Lesson:** A successful Lambda deployment does not guarantee that the configured entry point exists. Engineers must verify the handler name, module structure, invocation result, and CloudWatch evidence.

### Skills Demonstrated

- AWS Lambda
- Python 3.13
- Lambda handler configuration
- Lambda initialization troubleshooting
- Runtime.HandlerNotFound
- Runtime.ImportModuleError
- AWS CLI v2
- Linux Bash
- Python source inspection
- ZIP deployment packages
- IAM execution roles
- IAM trust policies
- AWSLambdaBasicExecutionRole
- CloudWatch Logs
- Lambda Invoke API
- FunctionError investigation
- Configuration remediation
- LastUpdateStatus verification
- Root cause analysis
- Recovery testing
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-002 |
| Scenario | Handler Not Found |
| Function | lambda-lab02-handler-not-found |
| Region | us-east-1 |
| Runtime | Python 3.13 |
| Broken Handler | lambda_function.process_event |
| Error | Runtime.HandlerNotFound |
| Root Cause | Wrong handler name |
| Correct Handler | lambda_function.lambda_handler |
| Code Changes | None |
| Configuration Update | Required |
| Recovery | Successful invocation |
| Cleanup | Function, role, and logs deleted |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** Lambda handler failures are often configuration problems rather than application logic problems. Correctly identifying the module and function name can restore an application without requiring a code deployment.

---

## Official AWS Documentation

- [AWS Lambda Python Handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [AWS Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)
- [AWS Lambda Deployment Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-deployment.html)
- [AWS Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [AWS Lambda CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS CLI — UpdateFunctionConfiguration](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-configuration.html)
- [AWS CLI — Invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)