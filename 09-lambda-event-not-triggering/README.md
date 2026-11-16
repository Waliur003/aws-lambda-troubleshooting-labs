# Lab 09 — AWS Lambda Event Not Triggering

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and fix an AWS Lambda function that is not triggered when new objects are uploaded to Amazon S3.

AWS Lambda supports event-driven applications where services such as Amazon S3 automatically invoke a function when specific events occur.

In production, this architecture is commonly used for file processing, data ingestion, image processing, customer order handling, log analysis, and security automation.

However, a Lambda function can be healthy and correctly deployed but still never receive the expected events.

In this lab, we simulate a production incident where a company uploads customer order JSON files to an S3 bucket.

The Lambda function should automatically process files uploaded under the `orders/` prefix.

However, the S3 event notification is intentionally configured with the incorrect prefix `uploads/`.

As a result, files uploaded under `orders/` do not match the notification filter, so S3 does not send those object-created notifications to Lambda.

We investigate the issue using AWS CLI, S3 notification configurations, Lambda resource-based permissions, and CloudWatch Logs.

We also upload a control object under `uploads/` to confirm that the S3-to-Lambda integration works when the notification filter matches.

After identifying the root cause, we correct the prefix to `orders/`, upload a new test object, and verify successful Lambda invocation.

Finally, we remove the S3 notification, Lambda invocation permission, IAM role, S3 objects, bucket, and CloudWatch log group.

### Troubleshooting Workflow

```text
Create Private S3 Bucket
           |
           v
Create Lambda Execution Role
           |
           v
Deploy Python Lambda Function
           |
           v
Grant S3 Invoke Permission
           |
           v
Create S3 Event Notification
           |
           v
Configure Wrong Prefix: uploads/
           |
           v
Upload orders/order-1001.json
           |
           v
Object Upload Succeeds
           |
           v
Notification Filter Does Not Match
           |
           v
Lambda Not Triggered for Order
           |
           v
Investigate Notification Configuration
           |
           v
Verify Lambda Resource-Based Policy
           |
           v
Upload uploads/control-test.json
           |
           v
Control Event Successfully Triggers Lambda
           |
           v
Identify Prefix Mismatch
           |
           v
Correct Prefix to orders/
           |
           v
Upload New Order Object
           |
           v
Lambda Receives ObjectCreated Event
           |
           v
Verify CloudWatch Logs
           |
           v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-009 |
| Lab Name | Lambda Event Not Triggering |
| Difficulty | Intermediate |
| Primary Services | AWS Lambda, Amazon S3 |
| Supporting Services | IAM, Amazon CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Language | Python |
| Lambda Runtime | Python 3.13 |
| Function Name | `lambda-lab09-event-trigger` |
| Execution Role | `lambda-lab09-execution-role` |
| Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Timeout | 10 seconds |
| S3 Bucket | Unique dedicated private bucket |
| Event Type | `s3:ObjectCreated:Put` |
| Incorrect Prefix | `uploads/` |
| Correct Prefix | `orders/` |
| File Suffix | `.json` |
| S3 Notification ID | `lambda-lab09-object-created` |
| Lambda Permission SID | `AllowLab09S3Invoke` |
| CloudWatch Log Group | `/aws/lambda/lambda-lab09-event-trigger` |
| Log Retention | 7 days |
| Root Cause | Incorrect S3 event notification prefix |
| Remediation | Correct the prefix filter |
| Code Redeployment | Not required |
| Verification | Object-created event appears in Lambda logs |
| VPC | Not required |
| NAT Gateway | Not required |

### Learning Objectives

- Understand event-driven Lambda architecture.
- Configure S3 object-created event notifications.
- Understand object-key prefix and suffix filtering.
- Understand Lambda asynchronous invocation.
- Understand Lambda resource-based invocation policies.
- Distinguish invocation permissions from execution-role permissions.
- Reproduce an event-trigger failure.
- Verify successful S3 object uploads.
- Inspect bucket notification configurations.
- Investigate CloudWatch Logs for missing events.
- Test the S3-to-Lambda integration using control objects.
- Identify incorrect event filters.
- Correct event notifications without redeploying code.
- Verify successful asynchronous event delivery.
- Understand duplicate events and idempotent processing.
- Practice production root cause analysis.
- Clean up temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company uses Amazon S3 to store customer order files.

When a new JSON order file is uploaded under the `orders/` prefix, Amazon S3 should send an event notification to AWS Lambda.

The Lambda application receives the event, extracts the S3 object key, and records the order-processing event in CloudWatch Logs.

The infrastructure team deploys the Lambda function and configures the S3 notification.

However, customer order files are uploaded successfully without triggering the expected Lambda processing.

The operations team notices that new orders remain unprocessed.

The Cloud Engineer begins investigating.

The engineer confirms that:

- The S3 bucket exists.
- The customer order file was uploaded successfully.
- The Lambda function is Active.
- The event notification destination points to the correct Lambda function.
- The Lambda resource-based policy allows S3 invocation.
- No object-processing log appears for the uploaded order.

The engineer then inspects the S3 notification filter.

The configured prefix is:

```text
uploads/
```

But the customer order files are stored under:

```text
orders/
```

The notification configuration is syntactically valid, but its filter does not match the intended objects.

To isolate the issue, the engineer uploads a control file under `uploads/`.

That object successfully triggers Lambda, proving that the event destination, invocation permission, and Lambda handler work.

The engineer changes the notification prefix from `uploads/` to `orders/`.

A new order file is uploaded, and CloudWatch Logs confirm that Lambda receives the corresponding event.

### Incident Symptoms

- S3 upload succeeds.
- Uploaded object exists.
- Lambda function is Active.
- S3 event notification exists.
- Lambda resource-based invocation permission exists.
- Expected object-created event does not reach Lambda.
- CloudWatch has no matching order-processing message.
- Control objects matching the configured filter trigger Lambda.
- Correcting the filter restores the expected processing.

### Business Impact

Missing S3-to-Lambda events can cause:

- Delayed customer order processing.
- Unprocessed uploaded files.
- Interrupted data ingestion.
- Failed serverless automation.
- Missing file-validation workflows.
- Incomplete document processing.
- Delayed security scanning.
- Missing operational notifications.
- Increased manual intervention.

### Objective

Identify the incorrect S3 notification prefix, restore event-driven processing, and verify that new matching objects successfully invoke Lambda.

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
                    Amazon S3
                          |
                          v
              Upload Customer Order
                          |
                          v
               orders/order-1001.json
                          |
                          v
               S3 ObjectCreated:Put
                          |
                          v
              Event Notification Filter
                          |
              +-----------+-----------+
              |                       |
              v                       v
       Configured Prefix        Actual Object Key
          uploads/                 orders/
              |                       |
              +-----------+-----------+
                          |
                          v
                    No Match
                          |
                          v
               Notification Not Sent
                          |
                          X
                          |
                       Lambda
                          |
                          v
               No Order Processing Log
```

