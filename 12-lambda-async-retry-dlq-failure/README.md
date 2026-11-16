# Lab 12 — AWS Lambda Asynchronous Retry and DLQ Failure

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda asynchronous invocation failure where an event cannot be delivered to an Amazon SQS dead-letter queue (DLQ).

In production, AWS Lambda is commonly used to process events from applications, Amazon S3, EventBridge, SNS, and other AWS services.

When Lambda processes an event asynchronously, the service accepts the event and processes it separately from the original request.

If the application fails, Lambda can retry execution according to its asynchronous invocation configuration.

After the permitted processing attempts are exhausted, Lambda can send the failed event to a configured dead-letter queue for investigation.

However, DLQ delivery can fail because of missing IAM permissions, invalid queue configuration, or other service-level issues.

In this lab, we create a Python Lambda function that intentionally raises a `RuntimeError` while processing selected events.

We configure asynchronous invocation with one function-error retry and attach an encrypted Amazon SQS standard queue as the Lambda DLQ.

We initially grant the Lambda execution role permission to send messages to SQS.

After configuring the DLQ successfully, we intentionally remove the `sqs:SendMessage` permission to simulate an IAM policy regression.

When we invoke Lambda asynchronously, the Invoke API returns `202 Accepted`.

However, the application fails, the event is retried, and Lambda cannot deliver the discarded event to SQS.

We investigate the failure using AWS CLI, CloudWatch Logs, Lambda asynchronous retry settings, IAM policies, SQS attributes, and the CloudWatch `DeadLetterErrors` metric.

After identifying the missing IAM permission, we restore least-privilege access, submit a new failing event, and verify that the original event payload is delivered to the SQS DLQ.

Finally, we remove the temporary Lambda, SQS, IAM, and CloudWatch resources.

This is the final troubleshooting scenario in the `aws-lambda-troubleshooting-labs` repository.

### Troubleshooting Workflow

```text
Create SQS Dead-Letter Queue
              |
              v
Create Lambda Execution Role
              |
              v
Grant sqs:SendMessage Permission
              |
              v
Create Python Lambda Application
              |
              v
Configure CloudWatch Logs
              |
              v
Deploy Lambda Function
              |
              v
Verify Successful Baseline
              |
              v
Configure Async Retry = 1
              |
              v
Attach SQS DLQ
              |
              v
Remove sqs:SendMessage Permission
              |
              v
Invoke Lambda Asynchronously
              |
              v
202 Accepted
              |
              v
Application Raises RuntimeError
              |
              v
Lambda Retries Event
              |
              v
Processing Fails Again
              |
              v
Attempt DLQ Delivery
              |
              v
IAM Permission Missing
              |
              v
DLQ Delivery Fails
              |
              v
DeadLetterErrors Increases
              |
              v
Investigate IAM and SQS
              |
              v
Restore sqs:SendMessage
              |
              v
Invoke New Failing Event
              |
              v
Retries Exhausted
              |
              v
SQS Receives Failed Event
              |
              v
Verify Original Message Body
              |
              v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-012 |
| Lab Name | Lambda Asynchronous Retry and DLQ Failure |
| Difficulty | Intermediate to Advanced |
| Primary Services | AWS Lambda, Amazon SQS |
| Supporting Services | IAM, Amazon CloudWatch |
| Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Tools | AWS CLI v2, Bash, Python |
| Lambda Runtime | Python 3.13 |
| Architecture | x86_64 |
| Function Name | `lambda-lab12-async-dlq` |
| Execution Role | `lambda-lab12-execution-role` |
| Handler | `lambda_function.lambda_handler` |
| Lambda Memory | 128 MB |
| Lambda Timeout | 10 seconds |
| Invocation Type | `Event` |
| Expected Invoke API Status | 202 |
| DLQ Name | `lambda-lab12-failed-events-dlq` |
| DLQ Type | SQS Standard Queue |
| SQS Encryption | SQS-managed SSE |
| Queue Retention | 3,600 seconds |
| Queue Visibility Timeout | 30 seconds |
| Maximum Function-Error Retries | 1 |
| Maximum Event Age | 600 seconds |
| Application Failure | `RuntimeError` |
| Missing Permission | `sqs:SendMessage` |
| Inline IAM Policy | `LambdaLab12SQSAccess` |
| CloudWatch Metrics | `Errors`, `DeadLetterErrors` |
| Root Cause | IAM policy regression prevents DLQ delivery |
| Remediation | Restore least-privilege `sqs:SendMessage` |
| Recovery Verification | Retrieve original failed event from SQS |
| VPC | Not required |
| NAT Gateway | Not required |
| Cleanup | Lambda, SQS, IAM, CloudWatch |

### Learning Objectives

- Understand asynchronous Lambda invocation.
- Understand HTTP 202 acceptance.
- Distinguish event acceptance from successful processing.
- Configure asynchronous retry attempts.
- Understand maximum event age.
- Create an Amazon SQS standard dead-letter queue.
- Understand Lambda DLQs versus on-failure destinations.
- Configure Lambda execution-role SQS permissions.
- Understand `sqs:SendMessage`.
- Reproduce failed Lambda processing.
- Investigate asynchronous retry behavior.
- Simulate an IAM permission regression.
- Diagnose missing DLQ messages.
- Understand CloudWatch `Errors`.
- Understand CloudWatch `DeadLetterErrors`.
- Inspect SQS message attributes.
- Retrieve and validate failed event payloads.
- Restore DLQ permissions safely.
- Understand event loss and reprocessing.
- Practice production root cause analysis.
- Clean up temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company uses AWS Lambda to process payment events asynchronously.

Applications submit payment-processing events to Lambda without waiting for the final processing result.

When Lambda receives an event, it validates the transaction and performs application operations.

If processing fails, Lambda should retry the event.

If all permitted attempts fail, the original event should be sent to an Amazon SQS dead-letter queue.

The operations team monitors the DLQ and investigates failed payment-processing events.

However, a recent IAM role update accidentally removes the execution role's permission to send messages to SQS.

The Lambda function and DLQ remain configured correctly.

When an application submits an event, Lambda returns HTTP 202.

The application raises a runtime error and Lambda retries processing.

The retry also fails.

Lambda attempts to deliver the failed event to SQS, but its execution role does not have the required `sqs:SendMessage` permission.

Consequently, the event is not stored in the DLQ.

The Cloud Engineering team investigates.

The engineer discovers that:

- Lambda is Active.
- The asynchronous invocation was accepted.
- The application failed during execution.
- The retry configuration is correct.
- The DLQ ARN is correct.
- The SQS queue exists.
- The execution role lacks `sqs:SendMessage`.
- CloudWatch reports DLQ delivery failures.

The engineer restores the least-privilege IAM policy.

A new failing event is submitted.

After the function-error retry is exhausted, Lambda successfully sends the failed event to SQS.

The engineer receives the message and verifies that its body contains the original failed event.

### Incident Symptoms

- Lambda Invoke API returns 202.
- Application processing fails.
- CloudWatch Logs show `RuntimeError`.
- The same event is retried.
- Lambda DLQ configuration is present.
- SQS queue remains empty.
- `DeadLetterErrors` increases.
- Execution role lacks SQS send permission.
- Restoring permission allows new failed events to reach SQS.

### Business Impact

Failed asynchronous events that are not preserved may cause:

- Lost payment-processing requests.
- Missing customer orders.
- Interrupted background operations.
- Incomplete event-driven workflows.
- Failed security automation.
- Missing audit-processing events.
- Delayed business operations.
- Increased recovery complexity.
- Data reconciliation problems.

### Objective

Identify why asynchronous Lambda processing fails and why unsuccessful events cannot be delivered to the configured SQS DLQ.

Restore the required IAM permission and verify that a new failed event is successfully retained for investigation.

---

## 3. AWS Architecture

### Broken Architecture

```text
                   Application
                       |
                       v
                 Async Invocation
                       |
                       v
                 AWS Lambda API
                       |
                       v
                  HTTP 202
                       |
                       v
              Internal Event Queue
                       |
                       v
               Lambda Execution
                       |
                       v
                RuntimeError
                       |
                       v
                  Retry Event
                       |
                       v
                RuntimeError
                       |
                       v
              Retry Limit Reached
                       |
                       v
               Attempt DLQ Delivery
                       |
                       v
              IAM Permission Check
                       |
                       v
              sqs:SendMessage Missing
                       |
                       X
                       |
                   SQS DLQ
                       |
                       v
                Event Not Stored
                       |
                       v
              DeadLetterErrors Metric
