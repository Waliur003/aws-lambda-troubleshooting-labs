# Lab 05 — AWS Lambda AccessDenied

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda `AccessDenied` error when a Python application attempts to retrieve an object from Amazon S3.

AWS Lambda functions use IAM execution roles to access other AWS services. A function may deploy successfully, start running, and write logs while still lacking permission to perform a required AWS API operation.

In production, these permission problems can interrupt applications, background processing, automated workflows, and service integrations.

In this lab, we simulate a production incident involving a Python Lambda function that processes customer orders stored in a private Amazon S3 bucket.

The Lambda function uses boto3 to retrieve a JSON order file.

However, the execution role initially contains only CloudWatch logging permissions and does not allow `s3:GetObject`.

When the function invokes the S3 GetObject API, Amazon S3 rejects the request with `AccessDenied`.

We investigate the Lambda invocation response, CloudWatch Logs, IAM execution role, attached policies, S3 object, and bucket security configuration.

After identifying the missing permission, we create a least-privilege IAM policy allowing the function to read only the required S3 object.

We then repeat the invocation and verify successful order retrieval.

An additional test confirms that the Lambda function cannot read another object outside its authorized scope.

Finally, we remove the temporary Lambda function, IAM execution role, S3 objects, S3 bucket, and CloudWatch log group.

### Troubleshooting Workflow