### Recovered Architecture

```text
                    Cloud Engineer
                          |
                          v
                       AWS CLI
                          |
                          v
                    Amazon S3
                          |
                          v
                 Upload New Order
                          |
                          v
              orders/recovery-xxx.json
                          |
                          v
               S3 ObjectCreated:Put
                          |
                          v
              Event Notification Filter
                          |
                          v
                 Prefix = orders/
                 Suffix = .json
                          |
                          v
                     Match Found
                          |
                          v
              Lambda Resource-Based Policy
                          |
                          v
                   Invoke Allowed
                          |
                          v
                AWS Lambda Function
                          |
                          v
                  Python Handler
                          |
                          v
                Extract Bucket and Key
                          |
                          v
                  CloudWatch Logs
                          |
                          v
                Event Processing Verified
```

### AWS Components

| Component | Purpose |
|---|---|
| Amazon S3 | Stores customer order files |
| S3 Event Notifications | Detects matching object-created events |
| Prefix Filter | Matches the beginning of object keys |
| Suffix Filter | Matches `.json` files |
| Lambda Resource-Based Policy | Allows the S3 service to invoke Lambda |
| AWS Lambda | Processes S3 event records |
| IAM Execution Role | Allows the function to write logs |
| Python urllib.parse | Decodes S3 event object keys |
| Amazon CloudWatch Logs | Records received object events |
| AWS CLI | Creates, inspects, and updates AWS resources |

---

## 4. Understanding S3-to-Lambda Event Notifications

### What Is an Event-Driven Architecture?

An event-driven architecture allows services to respond automatically when events occur.

In this lab, an S3 object upload generates an event that may invoke Lambda.

### What Is an S3 Event Notification?

An S3 event notification is a configuration that sends information about selected bucket events to supported destinations.

Example event:

```text
s3:ObjectCreated:Put
```

### What Is a Prefix Filter?

A prefix filter matches the beginning of an object key.

Example:

```text
orders/
```

Matches:

```text
orders/order-1001.json
orders/recovery-001.json
```

Does not match:

```text
uploads/order-1001.json
```

### What Is a Suffix Filter?

A suffix filter matches the end of an object key.

Example:

```text
.json
```

Matches JSON filenames but not filenames ending in `.csv` or `.txt`.

### How Are Prefix and Suffix Filters Combined?

An object must satisfy both configured filters.

For this lab:

```text
Prefix: orders/
Suffix: .json
```

### What Happens if the Filter Does Not Match?

The object event is not sent to the configured Lambda destination.

### What Is a Lambda Resource-Based Policy?

A Lambda resource-based policy controls which principals and AWS services can invoke the function.

For S3 notifications, the S3 service principal must be authorized to invoke the function.

### Execution Role vs. Resource-Based Policy

| Policy | Purpose |
|---|---|
| Lambda execution role | Controls what Lambda can access while running |
| Lambda resource-based policy | Controls which services or principals may invoke Lambda |

These permissions are different.

### Does Lambda Need s3:GetObject to Receive an S3 Event?

No.

The handler in this lab only reads metadata included in the event.

It does not retrieve the actual S3 object body.

An application that downloads object contents would need the appropriate S3 object permissions.

### Are S3 Event Notifications Synchronous?

S3 invokes Lambda asynchronously.

Event delivery and CloudWatch log availability are not instantaneous.

### Can S3 Send Duplicate Notifications?

Yes.

S3 event notifications are designed for at-least-once delivery.

Applications should support idempotent event processing.

### Are Older Events Replayed After Fixing a Notification?

No.