```

### Recovered Architecture

```text
                   Application
                       |
                       v
                Async Invocation
                       |
                       v
                 AWS Lambda API
                       |
                       v
                  HTTP 202
                       |
                       v
             Internal Event Queue
                       |
                       v
                Lambda Execution
                       |
                       v
                 RuntimeError
                       |
                       v
                  Retry Event
                       |
                       v
                 RuntimeError
                       |
                       v
                Retry Exhausted
                       |
                       v
               Attempt DLQ Delivery
                       |
                       v
              sqs:SendMessage Allowed
                       |
                       v
                  Amazon SQS DLQ
                       |
                       v
               Original Event Stored
                       |
                       v
                Cloud Engineer
                       |
                       v
                Receive Message
                       |
                       v
                Investigate Failure
```

### Architecture Components

| Component | Purpose |
|---|---|
| AWS Lambda | Processes asynchronous events |
| Lambda Async Event Queue | Buffers accepted asynchronous invocations |
| Lambda Retry Configuration | Controls function-error retry attempts |
| Amazon SQS | Stores events that could not be processed |
| Lambda DeadLetterConfig | Identifies the failure destination |
| IAM Execution Role | Grants permissions used by Lambda |
| Inline SQS Policy | Authorizes SendMessage to the DLQ |
| CloudWatch Logs | Records processing attempts and errors |
| CloudWatch Errors | Measures failed Lambda executions |
| CloudWatch DeadLetterErrors | Measures failures delivering events to DLQ |
| AWS CLI | Creates resources and investigates failures |
| Python | Implements the simulated failure |

---

## 4. Understanding Asynchronous Lambda Invocation

### What Is an Asynchronous Invocation?

An asynchronous Lambda invocation allows the caller to submit an event without waiting for the application to complete processing.

Example:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://broken-event.json \
  --region "$AWS_REGION" \
  broken-async-response.json
```

### What Does HTTP 202 Mean?

HTTP 202 indicates that Lambda accepted the asynchronous event.

It does not guarantee:

- Successful handler execution.
- Successful database operations.
- Successful retry processing.
- Successful DLQ delivery.
- Successful completion of the business workflow.

### Synchronous vs. Asynchronous Invocation

| Feature | Synchronous | Asynchronous |
|---|---|---|
| Invocation type | RequestResponse | Event |
| Normal API status | 200 | 202 |
| Caller waits for result | Yes | No |
| Caller receives handler response | Yes | No |
| Lambda manages function-error retries | No | Yes |
| Lambda async DLQ | Not applicable | Supported |

### What Happens When an Async Function Fails?

For a function error, Lambda can retry processing the event according to its asynchronous invocation retry configuration.

### How Many Retries Does Lambda Perform?

By default, Lambda makes up to two additional retries for function errors.

In this lab:

```text
MaximumRetryAttempts = 1
```

Therefore, the normal function-error sequence is:

```text
Attempt 1 → RuntimeError
Attempt 2 → RuntimeError
Retry limit reached
Attempt DLQ delivery
```

Additional duplicate processing is possible under at-least-once event delivery.

### What Is MaximumEventAgeInSeconds?

This setting limits how long an event can remain eligible for asynchronous processing.

Our configuration uses:

```text
MaximumEventAgeInSeconds = 600
```

### What Is a Lambda DLQ?

A Lambda dead-letter queue preserves discarded asynchronous events after Lambda cannot process them successfully.

Supported DLQ targets include standard SQS queues and standard SNS topics.

### What Does the SQS DLQ Store?

For this Lambda DLQ configuration, SQS receives the original event payload as the message body.

Error-related information is included in message attributes.

### What Is DeadLetterErrors?

A CloudWatch metric recording failures when Lambda attempts to send discarded asynchronous events to the configured DLQ.

### What Causes DeadLetterErrors?

Possible causes include:

- Missing `sqs:SendMessage` permission.
- Invalid DLQ ARN.
- Deleted destination queue.
- Restrictive SQS resource-based policies.
- Encryption-related permissions.
- Other queue delivery failures.

### Lambda DLQ vs. SQS Redrive DLQ

These are different mechanisms.

A Lambda asynchronous DLQ belongs to Lambda's asynchronous invocation failure handling.

An SQS redrive DLQ belongs to an SQS source queue's redrive policy.

This lab uses the first mechanism.

### Lambda DLQ vs. On-Failure Destination

A Lambda DLQ mainly stores the original event with diagnostic attributes.

An on-failure destination can receive a richer Lambda invocation record.

Both are useful for production incident investigation.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- ZIP and unzip.
- IAM role management permissions.
- Lambda management permissions.
- SQS management permissions.
- CloudWatch Logs and metrics permissions.

### Relevant AWS Permissions

```text
sts:GetCallerIdentity

iam:CreateRole
iam:GetRole
iam:ListRoleTags
iam:AttachRolePolicy
iam:ListAttachedRolePolicies
iam:PutRolePolicy
iam:GetRolePolicy
iam:ListRolePolicies
iam:DeleteRolePolicy
iam:DetachRolePolicy
iam:DeleteRole
iam:PassRole

lambda:CreateFunction
lambda:GetFunction
lambda:GetFunctionConfiguration
lambda:InvokeFunction
lambda:UpdateFunctionConfiguration
lambda:PutFunctionEventInvokeConfig
lambda:GetFunctionEventInvokeConfig
lambda:DeleteFunctionEventInvokeConfig
lambda:ListTags
lambda:DeleteFunction

sqs:CreateQueue
sqs:GetQueueUrl
sqs:GetQueueAttributes
sqs:ListQueueTags
sqs:ReceiveMessage
sqs:DeleteMessage
sqs:DeleteQueue

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup

cloudwatch:GetMetricStatistics
```