```text
Create Private S3 Bucket
           |
           v
Upload Customer Order JSON
           |
           v
Create Lambda Execution Role
           |
           v
Attach CloudWatch Logging Policy
           |
           v
Do Not Grant s3:GetObject
           |
           v
Deploy Python Lambda Function
           |
           v
Invoke Lambda
           |
           v
boto3 GetObject Request
           |
           v
S3 AccessDenied
           |
           v
Investigate CloudWatch Logs
           |
           v
Inspect Lambda Execution Role
           |
           v
Identify Missing IAM Permission
           |
           v
Create Least-Privilege IAM Policy
           |
           v
Grant s3:GetObject for One Object
           |
           v
Invoke Lambda Again
           |
           v
Successful Order Retrieval
           |
           v
Test Access to Restricted Object
           |
           v
Verify AccessDenied
           |
           v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-005 |
| Lab Name | AWS Lambda AccessDenied |
| Difficulty | Beginner to Intermediate |
| Primary Services | AWS Lambda, Amazon S3, IAM |
| Monitoring | Amazon CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Interface | AWS CLI v2 |
| Programming Language | Python |
| AWS SDK | boto3 |
| Lambda Runtime | Python 3.13 |
| Function Name | `lambda-lab05-access-denied` |
| Execution Role | `lambda-lab05-execution-role` |
| IAM Inline Policy | `lambda-lab05-s3-read-policy` |
| Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Timeout | 15 seconds |
| S3 Bucket | Unique dedicated lab bucket |
| Required Object | `orders/order-1001.json` |
| Restricted Object | `orders/restricted-order.json` |
| Bucket Encryption | SSE-S3 |
| Bucket Public Access | Blocked |
| CloudWatch Log Group | `/aws/lambda/lambda-lab05-access-denied` |
| Initial IAM Policy | AWSLambdaBasicExecutionRole |
| Missing Permission | `s3:GetObject` |
| Expected Error | `AccessDenied` |
| Root Cause | Insufficient execution-role permission |
| Remediation | Scoped IAM inline policy |
| Code Redeployment | Not required |
| Recovery Verification | Successful S3 object retrieval |
| Security Verification | Second object remains inaccessible |
| Cleanup | Lambda, IAM, S3, CloudWatch |

### Lab Objectives

- Understand AWS Lambda execution roles.
- Understand IAM authorization and implicit deny.
- Create a private S3 bucket.
- Configure S3 Block Public Access.
- Upload an encrypted test object.
- Create a dedicated Lambda execution role.
- Understand the AWSLambdaBasicExecutionRole policy.
- Deploy Python Lambda using AWS CLI.
- Use boto3 to access Amazon S3.
- Reproduce an actual S3 AccessDenied error.
- Inspect Python ClientError exceptions.
- Investigate CloudWatch Logs.
- Identify missing IAM actions.
- Understand S3 object ARNs.
- Apply a least-privilege IAM policy.
- Verify successful Lambda execution.
- Test unauthorized resource access.
- Perform root cause analysis.
- Clean up all temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company uses AWS Lambda to process customer orders stored in Amazon S3.

Each order is saved as a JSON object inside a private S3 bucket.

When invoked, the Lambda function reads the order file and returns information such as the order ID, status, and total amount.

The engineering team deploys the Lambda application and confirms that the function is Active.

However, the application fails while attempting to retrieve an order.

The CloudWatch error contains:

```text
botocore.exceptions.ClientError:
An error occurred (AccessDenied) when calling
the GetObject operation: Access Denied
```

The Cloud Engineering team investigates the incident.

The engineer confirms that the S3 bucket exists, the requested object is present, and the Lambda function is using the intended execution role.

The engineer then inspects the role's IAM policies.

The role has the AWS-managed `AWSLambdaBasicExecutionRole` policy, allowing the function to publish CloudWatch logs.

However, the role does not have an applicable Allow for `s3:GetObject`.

Amazon S3 denies the request because the execution role lacks permission to retrieve the object.

The engineer creates a least-privilege IAM policy allowing `s3:GetObject` for the specific order file.

After attaching the policy, the Lambda function successfully reads the file.

The engineer also tests access to another S3 object and confirms that the new permission does not grant unrestricted access to the bucket.

### Incident Symptoms

- Lambda deployment succeeds.
- Function state is Active.
- Python handler starts.
- CloudWatch logging works.
- S3 object exists.
- Bucket is private.
- Lambda attempts GetObject.
- S3 returns AccessDenied.
- boto3 raises ClientError.
- Lambda invocation reports an unhandled execution error.
- Customer order information is not returned.

### Business Impact

AccessDenied incidents can cause:

- Failed customer order processing.
- Interrupted serverless workflows.
- Unavailable application endpoints.
- Failed data-processing pipelines.
- Incomplete automation.
- Delays in business operations.
- Increased application error rates.
- Failed integrations between AWS services.

### Objective

Identify the missing authorization, grant the minimum required permission, restore successful processing, and confirm that unrelated S3 objects remain inaccessible.

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
              lambda-lab05-access-denied
                          |
                          v
                    Python Handler
                          |
                          v
                    boto3 GetObject
                          |
                          v
                    Amazon S3
                          |
                          v
                Evaluate IAM Permissions
                          |
                          v
                 Lambda Execution Role
                          |
                          v
             AWSLambdaBasicExecutionRole
                          |
                          v
                  No s3:GetObject Allow
                          |
                          v
                    ACCESS DENIED
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Python ClientError        CloudWatch Logs
              |                       |
              v                       v
       Failed Execution          Error Traceback
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
              lambda-lab05-access-denied
                          |
                          v
                    Python Handler
                          |
                          v
                    boto3 GetObject
                          |
                          v
                    Amazon S3
                          |
                          v
                 Evaluate IAM Permissions
                          |
                          v
                  Lambda Execution Role
                          |
               +----------+----------+
               |                     |
               v                     v
       CloudWatch Logging       Scoped s3:GetObject
               |                     |
               +----------+----------+
                          |
                          v
                  Access Authorized
                          |
                          v
              Read orders/order-1001.json
                          |
                          v
                   Parse Order JSON
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
| AWS Lambda | Executes the order-processing application |
| Amazon S3 | Stores customer order JSON |
| IAM Execution Role | Provides AWS permissions during execution |
| IAM Trust Policy | Allows the Lambda service to assume the role |
| AWSLambdaBasicExecutionRole | Grants CloudWatch logging permissions |
| IAM Inline Policy | Grants access to the specific S3 object |
| boto3 | Performs S3 API calls |
| CloudWatch Logs | Records application and runtime errors |
| AWS CLI | Deploys and investigates resources |
| Bash | Automates the lab commands |
| SSE-S3 | Encrypts test objects at rest |
| S3 Block Public Access | Helps prevent accidental public exposure |

---

## 4. Understanding Lambda AccessDenied

### What Is AccessDenied?

AccessDenied indicates that an AWS request is not authorized under the applicable permission controls.

For this lab, Amazon S3 rejects a GetObject request because the Lambda execution role lacks an applicable Allow.

### What Is a Lambda Execution Role?

A Lambda execution role is an IAM role that AWS Lambda assumes to access AWS services during function execution.

### Does the Engineer's Permission Transfer to Lambda?

No.

The engineer may have permission to upload and read an S3 object using AWS CLI.

That permission does not automatically transfer to the Lambda function.

Lambda performs AWS operations using its execution-role credentials.

### What Is AWSLambdaBasicExecutionRole?

It is an AWS-managed IAM policy that provides basic CloudWatch Logs permissions for Lambda.

It does not grant general S3 access.

### What Does s3:GetObject Allow?

It allows an authorized principal to retrieve object data from Amazon S3.

### What Is the S3 Object ARN Format?

```text
arn:aws:s3:::BUCKET_NAME/OBJECT_KEY
```

Example:

```text
arn:aws:s3:::example-bucket/orders/order-1001.json
```

### Bucket ARN vs. Object ARN

Bucket ARN:

```text
arn:aws:s3:::example-bucket
```

Object ARN:

```text
arn:aws:s3:::example-bucket/orders/order-1001.json
```

The `s3:GetObject` action requires an applicable object resource ARN.

### What Is Implicit Deny?

AWS access is denied by default unless the request is allowed by the applicable policies and no overriding restriction denies it.

### What Is Explicit Deny?

An explicit Deny statement blocks an operation even when another applicable policy allows it.

### What Is Least Privilege?

Granting only the permissions necessary for an application to perform its intended task.

For this lab, we allow:

```text
s3:GetObject
```

On one specific object.

We do not grant:

```text
s3:*
s3:DeleteObject
s3:PutObject
s3:ListBucket
```

### Does S3 Block Public Access Cause This Incident?

No.

The request uses the Lambda execution role for authenticated private access.

We keep S3 Block Public Access enabled throughout the lab.

### What Is boto3 ClientError?

A boto3/botocore exception raised when an AWS service API request returns an error response.

For this incident, the error code is `AccessDenied`.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Bash.
- Python 3.
- ZIP and unzip.
- IAM role management permissions.
- Lambda management permissions.
- S3 bucket and object permissions.
- CloudWatch Logs permissions.

### Relevant AWS Permissions

```text
sts:GetCallerIdentity