Changing the notification filter does not automatically replay events generated before the correction.

A new matching event must be generated to test recovery.

### Can S3 Notification Updates Affect Other Integrations?

Yes.

`put-bucket-notification-configuration` replaces the complete bucket notification configuration.

Engineers must preserve unrelated notifications when working with shared production buckets.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- Bash.
- ZIP and unzip.
- Permissions to manage S3 buckets and notifications.
- Permissions to deploy Lambda functions.
- Permissions to manage IAM roles and Lambda invocation permissions.
- CloudWatch Logs access.

### Relevant AWS Permissions

```text
sts:GetCallerIdentity

s3:CreateBucket
s3:PutBucketPublicAccessBlock
s3:GetBucketPublicAccessBlock
s3:PutBucketTagging
s3:GetBucketTagging
s3:PutBucketNotification
s3:GetBucketNotification
s3:PutObject
s3:GetObject
s3:ListBucket
s3:DeleteObject
s3:DeleteBucket

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
lambda:InvokeFunction
lambda:GetPolicy
lambda:AddPermission
lambda:RemovePermission
lambda:ListTags
lambda:DeleteFunction

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

### Safety Rules

- Use a dedicated lab S3 bucket.
- Keep S3 Block Public Access enabled.
- Never modify production event notifications.
- Do not overwrite shared notification configurations.
- Scope Lambda invocation permission to the dedicated bucket and account.
- Use fabricated test orders.
- Do not expose AWS credentials.
- Avoid recursive S3-to-Lambda event loops.
- Verify tags before cleanup.
- Remove all temporary AWS resources.

### Cost Considerations

This lab uses small S3 objects, short Lambda executions, and CloudWatch Logs.

Potential charges include S3 requests and storage, Lambda requests and duration, and CloudWatch log ingestion or retention.

No EC2 instances, RDS databases, NAT Gateways, or custom VPC resources are required.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create the Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 09-lambda-event-not-triggering

cd 09-lambda-event-not-triggering
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
zip -v

aws sts get-caller-identity
```

Install missing ZIP utilities if necessary:

```bash
sudo apt update
sudo apt install -y zip unzip
```

### Step 3 — Configure AWS Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab09"

export FUNCTION_NAME="lambda-lab09-event-trigger"

export ROLE_NAME="lambda-lab09-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export BUCKET_NAME="lambda-lab09-${ACCOUNT_ID}-$(date -u +%Y%m%d%H%M%S)"

export WRONG_PREFIX="uploads/"
export CORRECT_PREFIX="orders/"

export NOTIFICATION_ID="lambda-lab09-object-created"

export PERMISSION_SID="AllowLab09S3Invoke"
```

### Step 4 — Save Resource Configuration

```bash
cat > lab09-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export BUCKET_NAME="$BUCKET_NAME"
export WRONG_PREFIX="$WRONG_PREFIX"
export CORRECT_PREFIX="$CORRECT_PREFIX"
export NOTIFICATION_ID="$NOTIFICATION_ID"
export PERMISSION_SID="$PERMISSION_SID"
EOF
```

Restore later:

```bash
source lab09-resources.env
```

### Step 5 — Check Existing Lambda Resources

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Both should be absent in a fresh lab.

---

## 7. Create the Private S3 Bucket

### Step 1 — Create Bucket

```bash
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

### Step 2 — Configure S3 Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --region "$AWS_REGION"
```

### Step 3 — Add Project Tags

```bash
aws s3api put-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --tagging "TagSet=[{Key=Project,Value=$PROJECT_TAG}]" \
  --region "$AWS_REGION"
```

### Step 4 — Verify S3 Security

```bash
aws s3api get-public-access-block \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

```bash
aws s3api get-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

All public-access blocking settings should be enabled.

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
  --description "Lambda event notification Lab 09 execution role" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach CloudWatch Permissions

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 4 — Verify Policy Attachment

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

## 9. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 09 invoked")

    records = event.get("Records", [])

    if event.get("Event") == "s3:TestEvent":
        logger.info("S3 notification test event received")

        return {
            "statusCode": 200,
            "message": "S3 test event received"
        }

    processed = []

    for record in records:
        bucket = record["s3"]["bucket"]["name"]

        encoded_key = record["s3"]["object"]["key"]

        object_key = unquote_plus(encoded_key)

        event_name = record.get("eventName", "unknown")

        logger.info(
            "LAB09_OBJECT_EVENT bucket=%s key=%s event=%s",
            bucket,
            object_key,
            event_name
        )

        processed.append({
            "bucket": bucket,
            "key": object_key,
            "event": event_name
        })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "S3 event processed",
            "processed_records": processed
        })
    }
```

### Step 2 — Understand Event Parsing

The application accesses the S3 event record:

```python
bucket = record["s3"]["bucket"]["name"]

encoded_key = record["s3"]["object"]["key"]
```

The object key is decoded using:

```python
object_key = unquote_plus(encoded_key)
```

### Step 3 — Understand Object Event Logging

The function writes:

```text
LAB09_OBJECT_EVENT
```

This message identifies actual object-created events.

It allows us to distinguish customer order events from notification configuration test events.

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

---

## 10. Deploy Lambda

### Step 1 — Create Lambda Function

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

### Step 3 — Retrieve Function ARN