### Safety Rules

- Use a dedicated Lambda function.
- Create a dedicated SQS queue.
- Do not modify production IAM roles.
- Never remove SQS permissions from production applications for testing.
- Use fabricated event payloads.
- Keep the failure workload small.
- Verify AWS resource tags before cleanup.
- Do not publish account-specific identifiers or raw execution evidence.
- Do not delete DLQ messages before investigating them.
- Remove all temporary resources after the lab.

### Cost Considerations

This lab uses a small number of Lambda executions, SQS operations, and CloudWatch logs.

No EC2 instances, databases, NAT Gateways, or custom VPC resources are required.

The queue uses one-hour message retention for the lab. In production, a longer retention period is usually appropriate.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 12-lambda-async-retry-dlq-failure

cd 12-lambda-async-retry-dlq-failure
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
zip -v

aws sts get-caller-identity
```

Install ZIP tools if required:

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

export PROJECT_TAG="Lambda-Troubleshooting-Lab12"

export FUNCTION_NAME="lambda-lab12-async-dlq"

export ROLE_NAME="lambda-lab12-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export DLQ_NAME="lambda-lab12-failed-events-dlq"

export DLQ_POLICY_NAME="LambdaLab12SQSAccess"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"
```

### Step 4 — Save Environment Variables

```bash
cat > lab12-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export DLQ_NAME="$DLQ_NAME"
export DLQ_POLICY_NAME="$DLQ_POLICY_NAME"
export LOG_GROUP="$LOG_GROUP"
EOF

chmod 600 lab12-resources.env
```

Restore later:

```bash
source lab12-resources.env
```

### Step 5 — Verify Resources Do Not Already Exist

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

```bash
aws sqs get-queue-url \
  --queue-name "$DLQ_NAME" \
  --region "$AWS_REGION"
```

For a fresh lab, expect resource-not-found errors.

---

## 7. Create the SQS Dead-Letter Queue

### Step 1 — Create the Queue

```bash
export DLQ_URL=$(aws sqs create-queue \
  --queue-name "$DLQ_NAME" \
  --attributes \
  MessageRetentionPeriod=3600,VisibilityTimeout=30,SqsManagedSseEnabled=true \
  --tags "Project=$PROJECT_TAG" \
  --query QueueUrl \
  --output text \
  --region "$AWS_REGION")

echo "$DLQ_URL"
```

### Step 2 — Save Queue URL

```bash
echo "export DLQ_URL='$DLQ_URL'" >> lab12-resources.env
```

### Step 3 — Retrieve the Queue ARN

```bash
export DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text \
  --region "$AWS_REGION")

echo "$DLQ_ARN"
```

### Step 4 — Save Queue ARN

```bash
echo "export DLQ_ARN='$DLQ_ARN'" >> lab12-resources.env
```

### Step 5 — Verify Queue Attributes

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names All \
  --output json \
  --region "$AWS_REGION"
```

Expected relevant settings:

```text
MessageRetentionPeriod = 3600
VisibilityTimeout = 30
SqsManagedSseEnabled = true
```

### Step 6 — Verify Queue Tags

```bash
aws sqs list-queue-tags \
  --queue-url "$DLQ_URL" \
  --region "$AWS_REGION"
```

Confirm:

```text
Project = Lambda-Troubleshooting-Lab12
```

---

## 8. Create the Lambda Execution Role

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
  --description "Lambda asynchronous retry and DLQ Lab 12" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach Logging Permissions

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 4 — Create Least-Privilege SQS Policy

Generate `dlq-access-policy.json`:

```bash
python3 - <<'PY'
import json
import os

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSendToLab12DLQ",
            "Effect": "Allow",
            "Action": "sqs:SendMessage",
            "Resource": os.environ["DLQ_ARN"]
        }
    ]
}

with open("dlq-access-policy.json", "w") as file:
    json.dump(policy, file, indent=2)

print("SQS DLQ access policy generated")
PY
```

### Step 5 — Attach the Inline Policy

```bash
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME" \
  --policy-document file://dlq-access-policy.json
```

### Step 6 — Verify Permissions

```bash
aws iam get-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME"
```

Expected:

```text
Action = sqs:SendMessage
Resource = Lab 12 SQS DLQ ARN
```

### Why We Grant Permission Before Configuring the DLQ

AWS validates aspects of the Lambda DLQ configuration.

The function execution role should have the permissions required to send events to the selected destination.

Therefore, we configure the DLQ correctly first, then remove the permission to simulate a later production IAM regression.

This creates a realistic and controlled failure scenario.

---

## 9. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    event_id = event.get("event_id", "unknown")
    simulate_failure = event.get("simulate_failure", False)

    logger.info(
        "LAB12_START event_id=%s request_id=%s",
        event_id,
        context.aws_request_id
    )

    if simulate_failure:
        logger.error(
            "LAB12_PROCESSING_FAILED event_id=%s",
            event_id
        )

        raise RuntimeError(
            f"Simulated order processing failure: {event_id}"
        )

    logger.info(
        "LAB12_PROCESSING_SUCCESS event_id=%s",
        event_id
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Event processed successfully",
            "event_id": event_id
        })
    }
```

### Step 2 — Understand the Intentional Failure

When:

```json
{
  "simulate_failure": true
}
```

the application raises:

```python
raise RuntimeError(...)
```

This produces an unhandled function error.

### Step 3 — Understand the Logging

The handler records:

```text
LAB12_START
LAB12_PROCESSING_FAILED
LAB12_PROCESSING_SUCCESS
```

These messages help us identify actual Lambda processing attempts.

### Step 4 — Validate Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 5 — Package the Lambda Function

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
  "event_id": "LAB12-BASELINE-001",
  "simulate_failure": false
}
```

### Step 7 — Create Broken Event

Save as `broken-event.json`:

```json
{
  "event_id": "LAB12-BROKEN-001",
  "simulate_failure": true
}
```

### Step 8 — Create Recovery Event

Save as `recovered-event.json`:

```json
{
  "event_id": "LAB12-RECOVERED-001",
  "simulate_failure": true
}
```

The recovery event intentionally fails as well.

The objective is to restore failed-event retention, not to make the simulated business operation succeed.

---

## 10. Configure CloudWatch Logs

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
  --query "logGroups[?logGroupName=='${LOG_GROUP}'].{Name:logGroupName,Retention:retentionInDays}" \
  --output table \
  --region "$AWS_REGION"
```

---