iam:CreateRole
iam:GetRole
iam:ListRoleTags
iam:AttachRolePolicy
iam:ListAttachedRolePolicies
iam:ListRolePolicies
iam:PutRolePolicy
iam:GetRolePolicy
iam:DeleteRolePolicy
iam:DetachRolePolicy
iam:DeleteRole
iam:PassRole

lambda:CreateFunction
lambda:GetFunction
lambda:GetFunctionConfiguration
lambda:InvokeFunction
lambda:ListTags
lambda:DeleteFunction

s3:CreateBucket
s3:HeadBucket
s3:PutBucketTagging
s3:GetBucketTagging
s3:PutBucketPublicAccessBlock
s3:GetBucketPublicAccessBlock
s3:PutObject
s3:GetObject
s3:DeleteObject
s3:DeleteBucket
s3:GetBucketPolicy

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

Optional:

```text
iam:SimulatePrincipalPolicy
```

### Safety Rules

- Create a dedicated lab S3 bucket.
- Keep S3 Block Public Access enabled.
- Use fabricated customer data.
- Do not modify production IAM roles.
- Do not grant AmazonS3FullAccess.
- Scope policies to the required resource.
- Verify project tags before cleanup.
- Do not publish AWS account-specific resource names.
- Delete only lab-created resources.

### Cost Considerations

This lab uses short Lambda invocations, a small S3 object, and CloudWatch Logs.

Potential costs include Lambda requests, S3 requests and storage, and CloudWatch log ingestion or storage.

No EC2 instances, RDS databases, NAT Gateways, or VPC endpoints are required.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create the Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 05-lambda-access-denied

cd 05-lambda-access-denied
```

### Step 2 — Verify Tools

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

export PROJECT_TAG="Lambda-Troubleshooting-Lab05"

export FUNCTION_NAME="lambda-lab05-access-denied"

export ROLE_NAME="lambda-lab05-execution-role"

export POLICY_NAME="lambda-lab05-s3-read-policy"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"

export OBJECT_KEY="orders/order-1001.json"

export BUCKET_NAME="lambda-lab05-${ACCOUNT_ID}-$(date -u +%Y%m%d%H%M%S)"
```

### Step 5 — Verify Variables

```bash
echo "$AWS_REGION"
echo "$FUNCTION_NAME"
echo "$ROLE_NAME"
echo "$POLICY_NAME"
echo "$BUCKET_NAME"
echo "$OBJECT_KEY"
```

### Step 6 — Save Resource Identifiers

```bash
cat > lab05-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export POLICY_NAME="$POLICY_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
export OBJECT_KEY="$OBJECT_KEY"
export BUCKET_NAME="$BUCKET_NAME"
EOF
```

Restore:

```bash
source lab05-resources.env
```

Keep this file local and out of GitHub.

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

Expected for a new lab: the function and role are not found.

If either exists, verify ownership before proceeding.

---

## 7. Create the Private S3 Bucket

### Step 1 — Create Bucket

```bash
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Because the bucket is created in `us-east-1`, a LocationConstraint is not required.

### Step 2 — Verify Bucket Ownership

```bash
aws s3api head-bucket \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --region "$AWS_REGION"
```

### Step 3 — Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --region "$AWS_REGION"
```

### Step 4 — Verify Public Access Settings

```bash
aws s3api get-public-access-block \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

All four settings should be true.

### Step 5 — Tag the Bucket

```bash
aws s3api put-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --tagging "TagSet=[{Key=Project,Value=$PROJECT_TAG}]" \
  --region "$AWS_REGION"
```

### Step 6 — Verify Tags

```bash
aws s3api get-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

### Step 7 — Create the Customer Order File

Save as `order-1001.json`:

```json
{
  "order_id": "ORDER-1001",
  "customer": "Test Customer",
  "status": "pending",
  "total": 125.50,
  "currency": "USD"
}
```

### Step 8 — Validate JSON

```bash
python3 -m json.tool order-1001.json
```

### Step 9 — Upload the Order

```bash
aws s3api put-object \
  --bucket "$BUCKET_NAME" \
  --key "$OBJECT_KEY" \
  --body order-1001.json \
  --server-side-encryption AES256 \
  --region "$AWS_REGION"
```

### Step 10 — Verify the Object

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "$OBJECT_KEY" \
  --region "$AWS_REGION"
```

### Important Observation

The AWS CLI identity can access the S3 object.

However, this does not prove that the Lambda execution role has access.

The Lambda function uses its own execution-role credentials.

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
  --description "Lambda Lab 05 execution role" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach CloudWatch Logging Policy

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 4 — Inspect Attached Policies

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaBasicExecutionRole
```

### Step 5 — Inspect Inline Policies

```bash
aws iam list-role-policies \
  --role-name "$ROLE_NAME"
```

Expected:

```json
{
  "PolicyNames": []
}
```

### Initial IAM Misconfiguration

The execution role can publish CloudWatch logs but lacks an applicable Allow for S3 GetObject.

This is the intentional fault used in the lab.

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

## 10. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import os
import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):
    print("Lambda Lab 05 started", flush=True)

    bucket_name = os.environ["BUCKET_NAME"]

    object_key = event.get(
        "object_key",
        "orders/order-1001.json"
    )

    print(
        f"Reading S3 object: {object_key}",
        flush=True
    )

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key
    )

    content = response["Body"].read().decode("utf-8")

    order = json.loads(content)

    print(
        f"Successfully retrieved order: {order['order_id']}",
        flush=True
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Order retrieved successfully",
            "order_id": order["order_id"],
            "status": order["status"],
            "total": order["total"]
        })
    }