```bash
export FUNCTION_ARN=$(aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --query Configuration.FunctionArn \
  --output text \
  --region "$AWS_REGION")

echo "$FUNCTION_ARN"

echo "export FUNCTION_ARN=$FUNCTION_ARN" >> lab09-resources.env
```

### Step 4 — Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 5 — Configure Log Retention

```bash
aws logs put-retention-policy \
  --log-group-name "$LOG_GROUP" \
  --retention-in-days 7 \
  --region "$AWS_REGION"
```

---

## 11. Grant S3 Permission to Invoke Lambda

### Step 1 — Add Resource-Based Invocation Permission

```bash
aws lambda add-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id "$PERMISSION_SID" \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET_NAME" \
  --source-account "$ACCOUNT_ID" \
  --region "$AWS_REGION"
```

### Step 2 — Verify Lambda Resource-Based Policy

```bash
aws lambda get-policy \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Confirm:

```text
Principal: s3.amazonaws.com
Action: lambda:InvokeFunction
Source ARN: Lab S3 bucket
```

### Why This Permission Matters

Amazon S3 requires permission to invoke Lambda.

The execution role's CloudWatch logging policy does not grant S3 invocation permission.

The two permission systems serve different purposes.

### Security Considerations

The permission is restricted to the dedicated lab bucket and AWS account.

This is safer than granting unrestricted S3 service invocation permission.

---

## 12. Create the Broken S3 Notification

### Step 1 — Generate Broken Notification JSON

```bash
python3 - <<'PY'
import json
import os

configuration = {
    "LambdaFunctionConfigurations": [
        {
            "Id": os.environ["NOTIFICATION_ID"],
            "LambdaFunctionArn": os.environ["FUNCTION_ARN"],
            "Events": [
                "s3:ObjectCreated:Put"
            ],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "prefix",
                            "Value": "uploads/"
                        },
                        {
                            "Name": "suffix",
                            "Value": ".json"
                        }
                    ]
                }
            }
        }
    ]
}

with open("broken-notification.json", "w") as file:
    json.dump(configuration, file, indent=2)

print("Broken notification configuration created")
PY
```

### Step 2 — Verify the Incorrect Filter

```bash
python3 -m json.tool broken-notification.json
```

The configuration uses:

```text
Prefix: uploads/
Suffix: .json
```

### Step 3 — Apply the Broken Notification

```bash
aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --notification-configuration file://broken-notification.json \
  --region "$AWS_REGION"
```

**Warning:** This command replaces the complete notification configuration for the bucket. The lab uses a dedicated bucket, so there are no unrelated notifications to preserve.

### Step 4 — Inspect the Configuration

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
Event: s3:ObjectCreated:Put
Prefix: uploads/
Suffix: .json
Destination: Lambda function ARN
```

### Step 5 — Save Broken Configuration Evidence

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  > lab09-broken-notification-evidence.json
```

### Broken-State Verification

| Setting | Expected |
|---|---|
| S3 notification | Created |
| Event type | ObjectCreated:Put |
| Destination | Correct Lambda |
| Invocation permission | Correct |
| Notification prefix | `uploads/` |
| Application object prefix | `orders/` |
| Notification filter match | No |

---

## 13. Fault Injection — Upload an Order That Does Not Trigger Lambda

### Step 1 — Create Test Order

Save as `order-1001.json`:

```json
{
  "order_id": "ORDER-1001",
  "customer": "Test Customer",
  "status": "pending",
  "total": 125.50
}
```

### Step 2 — Validate JSON

```bash
python3 -m json.tool order-1001.json
```

### Step 3 — Upload the Order

```bash
export BROKEN_OBJECT_KEY="orders/order-1001.json"

aws s3api put-object \
  --bucket "$BUCKET_NAME" \
  --key "$BROKEN_OBJECT_KEY" \
  --body order-1001.json \
  --server-side-encryption AES256 \
  --region "$AWS_REGION"
```

### Step 4 — Verify Object Upload

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "$BROKEN_OBJECT_KEY" \
  --region "$AWS_REGION"
```

The object upload succeeds.

### Step 5 — Inspect Lambda CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 10m \
  --region "$AWS_REGION"
```

A test notification may appear during the notification configuration process.

That is different from a real object-processing event.

### Step 6 — Search for the Order Event

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB09_OBJECT_EVENT" "order-1001.json"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

Expected after allowing for log delivery:

```json
[]
```

### Step 7 — Observe Multiple Times

```bash
for attempt in 1 2 3 4 5 6; do
  echo "Checking event delivery: attempt $attempt"

  aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --filter-pattern '"LAB09_OBJECT_EVENT" "order-1001.json"' \
    --query 'events[].message' \
    --output json \
    --region "$AWS_REGION"

  sleep 5
done
```

The order should not produce a matching processing log because its key fails the configured prefix filter.

Absence of logs by itself does not conclusively prove non-delivery in every environment. Here, the notification configuration and object key independently demonstrate the filter mismatch.

### Step 8 — Save Failure Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab09-broken-cloudwatch-evidence.json
```

### Incident Findings

| Investigation | Result |
|---|---|
| S3 object upload | Successful |
| Object exists | Yes |
| Lambda Active | Yes |
| Invocation permission | Configured |
| Notification destination | Correct |
| Configured prefix | `uploads/` |
| Uploaded object prefix | `orders/` |
| Matching object-processing event | Not observed |
| Root cause | Prefix mismatch |