## 11. Deploy AWS Lambda

### Step 1 — Create Lambda

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13 \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --memory-size 128 \
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

### Step 3 — Verify Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,Runtime:Runtime,Handler:Handler,Timeout:Timeout}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Runtime = python3.13
Timeout = 10
```

---

## 12. Verify the Baseline Application

### Step 1 — Invoke Synchronously

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://baseline-event.json \
  --region "$AWS_REGION" \
  baseline-response.json \
  > lab12-baseline-invocation.json
```

### Step 2 — Inspect Response

```bash
python3 -m json.tool baseline-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Event processed successfully\", \"event_id\": \"LAB12-BASELINE-001\"}"
}
```

### Step 3 — Verify Baseline

```bash
python3 - <<'PY'
import json

with open("lab12-baseline-invocation.json") as file:
    invocation = json.load(file)

with open("baseline-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["event_id"] == "LAB12-BASELINE-001"

print("SUCCESS: Baseline Lambda invocation completed")
PY
```

This confirms the Lambda application can process a normal event.

---

## 13. Configure Asynchronous Retry Behavior

### Step 1 — Configure One Retry

```bash
aws lambda put-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --maximum-retry-attempts 1 \
  --maximum-event-age-in-seconds 600 \
  --region "$AWS_REGION"
```

### Step 2 — Verify Retry Configuration

```bash
aws lambda get-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected relevant values:

```json
{
  "MaximumRetryAttempts": 1,
  "MaximumEventAgeInSeconds": 600
}
```

### Step 3 — Understand the Processing Sequence

```text
Asynchronous event accepted
          |
          v
First execution
          |
          v
RuntimeError
          |
          v
One retry
          |
          v
RuntimeError
          |
          v
Retry attempts exhausted
          |
          v
Attempt DLQ delivery
```

The setting of one retry applies to ordinary function errors.

Lambda has different retry behavior for certain throttling and service errors.

---

## 14. Configure the SQS DLQ

### Step 1 — Attach SQS as the DLQ

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --dead-letter-config "TargetArn=$DLQ_ARN" \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify the DLQ

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,LastUpdateStatus:LastUpdateStatus,DeadLetterConfig:DeadLetterConfig}' \
  --output json \
  --region "$AWS_REGION"
```

Expected structure:

```json
{
  "State": "Active",
  "LastUpdateStatus": "Successful",
  "DeadLetterConfig": {
    "TargetArn": "arn:aws:sqs:us-east-1:ACCOUNT_ID:lambda-lab12-failed-events-dlq"
  }
}
```

### Step 4 — Save Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION" \
  > lab12-initial-function-config.json
```

### Step 5 — Save Async Configuration

```bash
aws lambda get-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION" \
  > lab12-async-retry-config.json
```

At this point, the function has a valid DLQ and the necessary IAM permission.

---

## 15. Fault Injection — Remove SQS SendMessage Permission

### Step 1 — Remove Inline SQS Permission

```bash
aws iam delete-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME"
```

This is the intentional failure.

### Step 2 — Verify Inline Policy Removal

```bash
aws iam list-role-policies \
  --role-name "$ROLE_NAME" \
  --output json
```

Expected:

```json
{
  "PolicyNames": []
}
```

### Step 3 — Verify Missing IAM Policy

```bash
aws iam get-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 4 — Verify CloudWatch Logging Remains

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaBasicExecutionRole
```

### Step 5 — Verify the DLQ Configuration Still Exists

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'DeadLetterConfig' \
  --region "$AWS_REGION"
```

The SQS ARN should still be present.

### Broken Configuration

| Component | Expected State |
|---|---|
| Lambda | Active |
| Retry configuration | Correct |
| SQS queue | Exists |
| DLQ ARN | Configured |
| CloudWatch logging | Allowed |
| sqs:SendMessage | Missing |
| DLQ delivery | Expected to fail |

IAM changes are eventually consistent. Wait for the removed permission to propagate before running the failing event.

---

## 16. Reproduce the Asynchronous Failure

### Step 1 — Invoke Lambda Asynchronously

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://broken-event.json \
  --region "$AWS_REGION" \
  broken-async-response.json \
  > lab12-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab12-broken-invocation.json
```

Expected:

```json
{
  "StatusCode": 202
}
```

### Step 3 — Verify Async Acceptance

```bash
python3 - <<'PY'
import json

with open("lab12-broken-invocation.json") as file:
    invocation = json.load(file)

assert invocation["StatusCode"] == 202

print("SUCCESS: Asynchronous event accepted")
print("Processing result not yet confirmed")
PY
```

### Important Observation

A 202 response does not mean successful payment processing.

It only means the event was accepted for asynchronous execution.

### Step 4 — Inspect Lambda Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected messages resemble:

```text
LAB12_START event_id=LAB12-BROKEN-001
LAB12_PROCESSING_FAILED event_id=LAB12-BROKEN-001
RuntimeError: Simulated order processing failure
```

### Step 5 — Inspect Retry Attempts

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB12_PROCESSING_FAILED" "LAB12-BROKEN-001"' \
  --query 'events[].{Timestamp:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

Under normal function-error retry behavior, the event should have two execution attempts.

Because asynchronous processing is eventually consistent, allow enough time for the retry to occur.

### Step 6 — Check SQS Queue

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --output json \
  --region "$AWS_REGION"
```

After processing and DLQ delivery attempts have completed, no event is expected to appear because the send permission is missing.

Queue counts are approximate, so use CloudWatch metrics for additional evidence.

---

## 17. Investigate CloudWatch Metrics

### Step 1 — Define Observation Window

```bash
export START_TIME=$(date -u -d '20 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')

export END_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
```

### Step 2 — Inspect Lambda Errors

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION"
```

Expected: a nonzero error count when metric data is available.

### Step 3 — Inspect DeadLetterErrors

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name DeadLetterErrors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION"
```

This is the main DLQ failure metric.

Expected: a nonzero datapoint after the DLQ delivery attempt fails.

### Step 4 — Save DeadLetterErrors Evidence

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name DeadLetterErrors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION" \
  > lab12-broken-deadletter-errors.json
```

### Step 5 — Save Lambda Errors Evidence

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Sum \
  --output json \
  --region "$AWS_REGION" \
  > lab12-broken-lambda-errors.json
```

### Step 6 — Save CloudWatch Log Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB12-BROKEN-001"' \
  --output json \
  --region "$AWS_REGION" \
  > lab12-broken-cloudwatch-evidence.json