```

### Step 2 — Understand the S3 Request

The application uses boto3:

```python
s3 = boto3.client("s3")
```

Then retrieves an object:

```python
response = s3.get_object(
    Bucket=bucket_name,
    Key=object_key
)
```

This operation requires authorization for `s3:GetObject` on the target object.

If authorization is missing, S3 returns AccessDenied.

### Step 3 — Verify Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 4 — Create Deployment ZIP

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

### Step 6 — Create Environment Configuration

Create `lambda-environment.json` using the actual bucket name:

```bash
python3 - <<'PY'
import json
import os

configuration = {
    "Variables": {
        "BUCKET_NAME": os.environ["BUCKET_NAME"]
    }
}

with open("lambda-environment.json", "w") as file:
    json.dump(configuration, file, indent=2)

print("Environment configuration created")
PY
```

### Step 7 — Create the Test Event

Save as `test-event.json`:

```json
{
  "object_key": "orders/order-1001.json"
}
```

---

## 11. Deploy Lambda Without S3 Access

### Step 1 — Create Lambda

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13 \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --environment file://lambda-environment.json \
  --timeout 15 \
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

If IAM role propagation prevents function creation, verify the role's trust policy and retry after propagation.

### Step 3 — Verify Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,Runtime:Runtime,Role:Role,Environment:Environment.Variables}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Runtime = python3.13
Role = lambda-lab05-execution-role
```

The environment configuration should contain the generated S3 bucket name.

### Step 4 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab05-broken-configuration.json
```

---

<WritingBlock id="52742" variant="document">## 12. Fault Injection — Reproduce AccessDenied

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
  > lab05-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab05-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

A synchronous Invoke API status of 200 does not guarantee successful application execution.

### Step 3 — Inspect the Error Payload

```bash
python3 -m json.tool broken-response.json
```

Expected error information resembles:

```json
{
  "errorMessage": "An error occurred (AccessDenied) when calling the GetObject operation: Access Denied",
  "errorType": "ClientError"
}
```

Additional fields may be present in the actual response.

### Step 4 — Verify AccessDenied

```bash
python3 - <<'PY'
import json