---

## 14. Control Test — Verify S3-to-Lambda Integration

### Purpose

Before changing the notification, verify that S3 can successfully invoke Lambda when an object matches the existing filter.

This helps isolate the issue to event filtering.

### Step 1 — Upload a Matching Control Object

```bash
export CONTROL_OBJECT_KEY="uploads/control-test.json"

aws s3api put-object \
  --bucket "$BUCKET_NAME" \
  --key "$CONTROL_OBJECT_KEY" \
  --body order-1001.json \
  --server-side-encryption AES256 \
  --region "$AWS_REGION"
```

### Step 2 — Inspect Control Event Logs

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"LAB09_OBJECT_EVENT" "control-test.json"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Poll for Event Delivery

```bash
for attempt in $(seq 1 12); do
  RESULT=$(aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --filter-pattern '"LAB09_OBJECT_EVENT" "control-test.json"' \
    --query 'length(events)' \
    --output text \
    --region "$AWS_REGION")

  if [ "$RESULT" -gt 0 ]; then
    echo "SUCCESS: Control event triggered Lambda"
    break
  fi

  echo "Waiting for control event: $attempt"
  sleep 5
done
```

### Control Test Findings

A successfully processed control event confirms:

- The bucket notification can deliver matching events.
- The Lambda destination is valid.
- S3 invocation permission works.
- The Lambda handler executes.
- CloudWatch receives the object's processing log.

The difference between the successful control upload and failed order upload is the object-key prefix.

---

## 15. Root Cause Analysis

### Root Cause

The S3 event notification was configured to match JSON files under:

```text
uploads/
```

However, the application stored customer orders under:

```text
orders/
```

The S3 event filter did not match the uploaded order's key.

Consequently, S3 did not send that object-created notification to Lambda.

### Root Cause Diagram

```text
S3 Object Uploaded
        |
        v
orders/order-1001.json
        |
        v
ObjectCreated:Put
        |
        v
Check Notification Filter
        |
        v
Expected Prefix: uploads/
        |
        v
Actual Prefix: orders/
        |
        v
Filter Mismatch
        |
        v
No Notification Sent
        |
        v
Lambda Not Triggered for Order
```

### Five Whys

**Why 1 — Why wasn't the order processed?**

The Lambda function did not receive a notification for the order upload.

**Why 2 — Why wasn't the notification sent?**

The object key did not match the configured filter.

**Why 3 — Why didn't the filter match?**

It used `uploads/` instead of `orders/`.

**Why 4 — Why was the incorrect configuration not detected?**

The notification was accepted, but an application-specific upload test was not performed.

**Why 5 — How can this be prevented?**

Manage notifications through Infrastructure as Code and perform end-to-end event delivery tests after deployment.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-009 |
| Services | Amazon S3, AWS Lambda |
| Event | ObjectCreated:Put |
| Expected prefix | `orders/` |
| Configured prefix | `uploads/` |
| Lambda execution role | Correct |
| Lambda invocation permission | Correct |
| Handler | Correct |
| Root cause | Incorrect notification filter |
| Remediation | Change prefix to `orders/` |
| Code Redeployment | Not required |

---

## 16. Remediation — Correct the Notification Filter

### Step 1 — Generate Corrected Notification JSON

```bash
python3 - <<'PY'
import json
import os

configuration = {
    "LambdaFunctionConfigurations": [
        {
            "Id": os.environ["NOTIFICATION_ID"],
            "LambdaFunctionArn": os.environ["FUNCTION_ARN"],
            "Events": [
                "s3:ObjectCreated:Put"
            ],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "prefix",
                            "Value": "orders/"
                        },
                        {
                            "Name": "suffix",
                            "Value": ".json"
                        }
                    ]
                }
            }
        }
    ]
}

with open("recovered-notification.json", "w") as file:
    json.dump(configuration, file, indent=2)

print("Corrected notification configuration created")
PY
```

### Step 2 — Validate the JSON

```bash
python3 -m json.tool recovered-notification.json
```

Confirm:

```text
Prefix = orders/
Suffix = .json
```

### Step 3 — Apply the Corrected Configuration

```bash
aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --notification-configuration file://recovered-notification.json \
  --region "$AWS_REGION"
```

### Step 4 — Verify S3 Notification

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
Event = s3:ObjectCreated:Put
Prefix = orders/
Suffix = .json
Destination = Lambda function ARN
```

### Step 5 — Save Recovered Configuration Evidence

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  > lab09-recovered-notification-evidence.json
```

### Before and After

| Setting | Broken | Recovered |
|---|---|---|
| Event type | ObjectCreated:Put | ObjectCreated:Put |
| Prefix | uploads/ | orders/ |
| Suffix | .json | .json |
| Lambda ARN | Correct | Unchanged |
| Invocation permission | Correct | Unchanged |
| Event filter | Incorrect | Correct |
| Python code | Unchanged | Unchanged |

---

## 17. Verify Successful Event Delivery

### Step 1 — Generate a New Order Key

Changing an S3 notification does not replay older events.

Create a new matching object:

```bash
export RECOVERY_OBJECT_KEY="orders/recovery-$(date -u +%Y%m%d%H%M%S).json"

echo "$RECOVERY_OBJECT_KEY"
```