```

### Investigation Findings

| Component | Expected Finding |
|---|---|
| Async Invoke API | 202 Accepted |
| Lambda state | Active |
| Application execution | RuntimeError |
| Function-error retry | Configured |
| DLQ ARN | Correct |
| SQS queue | Exists |
| IAM SendMessage permission | Missing |
| DLQ messages | Not received |
| Lambda Errors | Nonzero |
| DeadLetterErrors | Nonzero |
| Root cause | Missing IAM permission |

**Important:** An empty DLQ alone does not conclusively prove a permission failure. Confirm that retries have finished, the role lacks permission, and Lambda has attempted DLQ delivery.

---

## 18. Root Cause Analysis

### Root Cause

The Lambda execution role did not have `sqs:SendMessage` permission for the configured dead-letter queue.

The application intentionally failed during processing.

After the configured retry was exhausted, Lambda attempted to deliver the discarded event to SQS.

The send operation was not authorized.

Consequently, the original failed event could not be retained in the configured DLQ.

### Root Cause Diagram

```text
Asynchronous Event
         |
         v
202 Accepted
         |
         v
Lambda Processing
         |
         v
RuntimeError
         |
         v
Retry Attempt
         |
         v
RuntimeError Again
         |
         v
Retries Exhausted
         |
         v
DLQ Delivery Attempt
         |
         v
IAM Authorization Check
         |
         v
sqs:SendMessage Missing
         |
         v
DLQ Delivery Fails
         |
         v
DeadLetterErrors
         |
         v
Event Not Preserved
```

### Five Whys

**Why 1 — Why was the failed event missing from SQS?**

Lambda could not deliver it to the DLQ.

**Why 2 — Why couldn't Lambda deliver the event?**

The execution role lacked SQS send permission.

**Why 3 — Why was the permission missing?**

The inline IAM policy was removed.

**Why 4 — Why wasn't the incident obvious from the invocation response?**

The asynchronous Invoke API returned 202 before later processing and DLQ delivery completed.

**Why 5 — How can the issue be prevented?**

Manage IAM policies through Infrastructure as Code, monitor DLQ delivery metrics, and test failure handling after permission changes.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-012 |
| Primary Services | Lambda, SQS |
| Invocation Type | Event |
| Invoke Status | 202 |
| Application Error | RuntimeError |
| Retry Configuration | 1 retry |
| DLQ Configuration | Correct |
| Missing Permission | sqs:SendMessage |
| Root Cause | IAM policy regression |
| Evidence | DeadLetterErrors and absent message |
| Remediation | Restore SendMessage |
| Recovery Verification | Receive failed event from SQS |

---

<WritingBlock id="81243" variant="document">## 19. Remediation — Restore SQS SendMessage Permission

### Step 1 — Verify the DLQ ARN

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{State:State,DLQ:DeadLetterConfig}' \
  --output json \
  --region "$AWS_REGION"
```

Expected: Lambda is Active and its DLQ target ARN matches the queue created for Lab 12.

### Step 2 — Restore the Inline IAM Policy

```bash
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME" \
  --policy-document file://dlq-access-policy.json
```

### Step 3 — Verify the Restored Permission

```bash
aws iam get-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME"
```

Verify:

```text
Effect: Allow
Action: sqs:SendMessage
Resource: Lab 12 SQS DLQ ARN
```

### Step 4 — Verify the Queue

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn MessageRetentionPeriod \
  --output json \
  --region "$AWS_REGION"
```

### Step 5 — Verify IAM Authorization with Policy Simulation

If your lab identity has permission to use the IAM policy simulator:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn "$ROLE_ARN" \
  --action-names sqs:SendMessage \
  --resource-arns "$DLQ_ARN" \
  --query 'EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}' \
  --output table
```

Expected identity-policy result:

```text
sqs:SendMessage → allowed
```

The IAM policy simulator is useful for diagnosing permissions, but it does not replace an actual end-to-end test. Other authorization controls, such as queue resource policies or applicable organization restrictions, may still affect delivery.

### Remediation Comparison

| Setting | Broken | Recovered |
|---|---|---|
| Lambda function | Active | Active |
| Handler | Intentionally fails | Intentionally fails |
| Async retry attempts | 1 | 1 |
| Maximum event age | 600 seconds | 600 seconds |
| DLQ ARN | Correct | Correct |
| SQS queue | Exists | Exists |
| sqs:SendMessage | Missing | Allowed |
| Expected DLQ delivery | Fails | Succeeds |

The application code is intentionally unchanged.

We are repairing the failed-event handling mechanism.

**Important:** Restoring IAM permission does not automatically recover events that have already been discarded after unsuccessful DLQ delivery. A new failed event is required for recovery verification.

---

## 20. Verify Successful DLQ Recovery

### Step 1 — Invoke the Recovered Test Event

Submit a new event asynchronously:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://recovered-event.json \
  --region "$AWS_REGION" \
  recovered-async-response.json \
  > lab12-recovered-invocation.json
```

### Step 2 — Verify Event Acceptance

```bash
python3 - <<'PY'
import json

with open("lab12-recovered-invocation.json") as file:
    invocation = json.load(file)

assert invocation["StatusCode"] == 202

print("SUCCESS: Recovery event accepted")
PY
```

This confirms acceptance, not final processing or DLQ delivery.

### Step 3 — Check Failed Processing Logs

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB12_PROCESSING_FAILED" "LAB12-RECOVERED-001"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

Expected application message:

```text
LAB12_PROCESSING_FAILED event_id=LAB12-RECOVERED-001
```

### Step 4 — Check Queue Message Count

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --output json \
  --region "$AWS_REGION"
```

The queue may remain empty temporarily while Lambda processes retries.

### Step 5 — Poll SQS for Failed-Event Delivery

```bash
export MESSAGE_FOUND="false"

for attempt in $(seq 1 24); do
  MESSAGE_COUNT=$(aws sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --attribute-names ApproximateNumberOfMessages \
    --query 'Attributes.ApproximateNumberOfMessages' \
    --output text \
    --region "$AWS_REGION")

  echo "DLQ poll $attempt: $MESSAGE_COUNT available messages"

  if [ "$MESSAGE_COUNT" != "None" ] && \
     [ "$MESSAGE_COUNT" -gt 0 ]; then
    MESSAGE_FOUND="true"
    break
  fi

  sleep 10
done

if [ "$MESSAGE_FOUND" != "true" ]; then
  echo "No message observed. Investigate retries, IAM, and SQS."
fi
```

The observation window allows time for the asynchronous retry cycle to complete.

A queue's approximate message count can lag behind actual delivery.

### Step 6 — Receive the DLQ Message

```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 1 \
  --message-system-attribute-names All \
  --message-attribute-names All \
  --wait-time-seconds 10 \
  --visibility-timeout 120 \
  --output json \
  --region "$AWS_REGION" \
  > lab12-recovered-dlq-message.json
```

### Step 7 — Inspect the Message

```bash
python3 -m json.tool lab12-recovered-dlq-message.json
```

Expected structure:

```json
{
  "Messages": [
    {
      "MessageId": "example-message-id",
      "Body": "{\"event_id\":\"LAB12-RECOVERED-001\",\"simulate_failure\":true}",
      "MessageAttributes": {
        "RequestID": {
          "DataType": "String",
          "StringValue": "example-request-id"
        },
        "ErrorCode": {
          "DataType": "Number",
          "StringValue": "200"
        },
        "ErrorMessage": {
          "DataType": "String",
          "StringValue": "example-error"
        }
      }
    }
  ]
}
```