with open("lab05-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    payload = json.load(file)

assert invocation["StatusCode"] == 200
assert invocation.get("FunctionError") == "Unhandled"

error_message = payload.get("errorMessage", "")

assert "AccessDenied" in error_message

print("SUCCESS: S3 AccessDenied reproduced")
PY
```

If a different error appears, investigate it before proceeding.

### Step 5 — Decode Inline Logs

```bash
python3 - <<'PY'
import base64
import json

with open("lab05-broken-invocation.json") as file:
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
| Lambda function | Active |
| Python handler | Executing |
| S3 bucket | Exists |
| S3 order object | Exists |
| S3 Block Public Access | Enabled |
| Lambda logging permission | Present |
| Lambda S3 read permission | Missing |
| S3 GetObject | AccessDenied |
| FunctionError | Unhandled |
| Order processing | Failed |

---

## 13. Investigate CloudWatch Logs

### Step 1 — Read Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected output resembles:

```text
Lambda Lab 05 started

Reading S3 object: orders/order-1001.json

[ERROR] ClientError:
An error occurred (AccessDenied)
when calling the GetObject operation:
Access Denied
```

### Step 2 — Search AccessDenied

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"AccessDenied"' \
  --query 'events[].{Time:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search GetObject

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"GetObject"' \
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
  > lab05-broken-cloudwatch-evidence.json
```

### CloudWatch Findings

The Python handler starts successfully.

The function reaches the S3 GetObject call.

Amazon S3 denies the request.

The exception is recorded in CloudWatch Logs.

This indicates a downstream AWS service authorization failure rather than a Lambda initialization or Python syntax problem.

---

## 14. Investigate IAM and Amazon S3

### Step 1 — Identify the Lambda Execution Role

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query Role \
  --output text \
  --region "$AWS_REGION"
```

Expected:

```text
arn:aws:iam::ACCOUNT_ID:role/lambda-lab05-execution-role
```

### Step 2 — Inspect Attached Managed Policies

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaBasicExecutionRole
```

### Step 3 — Inspect Inline Policies

```bash
aws iam list-role-policies \
  --role-name "$ROLE_NAME"
```

Expected:

```json
{
  "PolicyNames": []
}
```

### Step 4 — Verify the S3 Object Exists

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "$OBJECT_KEY" \
  --region "$AWS_REGION"
```

This verification uses the currently configured AWS CLI credentials, not the Lambda execution role.

### Step 5 — Inspect S3 Public Access Settings

```bash
aws s3api get-public-access-block \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

All public-access blocking settings should be enabled.

These controls do not prevent properly authorized private S3 access.

### Step 6 — Inspect S3 Bucket Policy

```bash
aws s3api get-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected for the newly created bucket:

```text
NoSuchBucketPolicy
```

No custom bucket policy was created for this lab.

### Step 7 — Identify the Required Permission

The Python application calls:

```python
s3.get_object(
    Bucket=bucket_name,
    Key=object_key
)
```

Required IAM action:

```text
s3:GetObject
```

Required resource type:

```text
S3 object ARN
```

### Investigation Findings

| Component | Finding |
|---|---|
| Lambda runtime | Healthy |
| Handler | Correct |
| S3 bucket | Exists |
| Order object | Exists |
| Execution role | Correct role assigned |
| CloudWatch logging | Allowed |
| s3:GetObject | Not allowed |
| Bucket custom policy | None |
| Root cause | Missing execution-role permission |

---

## 15. Root Cause Analysis

### Root Cause

The Lambda execution role did not have an applicable Allow for the `s3:GetObject` operation.

The role initially had:

```text
AWSLambdaBasicExecutionRole
```

This policy allows basic CloudWatch logging but does not provide permission to retrieve S3 objects.

When the application attempted `GetObject`, S3 evaluated the request against the applicable authorization controls.

Because no applicable permission allowed the operation, access was denied.

### Root Cause Flow

```text
Lambda Invocation
       |
       v
Python Handler Starts
       |
       v
boto3 GetObject
       |
       v
Amazon S3
       |
       v
IAM Authorization Evaluation
       |
       v
Lambda Execution Role
       |
       v
No s3:GetObject Allow
       |
       v
Implicit Deny
       |
       v
AccessDenied
       |
       v
Python ClientError
       |
       v
CloudWatch Error
```

### Five Whys

**Why 1 — Why did Lambda fail?**

Amazon S3 rejected the GetObject request.

**Why 2 — Why did Amazon S3 reject it?**

The execution role lacked the required permission.

**Why 3 — Why was the permission missing?**

The role had only CloudWatch logging permissions.

**Why 4 — Why didn't the engineer's S3 access help?**

Lambda executes AWS API requests using its own role credentials.

**Why 5 — How can this be prevented?**

Define required IAM permissions explicitly, scope them to intended resources, and validate authorization during deployment.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-005 |
| Services | AWS Lambda, Amazon S3, IAM |
| Failed API | GetObject |
| Error | AccessDenied |
| Missing Action | s3:GetObject |
| Identity | Lambda execution role |
| Fault Category | IAM authorization |
| Root Cause | Missing applicable Allow |
| Remediation | Least-privilege inline IAM policy |
| Application Code Change | Not required |
| Recovery Verification | Successful object retrieval |

---

## 16. Remediation — Apply Least-Privilege IAM Permissions

### Step 1 — Create the IAM Policy Document

Generate `lambda-s3-read-policy.json` with the actual S3 bucket name:

```bash
python3 - <<'PY'
import json
import os

bucket_name = os.environ["BUCKET_NAME"]
object_key = os.environ["OBJECT_KEY"]

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowReadSpecificOrder",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": (
                f"arn:aws:s3:::{bucket_name}/{object_key}"
            )
        }
    ]
}

with open("lambda-s3-read-policy.json", "w") as file:
    json.dump(policy, file, indent=2)

print("Least-privilege IAM policy created")
PY
```

### Step 2 — Verify Policy

```bash
python3 -m json.tool lambda-s3-read-policy.json
```

Expected structure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadSpecificOrder",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET/orders/order-1001.json"
    }
  ]
}
```

### Step 3 — Understand Least Privilege

The policy grants one action:

```text
s3:GetObject
```

For one object:

```text
orders/order-1001.json
```

It does not allow bucket-wide access.

### Step 4 — Attach Inline IAM Policy

```bash
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file://lambda-s3-read-policy.json
```

### Step 5 — Verify Inline Policy

```bash
aws iam list-role-policies \
  --role-name "$ROLE_NAME"
```

Expected:

```json
{
  "PolicyNames": [
    "lambda-lab05-s3-read-policy"
  ]
}
```

### Step 6 — Inspect the Policy

```bash
aws iam get-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --output json
```

Confirm that it allows only the intended operation and object ARN.

### Step 7 — Optional IAM Simulation

If your current identity has IAM simulation permissions:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn "$ROLE_ARN" \
  --action-names s3:GetObject \
  --resource-arns "arn:aws:s3:::${BUCKET_NAME}/${OBJECT_KEY}" \
  --query 'EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}' \
  --output table
```

Expected identity-policy evaluation:

```text
allowed
```

IAM simulation is a diagnostic tool. The real S3 API request remains the final verification because additional authorization controls may apply.

### Remediation Summary

| Component | Before | After |
|---|---|---|
| IAM execution role | Logging only | Logging + S3 read |
| s3:GetObject | Not allowed | Allowed for one object |
| S3 bucket | Private | Private |
| S3 public access | Blocked | Blocked |
| Lambda source | Unchanged | Unchanged |
| Expected result | AccessDenied | Successful retrieval |

---

## 17. Verify Successful Recovery

### Step 1 — Invoke the Same Lambda Function

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab05-healthy-invocation.json
```

Allow IAM policy changes time to propagate if the first attempt still fails.

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab05-healthy-invocation.json
```

Expected relevant field:

```json
{
  "StatusCode": 200
}
```

There should be no `FunctionError`.

### Step 3 — Inspect Successful Response

```bash
python3 -m json.tool healthy-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Order retrieved successfully\", \"order_id\": \"ORDER-1001\", \"status\": \"pending\", \"total\": 125.5}"
}
```

### Step 4 — Verify with Python

```bash
python3 - <<'PY'
import json

with open("lab05-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 200
assert body["order_id"] == "ORDER-1001"
assert body["status"] == "pending"
assert body["total"] == 125.5

print("SUCCESS: Lambda AccessDenied resolved")
PY
```