### Step 2 — Upload Recovery Test

```bash
aws s3api put-object \
  --bucket "$BUCKET_NAME" \
  --key "$RECOVERY_OBJECT_KEY" \
  --body order-1001.json \
  --server-side-encryption AES256 \
  --region "$AWS_REGION"
```

### Step 3 — Verify the Object

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "$RECOVERY_OBJECT_KEY" \
  --region "$AWS_REGION"
```

### Step 4 — Poll CloudWatch for the Exact Object Key

```bash
export EVENT_FOUND="false"

for attempt in $(seq 1 12); do
  RESULT=$(aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --filter-pattern '"LAB09_OBJECT_EVENT"' \
    --query 'events[].message' \
    --output text \
    --region "$AWS_REGION")

  if printf '%s\n' "$RESULT" | grep -Fq "$RECOVERY_OBJECT_KEY"; then
    EVENT_FOUND="true"
    echo "SUCCESS: S3 event delivered to Lambda"
    break
  fi

  echo "Checking recovery event: $attempt"
  sleep 5
done

if [ "$EVENT_FOUND" != "true" ]; then
  echo "Recovery event not observed; investigate delivery"
fi
```

### Step 5 — Inspect Lambda Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected message resembles:

```text
Lambda Lab 09 invoked
LAB09_OBJECT_EVENT bucket=lambda-lab09-... key=orders/recovery-....json event=ObjectCreated:Put
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab09-recovered-cloudwatch-evidence.json
```

### Recovery Verification

| Check | Broken | Recovered |
|---|---|---|
| S3 object upload | Successful | Successful |
| Lambda Active | Yes | Yes |
| Notification configured | Yes | Yes |
| Prefix | Incorrect | Correct |
| Matching order event | Not sent | Sent |
| Object-processing log | Absent | Present |
| Application code change | None | None |

**Recovery is confirmed when the newly uploaded order object generates a matching Lambda processing log.**

---

## 18. Production Troubleshooting Best Practices

### Investigation Checklist

1. Verify AWS account and Region.
2. Identify the affected S3 bucket.
3. Confirm the uploaded object exists.
4. Inspect the actual object key.
5. Identify the expected event type.
6. Read the bucket notification configuration.
7. Verify the Lambda destination ARN.
8. Compare configured prefix and suffix filters.
9. Inspect Lambda resource-based permissions.
10. Verify the Lambda function is Active.
11. Review CloudWatch Logs.
12. Allow for asynchronous delivery.
13. Upload a matching control object.
14. Compare successful and unsuccessful object keys.
15. Identify the root cause.
16. Correct the notification configuration.
17. Upload a new matching object.
18. Verify object-specific Lambda logs.
19. Document findings.
20. Clean up temporary AWS resources.

### Common S3-to-Lambda Trigger Failures

| Problem | Symptom | Investigation |
|---|---|---|
| Missing notification | Lambda never receives expected events | Inspect S3 notification |
| Wrong prefix | Some object keys do not trigger | Check prefix filter |
| Wrong suffix | Wrong file types ignored | Check suffix filter |
| Wrong event type | Upload method not matched | Inspect event type |
| Incorrect Lambda ARN | Wrong destination | Inspect notification |
| Missing invoke permission | S3 cannot invoke Lambda | Inspect Lambda policy |
| Lambda runtime error | Event delivered but processing fails | Check CloudWatch Logs |
| Region mismatch | Destination configuration issue | Check bucket and Lambda Region |
| Delivery delay | Logs appear later | Poll for delivery |
| Duplicate notifications | Same object processed more than once | Implement idempotency |
| Existing object unchanged | No new event | Generate a new upload |

### Production Recommendations

- Manage S3 notifications through Terraform or CloudFormation.
- Review prefix and suffix filters carefully.
- Use precise Lambda resource-based permissions.
- Keep S3 buckets private.
- Run post-deployment object-upload tests.
- Use idempotent event processors.
- Monitor Lambda Errors and invocation activity.
- Avoid recursive trigger configurations.
- Preserve existing notifications when updating shared buckets.
- Consider Amazon EventBridge for more complex event routing.

---

## 19. Cloud Security Engineering Considerations

### S3 Bucket Privacy

The lab bucket uses S3 Block Public Access.

The bucket does not need public accessibility to invoke Lambda.

### Least-Privilege Invocation Permissions

The Lambda resource-based policy is scoped to the specific S3 bucket and AWS account.

### Execution-Role Permissions

The handler only logs event metadata.

It does not require S3 object read permissions.

### Avoiding Recursive Events

A Lambda function that writes objects into a triggering bucket can create repeated invocations if the output keys match the notification filter.

Production implementations should separate input and output prefixes or buckets when appropriate.

### Idempotency

Duplicate S3 notifications may occur.

A production processor should avoid processing the same operation multiple times in a harmful way.

### Monitoring

CloudWatch Logs, Lambda metrics, and suitable event-delivery monitoring can help detect missing or failed processing.

### Configuration Integrity

Unexpected changes to S3 notification configuration can interrupt security scanning, monitoring, or automation.

Use controlled deployment processes and AWS CloudTrail for relevant change auditing.

---

## 20. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 09.

### Step 1 — Verify S3 Bucket Ownership

```bash
aws s3api head-bucket \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --region "$AWS_REGION"
```

### Step 2 — Verify Bucket Tags

```bash
aws s3api get-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Confirm:

```text
Project = Lambda-Troubleshooting-Lab09
```

### Step 3 — Verify Lambda Tags

```bash
aws lambda list-tags \
  --resource "$FUNCTION_ARN" \
  --region "$AWS_REGION"
```

### Step 4 — Verify IAM Role Tags

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

### Step 5 — Remove S3 Notification

Because this is a dedicated lab bucket with no unrelated notifications:

```bash
echo '{}' > empty-notification.json

aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --notification-configuration file://empty-notification.json \
  --region "$AWS_REGION"
```

Verify:

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected:

```json
{}
```

### Step 6 — Remove Lambda Invocation Permission

```bash
aws lambda remove-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id "$PERMISSION_SID" \
  --region "$AWS_REGION"
```

### Step 7 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 8 — Detach CloudWatch Logging Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 9 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 10 — List S3 Objects

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET_NAME" \
  --query 'Contents[].Key' \
  --output json \
  --region "$AWS_REGION"
```

Verify that the objects belong to this lab.

### Step 11 — Delete Broken Test Object

```bash
aws s3api delete-object \
  --bucket "$BUCKET_NAME" \
  --key "orders/order-1001.json" \
  --region "$AWS_REGION"
```

### Step 12 — Delete Control Object

```bash
aws s3api delete-object \
  --bucket "$BUCKET_NAME" \
  --key "uploads/control-test.json" \
  --region "$AWS_REGION"
```

### Step 13 — Delete Recovery Object

```bash
aws s3api delete-object \
  --bucket "$BUCKET_NAME" \
  --key "$RECOVERY_OBJECT_KEY" \
  --region "$AWS_REGION"
```

If you opened a new terminal, recover the generated recovery key from your recorded lab output before deleting it.

### Step 14 — Delete S3 Bucket

```bash
aws s3api delete-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

If S3 reports `BucketNotEmpty`, inspect remaining objects or versions before retrying.

### Step 15 — Delete CloudWatch Logs

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 16 — Verify Cleanup

Check Lambda:

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected: `ResourceNotFoundException`.

Check IAM:

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected: `NoSuchEntity`.

Check S3:

```bash
aws s3api head-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected: the bucket no longer exists.

Check CloudWatch:

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
| S3 notification | Removed |
| Lambda invoke permission | Removed |
| Lambda function | Deleted |
| IAM execution role | Deleted |
| S3 original order | Deleted |
| S3 control object | Deleted |
| S3 recovery object | Deleted |
| S3 bucket | Deleted |
| CloudWatch log group | Deleted |
| VPC | Not created |
| NAT Gateway | Not created |
| RDS | Not created |

---

## 21. Interview Questions and Answers

### Q1. Why can an S3 event fail to trigger Lambda?

An incorrect event notification, prefix or suffix mismatch, missing invocation permission, invalid destination, or event delivery issue can prevent the expected invocation.

### Q2. What was the root cause in this lab?

The S3 notification prefix was `uploads/`, but the application uploaded files under `orders/`.

### Q3. What is an S3 prefix filter?

A filter that matches the beginning of an object key.

### Q4. What is an S3 suffix filter?

A filter that matches the ending of an object key, such as `.json`.

### Q5. What permission allows Amazon S3 to invoke Lambda?

A Lambda resource-based permission granting `lambda:InvokeFunction` to `s3.amazonaws.com` for the intended source.

### Q6. Does a Lambda execution role control who can invoke the function?

No. Invocation authorization is managed separately, including through Lambda resource-based policies.

### Q7. Does Lambda need s3:GetObject just to receive an S3 event?

No. It needs object-read permission only if the application retrieves object contents.

### Q8. Why did the control object trigger Lambda?

The control object's key matched the configured `uploads/` prefix and `.json` suffix.

### Q9. Why upload a new object after remediation?

Updating S3 notifications does not replay earlier object-created events.

### Q10. Are S3 event notifications delivered exactly once?

No. Duplicate notifications are possible, so applications should be idempotent.

### Q11. Can updating an S3 notification configuration affect unrelated integrations?

Yes. The update replaces the bucket's complete notification configuration.

### Q12. What AWS tools are useful for troubleshooting event triggers?

AWS CLI, S3 notification configuration, Lambda resource-based policy, CloudWatch Logs, and Lambda metrics.

### Q13. What is the difference between S3 delivery and Lambda processing failure?

A delivery failure prevents the expected invocation. A processing failure occurs after an event reaches Lambda and the handler encounters an error.

### Q14. How can you prevent recursive Lambda invocations?

Use separate input and output buckets or prefixes, and ensure output objects do not match the trigger filter.

### Q15. How would you explain this lab in an interview?

I created an event-driven architecture using Amazon S3 and AWS Lambda.

I configured the S3 bucket to invoke Lambda when a JSON object was created.

I intentionally used an incorrect notification prefix, so customer order files uploaded under orders/ did not trigger the Lambda function.

I investigated the S3 notification configuration, Lambda resource-based permissions, object keys, and CloudWatch Logs.

I uploaded a control file under uploads/ and confirmed that it successfully triggered Lambda.

This proved that the event destination and invocation permission worked correctly.

I identified the notification prefix mismatch as the root cause.

I corrected the prefix to orders/, uploaded a new customer order file, and verified that Lambda received the event through CloudWatch Logs.

Finally, I removed the S3 notification, invocation permission, Lambda function, IAM role, S3 bucket, and CloudWatch log group.

---

## 22. Repository Structure

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
│
├── 09-lambda-event-not-triggering/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── order-1001.json
│   ├── empty-notification.json
│   ├── broken-notification.json
│   ├── recovered-notification.json
│   ├── function.zip
│   ├── lab09-resources.env
│   ├── lab09-broken-notification-evidence.json
│   ├── lab09-recovered-notification-evidence.json
│   ├── lab09-broken-cloudwatch-evidence.json
│   └── lab09-recovered-cloudwatch-evidence.json
│
├── 10-lambda-dependency-import-error/
├── 11-lambda-concurrency-throttling/
└── 12-lambda-async-retry-dlq-failure/
```

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Production incident documentation |
| lambda_function.py | S3 event-processing Lambda application |
| lambda-trust-policy.json | Lambda execution-role trust policy |
| order-1001.json | Fabricated test order |
| empty-notification.json | Cleanup notification configuration |
| broken-notification.json | Initial incorrect S3 filter |
| recovered-notification.json | Corrected S3 filter |
| function.zip | Generated deployment package |
| lab09-resources.env | Local AWS resource identifiers |
| lab09-broken-notification-evidence.json | Incorrect notification evidence |
| lab09-recovered-notification-evidence.json | Corrected notification evidence |
| lab09-broken-cloudwatch-evidence.json | Initial event investigation logs |
| lab09-recovered-cloudwatch-evidence.json | Successful event-delivery logs |