The exact values and attributes may vary.

The most important field is the original failed event in `Body`.

### Step 8 — Verify the Original Failed Event

```bash
python3 - <<'PY'
import json

with open("lab12-recovered-dlq-message.json") as file:
    response = json.load(file)

messages = response.get("Messages", [])

assert messages, "No SQS message received"

message = messages[0]
body = json.loads(message["Body"])

assert body["event_id"] == "LAB12-RECOVERED-001"
assert body["simulate_failure"] is True

print("SUCCESS: Failed event reached SQS DLQ")
print("Event ID:", body["event_id"])

print(
    "Message attributes:",
    list(message.get("MessageAttributes", {}).keys())
)
PY
```

### Step 9 — Inspect Recovery Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 20m \
  --region "$AWS_REGION"
```

### Step 10 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB12-RECOVERED-001"' \
  --output json \
  --region "$AWS_REGION" \
  > lab12-recovered-cloudwatch-evidence.json
```

### Recovery Comparison

| Check | Broken | Recovered |
|---|---|---|
| Async Invoke API | 202 | 202 |
| Function processing | Failed | Intentionally failed |
| Retry configuration | 1 retry | 1 retry |
| SQS DLQ | Configured | Configured |
| sqs:SendMessage | Missing | Restored |
| Event delivered to SQS | No | Yes |
| Event available for investigation | No | Yes |
| Application code | Unchanged | Unchanged |
| Operational recovery | Failed | Successful |

**Recovery is confirmed when the original payload of the new failed event can be retrieved from the SQS dead-letter queue.**

---

## 21. Inspect and Acknowledge the SQS Message

### Step 1 — Inspect Message Attributes

```bash
python3 - <<'PY'
import json

with open("lab12-recovered-dlq-message.json") as file:
    data = json.load(file)

for message in data.get("Messages", []):
    print("Message ID:", message["MessageId"])

    for name, attribute in message.get(
        "MessageAttributes", {}
    ).items():
        print(name, attribute.get("StringValue"))
PY
```

### Understanding Message Attributes

| Field | Purpose |
|---|---|
| MessageId | SQS message identifier |
| Body | Original failed event payload |
| RequestID | Associated Lambda invocation identifier |
| ErrorCode | Error information |
| ErrorMessage | Processing failure details |
| ReceiptHandle | Token used to delete the received message |

The receipt handle is returned by SQS when a consumer receives the message.

### Step 2 — Extract Receipt Handle

```bash
export RECEIPT_HANDLE=$(python3 - <<'PY'
import json

with open("lab12-recovered-dlq-message.json") as file:
    data = json.load(file)

print(data["Messages"][0]["ReceiptHandle"])
PY
)
```

### Step 3 — Delete the Verified Message

```bash
aws sqs delete-message \
  --queue-url "$DLQ_URL" \
  --receipt-handle "$RECEIPT_HANDLE" \
  --region "$AWS_REGION"
```

In production, do not delete failed events until they have been investigated, reprocessed if necessary, or handled according to an approved recovery procedure.

---

## 22. Production Troubleshooting Best Practices

### Investigation Checklist

1. Identify the affected Lambda function.
2. Verify AWS account and Region.
3. Confirm the function is Active.
4. Identify the asynchronous event source.
5. Verify that the Invoke API accepted the event.
6. Inspect CloudWatch application logs.
7. Identify the function error.
8. Inspect asynchronous retry configuration.
9. Verify maximum retry attempts.
10. Verify maximum event age.
11. Inspect the Lambda DLQ ARN.
12. Confirm the SQS queue exists.
13. Inspect execution-role IAM permissions.
14. Check `sqs:SendMessage`.
15. Review SQS queue policies and encryption settings.
16. Check CloudWatch `Errors`.
17. Check `DeadLetterErrors`.
18. Determine whether the event was discarded.
19. Correct the delivery configuration.
20. Generate a new failing test event.
21. Verify retry behavior.
22. Receive the failed message from SQS.
23. Validate the original event.
24. Document the root cause.
25. Clean up temporary resources.

### Common Asynchronous Failure Scenarios

| Problem | Possible Cause | Investigation |
|---|---|---|
| HTTP 202 but application fails | Asynchronous processing error | Lambda Logs |
| Multiple processing attempts | Retry configuration | Event invoke config |
| Event missing from DLQ | Missing SendMessage permission | IAM role |
| DeadLetterErrors increases | DLQ delivery failure | CloudWatch |
| Queue not found | Incorrect or deleted SQS queue | GetQueueAttributes |
| Event age exceeded | Processing delayed too long | AsyncEventAge |
| Events discarded | Retries or age exhausted | AsyncEventsDropped |
| Duplicate processing | At-least-once semantics | Event IDs and logs |
| Queue delivery denied | IAM or SQS policy | Policy evaluation |
| Encrypted queue failure | KMS permission problems where applicable | Queue encryption configuration |
| Failed events cannot be replayed | No retained event copy | DLQ and recovery design |

---

## 23. Lambda DLQ vs. On-Failure Destination

| Feature | Lambda DLQ | On-Failure Destination |
|---|---|---|
| Purpose | Store failed events | Store detailed failure records |
| SQS supported | Yes | Yes |
| SNS supported | Yes | Yes |
| Original payload | Yes | Included in invocation record when deliverable |
| Error details | Message attributes | Richer record |
| Failure metric | DeadLetterErrors | DestinationDeliveryFailures |
| Common use | Preserve failed work | Failure analysis and routing |

### Which Should Be Used in Production?

Both mechanisms can be useful.

A DLQ is a simple way to retain failed asynchronous events.

An on-failure destination provides more information about the failed invocation and can support more advanced processing workflows.

The best choice depends on application requirements and operational needs.

---

## 24. Production Reliability and Recovery Design

### Idempotency

Asynchronous processing can result in duplicate execution attempts.

Applications should use unique event IDs and idempotent operations where possible.

For example, processing the same payment event twice must not charge a customer twice.

### Event Reprocessing

A failed event may be investigated, corrected, and resubmitted for processing.

A production workflow should preserve traceability between the original event and any replayed event.

### DLQ Retention

The lab uses:

```text
MessageRetentionPeriod = 3600
```

That is one hour.

Production queues usually require a retention period aligned with incident response and recovery objectives.

### DeadLetterErrors Monitoring

Create a CloudWatch alarm to detect unexpected DLQ delivery failures.

A rising metric may indicate that events are being discarded without reaching the intended recovery system.

### IAM Policy Management

Use Terraform or CloudFormation to manage:

- Lambda execution roles.
- SQS permissions.
- DLQ configuration.
- Async retry settings.
- CloudWatch alarms.

Changes should be reviewed and tested before deployment.