Expected:

```text
SUCCESS: Lambda AccessDenied resolved
```

### Step 5 — Verify CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Lambda Lab 05 started
Reading S3 object: orders/order-1001.json
Successfully retrieved order: ORDER-1001
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Successfully retrieved order:"' \
  --output json \
  --region "$AWS_REGION" \
  > lab05-recovery-cloudwatch-evidence.json
```

### Before and After Verification

| Check | Broken | Recovered |
|---|---|---|
| Lambda state | Active | Active |
| Order object exists | Yes | Yes |
| S3 bucket | Private | Private |
| IAM logging access | Allowed | Allowed |
| s3:GetObject | Missing | Scoped Allow |
| S3 API result | AccessDenied | Successful |
| FunctionError | Unhandled | Absent |
| Order processing | Failed | Successful |
| Python code | Unchanged | Unchanged |
| CloudWatch evidence | ClientError | Successful retrieval |

**Recovery is confirmed when the same Lambda function retrieves the original order successfully without a FunctionError.**

---

## 18. Additional Security Test — Restricted S3 Object

### Purpose

Verify that the Lambda execution role cannot access an object outside the intended resource scope.

### Step 1 — Create the Restricted Object

Save as `restricted-order.json`:

```json
{
  "order_id": "ORDER-PRIVATE",
  "classification": "restricted"
}
```

### Step 2 — Upload the Object

```bash
aws s3api put-object \
  --bucket "$BUCKET_NAME" \
  --key "orders/restricted-order.json" \
  --body restricted-order.json \
  --server-side-encryption AES256 \
  --region "$AWS_REGION"
```

### Step 3 — Create Test Event

Save as `restricted-event.json`:

```json
{
  "object_key": "orders/restricted-order.json"
}
```

### Step 4 — Invoke Lambda

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://restricted-event.json \
  --region "$AWS_REGION" \
  restricted-response.json \
  > lab05-restricted-invocation.json
```

### Step 5 — Inspect Response

```bash
python3 -m json.tool restricted-response.json
```

Expected: AccessDenied.

### Step 6 — Verify Permission Restriction

```bash
python3 - <<'PY'
import json

with open("lab05-restricted-invocation.json") as file:
    invocation = json.load(file)

with open("restricted-response.json") as file:
    payload = json.load(file)

assert invocation.get("FunctionError") is not None
assert "AccessDenied" in payload.get("errorMessage", "")

print("SUCCESS: Least-privilege restriction verified")
PY
```

Expected:

```text
SUCCESS: Least-privilege restriction verified
```

### Security Verification

| S3 Object | Permission | Expected Result |
|---|---|---|
| orders/order-1001.json | Allowed | Successful |
| orders/restricted-order.json | Not allowed | AccessDenied |

### Security Lesson

The execution role can retrieve the required object without gaining unnecessary access to other objects in the same bucket.

This demonstrates the principle of least privilege.

---

<WritingBlock id="52743" variant="document">## 19. Production Troubleshooting Best Practices

### Standard Investigation Checklist

1. Verify the AWS account and Region.
2. Identify the failing Lambda function.
3. Confirm Lambda is Active.
4. Inspect CloudWatch Logs.
5. Identify the denied AWS API operation.
6. Inspect the Lambda execution role.
7. Review attached managed policies.
8. Review inline IAM policies.
9. Confirm the requested S3 resource exists.
10. Inspect the S3 object ARN.
11. Review the bucket policy.
12. Check for explicit Deny statements.
13. Investigate permission boundaries when applicable.
14. Investigate AWS Organizations restrictions when applicable.
15. Identify missing or incorrect permissions.
16. Create a least-privilege IAM policy.
17. Apply the policy to the execution role.
18. Repeat the original invocation.
19. Verify successful access.
20. Confirm unrelated resources remain protected.
21. Preserve evidence.
22. Clean up temporary resources.

### Investigation Flow

```text
Lambda AccessDenied
         |
         v
Read CloudWatch Error
         |
         v
Identify AWS API Operation
         |
         v
Check Lambda Execution Role
         |
         v
Inspect IAM Policies
         |
         v
Verify S3 Resource ARN
         |
         v
Inspect Bucket Policy
         |
         v
Check Other Authorization Controls
         |
         v
Determine Root Cause
         |
         v
Apply Least-Privilege Fix
         |
         v
Repeat Invocation
         |
         v
Verify Successful Access
```

### Common Causes of S3 AccessDenied

| Cause | Investigation |
|---|---|
| Missing s3:GetObject | Check execution-role policy |
| Wrong resource ARN | Compare bucket and object ARNs |
| Wrong execution role | Inspect Lambda configuration |
| Explicit Deny | Inspect identity and resource policies |
| Permissions boundary | Check IAM role boundary |
| Organization restriction | Inspect applicable SCP/RCP controls |
| SSE-KMS encryption | Review KMS permissions and key policy |
| Cross-account S3 access | Inspect identity and bucket policies |
| Missing object | Verify key and object existence |
| VPC endpoint policy | Inspect S3 endpoint policy when used |

### Production Recommendations

- Define IAM permissions through Terraform or CloudFormation.
- Use separate roles for separate applications.
- Grant only necessary AWS API actions.
- Scope permissions to required resources.
- Avoid broad wildcard permissions.
- Monitor Lambda Errors.
- Use CloudWatch Logs for application diagnostics.
- Review CloudTrail activity when investigating unexpected access changes.
- Test both allowed and denied operations.
- Keep S3 buckets private.
- Use encryption at rest.
- Review access policies during code review.
- Avoid logging sensitive customer data.