### Recommended Public GitHub Files

```text
09-lambda-event-not-triggering/
├── README.md
├── lambda_function.py
├── lambda-trust-policy.json
├── order-1001.json
└── empty-notification.json
```

The generated notification files contain a real Lambda ARN and should be sanitized or replaced with placeholder examples before publishing.

### Recommended Root .gitignore

Add these rules to the repository's `.gitignore`:

```gitignore
# Lambda Lab 09
09-lambda-event-not-triggering/function.zip
09-lambda-event-not-triggering/lab09-resources.env
09-lambda-event-not-triggering/lab09-*-evidence.json
09-lambda-event-not-triggering/broken-notification.json
09-lambda-event-not-triggering/recovered-notification.json

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

These rules exclude generated, account-specific evidence and configuration files.

---

## 23. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how incorrect Amazon S3 event notification filters can prevent AWS Lambda from receiving the expected events.

We created a private S3 bucket and deployed a Python Lambda function.

We granted Amazon S3 permission to invoke the function through a Lambda resource-based policy.

We intentionally configured the S3 event notification with the prefix uploads/.

When a customer order was uploaded under orders/, the notification filter did not match.

The Lambda function did not process that order.

We investigated the bucket notification, Lambda invocation permissions, object keys, and CloudWatch Logs.

We then uploaded a control object that matched the incorrect filter and confirmed that Lambda processed it successfully.

This demonstrated that the integration worked, but the filter was incorrect.

We corrected the notification prefix to orders/ and uploaded a new order file.

CloudWatch Logs confirmed that Lambda received the new object-created event.

Finally, we removed all temporary AWS resources.

**Key Lesson:** When an event-driven Lambda function does not trigger, engineers must investigate the event source configuration and filtering rules, not just the Lambda function itself.

### Skills Demonstrated

- AWS Lambda
- Amazon S3
- S3 Event Notifications
- ObjectCreated events
- Prefix filtering
- Suffix filtering
- Lambda resource-based policies
- IAM execution roles
- AWS CLI v2
- Linux Bash
- Python 3.13
- S3 event JSON parsing
- URL-decoded S3 object keys
- CloudWatch Logs
- Asynchronous event processing
- Event delivery troubleshooting
- Idempotency concepts
- Root cause analysis
- Notification remediation
- Recovery verification
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-009 |
| Scenario | Lambda Event Not Triggering |
| Lambda Function | lambda-lab09-event-trigger |
| Event Source | Amazon S3 |
| Event Type | ObjectCreated:Put |
| Incorrect Prefix | uploads/ |
| Correct Prefix | orders/ |
| Root Cause | Notification filter mismatch |
| Remediation | Correct S3 event notification |
| Control Event | Successfully invokes Lambda |
| Recovery Event | Successfully invokes Lambda |
| Code Redeployment | Not required |
| Cleanup | Lambda, IAM, S3, CloudWatch |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** Reliable event-driven cloud applications require correct event source configuration, scoped invocation permissions, end-to-end testing, monitoring, and idempotent processing.

---

## Official AWS Documentation

- [AWS Lambda — Process Amazon S3 Events](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)
- [Amazon S3 — Configuring Event Notification Filtering](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-filtering.html)
- [Amazon S3 — Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html)
- [AWS CLI — Put Bucket Notification Configuration](https://docs.aws.amazon.com/cli/latest/reference/s3api/put-bucket-notification-configuration.html)
- [AWS Lambda — Resource-Based Permissions](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html)
- [AWS Lambda — CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)