### Queue Encryption

The lab uses SQS-managed server-side encryption.

If a production queue uses customer-managed AWS KMS encryption, review the additional key policies and permissions required by the integration.

---

## 25. Cloud Security Engineering Considerations

### Availability and Resilience

A DLQ helps preserve work that cannot be completed successfully.

Without reliable failed-event retention, an application may lose important operations.

### IAM Least Privilege

Grant only the permissions needed:

```text
sqs:SendMessage
```

Scope the permission to the specific DLQ ARN.

### Event Data Protection

Failed-event payloads may contain sensitive customer or business information.

Encrypt queues, control message access, and avoid storing unnecessary secrets in event payloads.

### Monitoring and Detection

Monitor:

```text
Errors
DeadLetterErrors
AsyncEventAge
AsyncEventsDropped
```

These metrics help identify processing failures and failures in the recovery mechanism.

### Auditability

Use AWS CloudTrail to investigate relevant IAM policy changes and Lambda configuration changes.

### Preventing Silent Data Loss

A system can return successful asynchronous acceptance while later losing the event.

Cloud Security Engineers should verify end-to-end processing and failure retention rather than relying only on the initial API response.

---

## 26. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 12.

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
Project = Lambda-Troubleshooting-Lab12
```

### Step 2 — Verify SQS Ownership

```bash
aws sqs list-queue-tags \
  --queue-url "$DLQ_URL" \
  --region "$AWS_REGION"
```

### Step 3 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm that all three resources belong to this lab.

### Step 4 — Confirm the Retry Cycle Is Complete

```bash
aws logs tail "$LOG_GROUP" \
  --since 20m \
  --region "$AWS_REGION"
```

Confirm that the recovered event has completed its retry cycle and was delivered to SQS.

### Step 5 — Remove Custom Async Configuration

```bash
aws lambda delete-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 6 — Remove Lambda DLQ Configuration

```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --dead-letter-config '{"TargetArn":""}' \
  --region "$AWS_REGION"
```

Wait for update completion:

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Verify:

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query 'DeadLetterConfig' \
  --region "$AWS_REGION"
```

Expected: no DLQ target configured.

### Step 7 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 8 — Delete Inline SQS Policy

```bash
aws iam delete-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$DLQ_POLICY_NAME"
```

### Step 9 — Detach CloudWatch Logging Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 10 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 11 — Inspect Remaining SQS Messages

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --output json \
  --region "$AWS_REGION"
```

Verify no unexpected messages remain.

### Step 12 — Delete SQS Queue

```bash
aws sqs delete-queue \
  --queue-url "$DLQ_URL" \
  --region "$AWS_REGION"
```

### Step 13 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 14 — Verify Lambda Deletion

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
ResourceNotFoundException
```

### Step 15 — Verify IAM Role Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 16 — Verify SQS Queue Deletion

```bash
aws sqs get-queue-url \
  --queue-name "$DLQ_NAME" \
  --region "$AWS_REGION"
```

Expected after deletion propagates:

```text
QueueDoesNotExist
```

### Step 17 — Verify CloudWatch Cleanup

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
| Custom async retry configuration | Removed |
| Lambda DLQ configuration | Removed |
| IAM execution role | Deleted |
| IAM inline SendMessage policy | Deleted |
| SQS queue | Deleted |
| CloudWatch log group | Deleted |
| VPC | Not created |
| NAT Gateway | Not created |
| RDS | Not created |

---

## 27. Interview Questions and Answers

### Q1. What is asynchronous Lambda invocation?

An invocation where Lambda accepts an event for later processing without waiting for the handler to complete.

### Q2. What does HTTP 202 mean?

The asynchronous event was accepted. It does not guarantee successful processing.

### Q3. How many times does Lambda retry an asynchronous function error?

By default, Lambda can retry a function error two additional times.

### Q4. What is MaximumRetryAttempts?

A setting controlling the number of additional function-error execution attempts.

### Q5. What is MaximumEventAgeInSeconds?

A setting limiting how long an asynchronous event remains eligible for processing.

### Q6. What is a Lambda dead-letter queue?

A standard SQS queue or standard SNS topic configured to retain discarded asynchronous events.

### Q7. What caused the DLQ failure in this lab?

The Lambda execution role was missing `sqs:SendMessage`.

### Q8. What is DeadLetterErrors?

A CloudWatch metric that measures failed attempts to send discarded asynchronous events to the configured DLQ.

### Q9. What is the difference between Errors and DeadLetterErrors?

`Errors` measures failed function executions. `DeadLetterErrors` measures failures delivering discarded events to the DLQ.

### Q10. Why was the SQS queue empty?

The execution role lacked permission to send messages to that queue.

### Q11. Does restoring IAM permission recover previously discarded events?

No. Events already discarded after failed DLQ delivery are not automatically recovered.

### Q12. How do you verify that DLQ delivery works?

Submit a new failing asynchronous event, allow its retries to finish, and retrieve the original payload from SQS.

### Q13. What is the difference between a Lambda DLQ and an SQS source queue DLQ?

The Lambda DLQ handles discarded asynchronous Lambda events. An SQS source queue DLQ receives messages according to the source queue's redrive policy.

### Q14. What is an on-failure destination?

A Lambda asynchronous invocation configuration that routes detailed failure records to a supported destination.

### Q15. Why should asynchronous applications be idempotent?

The same event may be processed multiple times due to retries or duplicate delivery.

### Q16. How can failed events be reprocessed?

By retrieving the stored event, investigating the failure, and submitting it again through an approved processing workflow.

### Q17. Can a queue encryption configuration prevent delivery?

Yes. Depending on the encryption configuration, additional permissions may be required.

### Q18. How can DLQ delivery failures be monitored?

Monitor the CloudWatch `DeadLetterErrors` metric and configure appropriate alarms.

### Q19. Why use Terraform for DLQ configuration?

It helps keep Lambda configuration, IAM permissions, and recovery infrastructure consistent and reviewable.

### Q20. How would you explain this lab in an interview?

I deployed an asynchronous AWS Lambda application that intentionally failed while processing selected events.

I created an encrypted Amazon SQS standard dead-letter queue and configured Lambda to retry failed processing once.

I initially granted the execution role permission to send messages to SQS.

After configuring the DLQ, I removed `sqs:SendMessage` to simulate an IAM policy regression.

I submitted an asynchronous event and observed that Lambda returned 202 Accepted even though the application failed during processing.

I investigated the Lambda CloudWatch Logs, retry settings, SQS queue attributes, IAM permissions, and DeadLetterErrors metric.

I identified the missing SQS send permission as the root cause of the DLQ delivery failure.

I restored the least-privilege IAM policy and submitted a new failing event.

After the retry attempts were exhausted, the failed event was successfully delivered to SQS.

I retrieved the message and verified that its body contained the original event payload.

Finally, I removed the Lambda function, SQS queue, IAM role, and CloudWatch resources.

---

## 28. Repository Structure

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
├── 11-lambda-concurrency-throttling/
│
└── 12-lambda-async-retry-dlq-failure/
    ├── README.md
    ├── lambda_function.py
    ├── lambda-trust-policy.json
    ├── dlq-access-policy.json
    ├── baseline-event.json
    ├── broken-event.json
    ├── recovered-event.json
    ├── function.zip
    ├── lab12-resources.env
    ├── lab12-initial-function-config.json
    ├── lab12-async-retry-config.json
    ├── lab12-baseline-invocation.json
    ├── lab12-broken-invocation.json
    ├── lab12-recovered-invocation.json
    ├── lab12-broken-deadletter-errors.json
    ├── lab12-broken-lambda-errors.json
    ├── lab12-broken-cloudwatch-evidence.json
    ├── lab12-recovered-cloudwatch-evidence.json
    ├── lab12-recovered-dlq-message.json
    ├── baseline-response.json
    ├── broken-async-response.json
    └── recovered-async-response.json
```

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Complete incident and remediation documentation |
| lambda_function.py | Python async processing application |
| lambda-trust-policy.json | IAM execution-role trust policy |
| dlq-access-policy.json | Generated least-privilege SQS IAM policy |
| baseline-event.json | Successful processing event |
| broken-event.json | Intentional processing failure event |
| recovered-event.json | New failing event used for DLQ verification |
| function.zip | Generated deployment package |
| lab12-resources.env | Local AWS resource identifiers |
| lab12-initial-function-config.json | Original Lambda configuration |
| lab12-async-retry-config.json | Retry configuration evidence |
| lab12-baseline-invocation.json | Baseline invocation metadata |
| lab12-broken-invocation.json | Broken async invocation metadata |
| lab12-recovered-invocation.json | Recovery async invocation metadata |
| lab12-broken-deadletter-errors.json | DLQ delivery failure metric |
| lab12-broken-lambda-errors.json | Function error metric |
| lab12-broken-cloudwatch-evidence.json | Failed processing logs |
| lab12-recovered-cloudwatch-evidence.json | Recovered test logs |
| lab12-recovered-dlq-message.json | Original failed event received from SQS |
| baseline-response.json | Baseline application result |
| broken-async-response.json | Async invocation output file |
| recovered-async-response.json | Recovery invocation output file |