---

## 20. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 05.

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
Project = Lambda-Troubleshooting-Lab05
```

### Step 2 — Verify S3 Bucket Ownership

```bash
aws s3api head-bucket \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Bucket Tags

```bash
aws s3api get-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Confirm the same project tag.

### Step 4 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 5 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 6 — Delete Inline IAM Policy

```bash
aws iam delete-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME"
```

### Step 7 — Detach CloudWatch Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 8 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 9 — Delete Original Order Object

```bash
aws s3api delete-object \
  --bucket "$BUCKET_NAME" \
  --key "$OBJECT_KEY" \
  --region "$AWS_REGION"
```

### Step 10 — Delete Restricted Order Object

```bash
aws s3api delete-object \
  --bucket "$BUCKET_NAME" \
  --key "orders/restricted-order.json" \
  --region "$AWS_REGION"
```

### Step 11 — Delete S3 Bucket

```bash
aws s3api delete-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

If the bucket is not empty, inspect its remaining objects and versions before attempting further deletion.

### Step 12 — Verify Log Group Name

```bash
echo "$LOG_GROUP"
```

Expected:

```text
/aws/lambda/lambda-lab05-access-denied
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

### Step 15 — Verify Role Deletion

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected:

```text
NoSuchEntity
```

### Step 16 — Verify S3 Bucket Deletion

```bash
aws s3api head-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION"
```

Expected: the bucket is no longer found.

### Step 17 — Verify Log Group Removal

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
| IAM inline policy | Deleted |
| CloudWatch managed policy attachment | Removed |
| S3 original order | Deleted |
| S3 restricted order | Deleted |
| Private S3 bucket | Deleted |
| CloudWatch log group | Deleted |
| EC2 | Not created |
| RDS | Not created |
| NAT Gateway | Not created |
| VPC | Not created |

---

## 21. Interview Questions and Answers

### Q1. What causes AWS Lambda AccessDenied?

An AWS operation is denied because the Lambda execution role or other applicable authorization controls do not permit it.

### Q2. What is a Lambda execution role?

An IAM role assumed by Lambda to access AWS services while running application code.

### Q3. Why did Lambda fail to read S3 in this lab?

The execution role lacked permission for s3:GetObject.

### Q4. Does AWSLambdaBasicExecutionRole grant S3 access?

No. It provides basic CloudWatch logging permissions.

### Q5. What is the difference between s3:GetObject and s3:ListBucket?

GetObject retrieves object contents. ListBucket allows listing objects within a bucket.

### Q6. What is the ARN format for an S3 object?

```text
arn:aws:s3:::BUCKET_NAME/OBJECT_KEY
```

### Q7. Why not attach AmazonS3FullAccess?

It grants unnecessary permissions and violates least-privilege principles.

### Q8. Can a Lambda function start successfully and still receive AccessDenied?

Yes. The function can run, but a downstream AWS API request may be denied.

### Q9. Does an engineer's AWS CLI access automatically give Lambda the same permissions?

No. Lambda uses its execution-role credentials.

### Q10. What is implicit deny?

Access is denied when no applicable policy allows the requested operation.

### Q11. What is explicit deny?

A policy statement that blocks an operation even if another applicable policy allows it.

### Q12. How can you inspect a Lambda execution role?

```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --query Role \
  --region us-east-1
```

### Q13. How do you inspect attached IAM policies?

```bash
aws iam list-attached-role-policies \
  --role-name ROLE_NAME
```

### Q14. How do you inspect inline role policies?

```bash
aws iam list-role-policies \
  --role-name ROLE_NAME
```

### Q15. What if the object uses SSE-KMS?

Investigate the required KMS permissions, key policy, and encryption configuration.

### Q16. Can an S3 bucket policy deny access despite an IAM Allow?

Yes. An applicable explicit Deny can override the Allow.

### Q17. How do you grant access to only one S3 object?

Use s3:GetObject with that object's exact ARN in the IAM policy.

### Q18. How do you verify least privilege?

Test authorized access to the intended resource and denied access to unrelated resources.

### Q19. Do you need to redeploy Lambda code after fixing IAM?

Not when the application code is already correct. IAM permissions can be updated separately.

### Q20. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function that used boto3 to retrieve an order file from a private Amazon S3 bucket.

I intentionally configured its execution role with CloudWatch logging permissions but without S3 read access.

When I invoked the function, Amazon S3 returned AccessDenied.

I investigated the Lambda invocation response, CloudWatch logs, IAM execution role, and S3 object configuration.

I identified the missing s3:GetObject permission as the root cause.

I created a least-privilege IAM policy allowing access only to the required S3 object and attached it to the execution role.

I invoked Lambda again and verified that the application retrieved the order successfully.

I also created a second S3 object and confirmed that the execution role could not read it.

Finally, I deleted all temporary Lambda, IAM, S3, and CloudWatch resources.

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
│
├── 05-lambda-access-denied/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── lambda-s3-read-policy.json
│   ├── lambda-environment.json
│   ├── order-1001.json
│   ├── restricted-order.json
│   ├── test-event.json
│   ├── restricted-event.json
│   ├── function.zip
│   ├── lab05-resources.env
│   ├── lab05-broken-configuration.json
│   ├── lab05-broken-invocation.json
│   ├── lab05-healthy-invocation.json
│   ├── lab05-restricted-invocation.json
│   ├── lab05-broken-cloudwatch-evidence.json
│   ├── lab05-recovery-cloudwatch-evidence.json
│   ├── broken-response.json
│   ├── healthy-response.json
│   └── restricted-response.json
│
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
| README.md | Detailed incident documentation |
| lambda_function.py | Python Lambda application |
| lambda-trust-policy.json | IAM trust policy |
| lambda-s3-read-policy.json | Scoped S3 GetObject policy |
| lambda-environment.json | Lambda bucket configuration |
| order-1001.json | Original test order |
| restricted-order.json | Restricted-object test data |
| test-event.json | Normal Lambda invocation |
| restricted-event.json | Unauthorized-access test |
| function.zip | Generated Lambda deployment package |
| lab05-resources.env | Local AWS resource identifiers |
| lab05-broken-configuration.json | Initial Lambda configuration |
| lab05-broken-invocation.json | Failed invocation metadata |
| lab05-healthy-invocation.json | Successful invocation metadata |
| lab05-restricted-invocation.json | Restricted-access test metadata |
| lab05-broken-cloudwatch-evidence.json | Original error logs |
| lab05-recovery-cloudwatch-evidence.json | Successful execution logs |
| broken-response.json | AccessDenied payload |
| healthy-response.json | Successful order response |
| restricted-response.json | Restricted-access error |

### Recommended Public GitHub Files

```text
README.md
lambda_function.py
lambda-trust-policy.json
order-1001.json
restricted-order.json
test-event.json
restricted-event.json
```

The generated IAM policy and environment configuration contain a real bucket name, so review or sanitize them before publishing.

An example least-privilege policy with a placeholder resource ARN is appropriate for GitHub.

### Recommended .gitignore

Add the following to the root `.gitignore`:

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Lambda deployment packages
*.zip

# Local AWS resource variables
**/lab05-resources.env

# Lambda configuration dumps
**/lab05-*-configuration.json

# Invocation metadata
**/lab05-*-invocation.json

# CloudWatch evidence
**/lab05-*-evidence.json

# Generated account-specific configuration
05-lambda-access-denied/lambda-s3-read-policy.json
05-lambda-access-denied/lambda-environment.json

# Lambda response files
05-lambda-access-denied/broken-response.json
05-lambda-access-denied/healthy-response.json
05-lambda-access-denied/restricted-response.json

# Credentials
.env
.env.*
*.pem
*.key
```

These rules prevent the lab's generated configuration and evidence files from being added accidentally.

---

## 23. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how an AWS Lambda function can deploy successfully but fail when accessing another AWS service because of insufficient IAM permissions.

We created a private S3 bucket and uploaded a sample customer order.

We deployed a Python Lambda function that used boto3 to retrieve the order.

The function initially had CloudWatch logging permissions but lacked s3:GetObject.

When invoked, the function received AccessDenied from Amazon S3.

We investigated the invocation response, CloudWatch logs, execution role, IAM policies, and S3 resource configuration.

The root cause was a missing S3 read permission in the Lambda execution role.

We created a least-privilege IAM policy granting GetObject permission for the required object only.

After applying the policy, the function successfully retrieved the order.

We also tested access to another object and confirmed that the execution role remained restricted.

Finally, we removed all temporary resources.

**Key Lesson:** Lambda execution-role permissions must explicitly allow the application's required AWS operations. Successful Lambda deployment and logging do not imply permission to access downstream services.

### Skills Demonstrated

- AWS Lambda
- Amazon S3
- AWS IAM
- Python 3.13
- boto3
- AWS CLI v2
- Linux Bash
- IAM execution roles
- IAM trust policies
- IAM inline policies
- IAM least privilege
- s3:GetObject authorization
- S3 object ARNs
- S3 Block Public Access
- SSE-S3 encryption
- Amazon CloudWatch Logs
- ClientError troubleshooting
- AccessDenied investigation
- IAM policy simulation
- Root cause analysis
- Security verification
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-005 |
| Scenario | Lambda AccessDenied |
| Function | lambda-lab05-access-denied |
| AWS Region | us-east-1 |
| Runtime | Python 3.13 |
| Denied Operation | S3 GetObject |
| Root Cause | Missing s3:GetObject |
| Remediation | Scoped IAM inline policy |
| Authorized Object | orders/order-1001.json |
| Restricted Object | orders/restricted-order.json |
| Recovery | Successful S3 retrieval |
| Least-Privilege Test | AccessDenied for restricted object |
| Code Redeployment | Not required |
| Cleanup | Lambda, IAM, S3, and logs deleted |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** Production Cloud Engineers and Cloud Security Engineers must understand the relationship between Lambda execution roles, IAM permissions, resource policies, and downstream AWS API authorization.

---

## Official AWS Documentation

- [AWS Lambda Execution Roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [Troubleshooting Amazon S3 403 AccessDenied](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html)
- [S3 Actions, Resources, and Condition Keys](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html)
- [S3 Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [AWS IAM Policy Evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [AWS CLI — PutRolePolicy](https://docs.aws.amazon.com/cli/latest/reference/iam/put-role-policy.html)
- [AWS CLI — Lambda Invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)
- [AWS Lambda CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)