### Recommended Public GitHub Files

```text
12-lambda-async-retry-dlq-failure/
├── README.md
├── lambda_function.py
├── lambda-trust-policy.json
├── baseline-event.json
├── broken-event.json
└── recovered-event.json
```

The generated `dlq-access-policy.json` contains your actual SQS ARN. Sanitize it before publishing, or replace the resource ARN with a placeholder in a public example.

### Recommended Root .gitignore

Add the following:

```gitignore
# Lambda Lab 12
12-lambda-async-retry-dlq-failure/function.zip
12-lambda-async-retry-dlq-failure/lab12-resources.env
12-lambda-async-retry-dlq-failure/lab12-*.json
12-lambda-async-retry-dlq-failure/*-response.json
12-lambda-async-retry-dlq-failure/dlq-access-policy.json

# Python
__pycache__/
*.pyc
.venv/

# Credentials
.env
.env.*
*.pem
*.key
```

Generated evidence files and account-specific configurations should not be published without review.

Files already tracked in Git are not automatically excluded after adding `.gitignore` rules.

---

## 29. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how asynchronous AWS Lambda processing and failed-event retention work together.

We created a Python Lambda application that intentionally raised a RuntimeError when processing selected events.

We configured asynchronous invocation with one function-error retry and attached an SQS standard dead-letter queue.

We granted the Lambda execution role the required `sqs:SendMessage` permission.

After configuring the DLQ, we intentionally removed the permission to simulate an IAM policy regression.

When we submitted the failed event asynchronously, Lambda returned HTTP 202 because the event was accepted.

However, the application failed during execution.

The configured retry also failed, and Lambda could not deliver the discarded event to SQS because of the missing IAM permission.

We investigated the failure using CloudWatch Logs, IAM policy inspection, SQS queue attributes, the Lambda Errors metric, and DeadLetterErrors.

We identified the missing `sqs:SendMessage` permission as the root cause of the DLQ delivery failure.

After restoring the IAM policy, we submitted a new failing event.

Lambda exhausted the permitted retry attempts and successfully delivered the event to the SQS dead-letter queue.

We retrieved the failed event and verified that the original event payload was preserved.

Finally, we removed all temporary AWS resources.

**Key Lesson:** An asynchronous Lambda invocation returning HTTP 202 does not guarantee that the application successfully processed the event. Reliable systems must also monitor execution failures, retries, and failed-event delivery.

### Skills Demonstrated

- AWS Lambda
- Lambda asynchronous invocation
- Lambda retry configuration
- MaximumRetryAttempts
- MaximumEventAgeInSeconds
- Amazon SQS
- Lambda dead-letter queues
- SQS message attributes
- SQS message visibility
- SQS encryption
- Python RuntimeError
- IAM execution roles
- Inline IAM policies
- sqs:SendMessage
- AWS CLI v2
- Linux Bash
- CloudWatch Logs
- Lambda Errors
- Lambda DeadLetterErrors
- Asynchronous event processing
- Event idempotency
- IAM troubleshooting
- Event delivery failure investigation
- Root cause analysis
- Failed-event recovery
- Cloud security engineering
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-012 |
| Scenario | Lambda Asynchronous Retry and DLQ Failure |
| Function | lambda-lab12-async-dlq |
| Invocation Type | Event |
| API Response | 202 Accepted |
| Application Error | RuntimeError |
| Configured Retry | 1 |
| DLQ | Amazon SQS Standard Queue |
| Intentional Misconfiguration | Missing sqs:SendMessage |
| Broken-State DLQ Delivery | Failed |
| Failure Metric | DeadLetterErrors |
| Root Cause | IAM policy regression |
| Remediation | Restore SendMessage permission |
| Recovered-State DLQ Delivery | Successful |
| Original Event Payload | Preserved in SQS |
| Application Code Changes | None |
| Cleanup | Lambda, SQS, IAM, CloudWatch |
| Incident Status | Resolved after DLQ verification |

**Key Takeaway:** Production asynchronous Lambda reliability depends on correct retry configuration, IAM permissions, DLQ delivery, monitoring, and a defined failed-event recovery process.

---

## Official AWS Documentation

- [AWS Lambda — Asynchronous Invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html)
- [AWS Lambda — Asynchronous Errors and Retries](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html)
- [AWS Lambda — Configure Asynchronous Invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-configuring.html)
- [AWS Lambda — Retaining Failed Events](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html)
- [AWS Lambda — CloudWatch Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)
- [AWS CLI — Put Function Event Invoke Config](https://docs.aws.amazon.com/cli/latest/reference/lambda/put-function-event-invoke-config.html)
- [Amazon SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)