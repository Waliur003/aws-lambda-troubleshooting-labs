# Lab 10 — AWS Lambda Dependency Import Error

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda `Runtime.ImportModuleError` caused by a missing Python dependency in a deployment ZIP package.

In production, Lambda applications often depend on third-party Python libraries for HTTP communication, database connections, security automation, file processing, and AWS integrations.

A Python application may work correctly on a developer's laptop but fail after deployment because the required dependencies were not included in the deployment artifact.

In this lab, we create a Python Lambda function that imports the third-party `requests` library.

We intentionally deploy the function using a ZIP file containing only `lambda_function.py`, without the required dependency.

When Lambda initializes the runtime, Python cannot import `requests`.

The function fails before the handler executes.

We investigate the error using AWS CLI, CloudWatch Logs, Lambda runtime configuration, and ZIP archive inspection.

After identifying the root cause, we install the missing Python dependencies, rebuild the ZIP package with the correct directory structure, and update the Lambda function.

We then invoke the same test event and verify that the dependency loads successfully and the application completes.

Finally, we clean up the Lambda function, IAM execution role, CloudWatch log group, and generated local build artifacts.

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
Import Third-Party Library
             |
             v
Create Broken Deployment ZIP
             |
             v
Exclude requests Dependency
             |
             v
Deploy Lambda Function
             |
             v
Invoke Lambda
             |
             v
Python Runtime Initialization
             |
             v
ModuleNotFoundError
             |
             v
Runtime.ImportModuleError
             |
             v
Investigate CloudWatch Logs
             |
             v
Inspect Deployment Package
             |
             v
Identify Missing Dependency
             |
             v
Install Python Dependencies
             |
             v
Rebuild Correct ZIP
             |
             v
Update Lambda Function Code
             |
             v
Invoke Same Test Event
             |
             v
Successful Dependency Import
             |
             v
Verify Recovery
             |
             v
Cleanup AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-010 |
| Lab Name | Lambda Dependency Import Error |
| Difficulty | Beginner to Intermediate |
| Primary Service | AWS Lambda |
| Supporting Services | IAM, Amazon CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Tools | AWS CLI v2, Bash, Python, pip, ZIP |
| Lambda Runtime | Python 3.13 |
| Architecture | x86_64 |
| Function Name | `lambda-lab10-import-error` |
| Execution Role | `lambda-lab10-execution-role` |
| Handler | `lambda_function.lambda_handler` |
| Memory | 128 MB |
| Timeout | 10 seconds |
| Required Dependency | `requests` |
| Selected Dependency Version | `2.32.3` |
| Dependency File | `requirements.txt` |
| Broken Deployment | `broken-function.zip` |
| Recovered Deployment | `function.zip` |
| Error Type | `Runtime.ImportModuleError` |
| Root Cause | Missing dependency in deployment ZIP |
| Remediation | Rebuild ZIP with Python dependencies |
| Recovery Test | Successful import and HTTP request preparation |
| VPC | Not required |
| NAT Gateway | Not required |
| Database | Not required |
| Cleanup | Lambda, IAM, CloudWatch |

### Learning Objectives

- Understand Lambda Python deployment packages.
- Understand third-party Python dependencies.
- Understand Python module imports.
- Reproduce `Runtime.ImportModuleError`.
- Distinguish application initialization from handler execution.
- Investigate CloudWatch runtime errors.
- Inspect ZIP deployment contents.
- Understand Python module search paths.
- Install dependencies using pip.
- Create a `requirements.txt` file.
- Package dependencies correctly.
- Understand ZIP root directory structure.
- Update Lambda function code.
- Verify successful runtime initialization.
- Understand Lambda layers.
- Learn CI/CD dependency validation.
- Practice production root cause analysis.
- Clean up temporary AWS resources.

---

## 2. Production Incident Scenario

### Incident Description

A company operates a serverless Python application using AWS Lambda.

The application uses the third-party `requests` library to prepare HTTP requests for an external API integration.

During development, the application works correctly because the developer has installed the required Python packages locally.

The developer then creates a Lambda deployment ZIP containing only the Python application file.

The package is uploaded to AWS Lambda.

The function becomes Active, and deployment appears successful.

However, when the application is invoked, the Python runtime fails to load the required library.

CloudWatch Logs show:

```text
[ERROR] Runtime.ImportModuleError:
Unable to import module 'lambda_function':
No module named 'requests'
```

The Lambda handler never executes.

The Cloud Engineering team investigates the incident.

The engineer confirms that the handler configuration is correct and the function uses the expected Python runtime.

The engineer then inspects the ZIP archive.

The ZIP contains:

```text
lambda_function.py
```

But it does not contain the `requests` package or its dependencies.

The engineer identifies an incomplete deployment artifact as the root cause.

The dependencies are installed into a clean build directory and packaged at the ZIP archive root.

The Lambda function is updated with the corrected deployment package.

After remediation, the function imports `requests`, prepares an HTTP request, and returns a successful application response.

### Incident Symptoms

- Lambda deployment succeeds.
- Lambda function state is Active.
- Invocation fails during initialization.
- Python cannot import `requests`.
- `Runtime.ImportModuleError` appears.
- Lambda Invoke API reports `FunctionError`.
- Handler logging statements do not execute.
- Broken ZIP does not contain the dependency.
- Rebuilding the deployment package restores execution.

### Business Impact

Dependency import failures can cause:

- Application API failures.
- Failed scheduled automation.
- Interrupted data-processing jobs.
- Broken serverless integrations.
- Delayed customer transactions.
- Failed security automation.
- Increased incident response work.
- Unavailable application functionality.

### Objective

Identify the missing Python dependency, rebuild the deployment package correctly, and restore Lambda execution without modifying IAM or network configuration.

---

## 3. AWS Architecture

### Broken Architecture

```text
               Developer / CI System
                        |
                        v
                Python Application
                        |
                        v
                 import requests
                        |
                        v
             Create Deployment Package
                        |
                        v
              broken-function.zip
                        |
                        |
              +---------+---------+
              |                   |
              v                   v
       lambda_function.py     requests/
           Present            MISSING
              |                   |
              +---------+---------+
                        |
                        v
                 Deploy Lambda
                        |
                        v
              Python Runtime Starts
                        |
                        v
              Load lambda_function.py
                        |
                        v
                 import requests
                        |
                        v
                  Module Missing
                        |
                        v
                 ModuleNotFoundError
                        |
                        v
               Runtime.ImportModuleError
                        |
                        v
                  CloudWatch Logs
```

### Recovered Architecture

```text
               Developer / CI System
                        |
                        v
                  requirements.txt
                        |
                        v
               pip Install Dependencies
                        |
                        v
                   package/
                        |
                        v
                 Rebuild ZIP
                        |
                        v
                   function.zip
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
   lambda_function.py requests/    urllib3/
          |             |             |
          +-------------+-------------+
                        |
                        v
                Update Lambda Code
                        |
                        v
              Python Runtime Initializes
                        |
                        v
                 import requests
                        |
                        v
                Import Successful
                        |
                        v
                Handler Executes
                        |
                        v
                Prepare HTTP Request
                        |
                        v
                   statusCode: 200
```

### Architecture Components

| Component | Purpose |
|---|---|
| AWS Lambda | Executes Python application |
| Python Runtime | Loads modules and executes handler |
| IAM Execution Role | Grants CloudWatch logging permission |
| CloudWatch Logs | Records initialization errors and execution logs |
| requests | Third-party HTTP library |
| urllib3 | HTTP transport dependency |
| certifi | Certificate authority bundle dependency |
| idna | Internationalized domain support |
| charset-normalizer | Character encoding detection dependency |
| pip | Installs Python packages |
| requirements.txt | Defines required dependency versions |
| ZIP Deployment Package | Contains code and dependencies |
| AWS CLI | Deploys and investigates Lambda |

---

## 4. Understanding Runtime.ImportModuleError

### What Is Runtime.ImportModuleError?

It is an error reported when AWS Lambda cannot import the application's Python module during runtime initialization.

### What Is ModuleNotFoundError?

`ModuleNotFoundError` is a Python exception raised when a requested module cannot be found in the available import paths.

### Why Can Code Work Locally but Fail in Lambda?

The developer's local Python environment may contain libraries that were not included in the Lambda deployment package.

### Does Lambda Automatically Install Dependencies?

No.

AWS Lambda does not automatically run pip to install packages from `requirements.txt` when a ZIP package is deployed.

Dependencies must be included in the deployment package, provided through a compatible layer, or otherwise available in the runtime.

### What Is a Lambda Deployment ZIP?

A ZIP archive containing the function code and any dependencies needed for execution.

### What Is the Correct ZIP Structure?

For this lab:

```text
function.zip
├── lambda_function.py
├── requests/
├── urllib3/
├── certifi/
├── idna/
├── charset_normalizer/
└── ... metadata and dependencies
```

The module directories must be available on the Python import path.

### Why Can a Nested package/ Folder Cause Problems?

If the archive contains:

```text
function.zip
└── package/
    └── requests/
```

the runtime may not find `requests` because the nested directory is not automatically treated as an application import root.

### What Is requirements.txt?

A file used by pip to identify Python dependencies and requested versions.

For this lab:

```text
requests==2.32.3
```

### Does Runtime.ImportModuleError Always Mean a Missing Package?

No.

Possible causes include:

- Missing dependency.
- Incorrect ZIP structure.
- Incorrect handler module.
- Incompatible Python version.
- Incompatible native binary.
- Missing shared libraries.
- Incorrect Lambda layer structure.
- Circular imports or dependency conflicts.

### What Is a Lambda Layer?

A Lambda layer is a separate archive that can provide shared dependencies or other runtime content to compatible Lambda functions.

### What Is the Difference Between HandlerNotFound and ImportModuleError?

`Runtime.HandlerNotFound` means the configured handler function cannot be found.

`Runtime.ImportModuleError` indicates a problem importing the handler module or one of its dependencies.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- pip.
- ZIP and unzip.
- IAM role management permissions.
- Lambda management permissions.
- CloudWatch Logs access.

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
lambda:ListTags
lambda:DeleteFunction

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

### Safety Rules

- Create a dedicated Lambda function.
- Do not modify production Lambda functions.
- Use only approved Python dependencies.
- Pin dependency versions.
- Do not place credentials in deployment packages.
- Verify ZIP contents before deployment.
- Avoid granting unnecessary IAM permissions.
- Verify project tags before deleting resources.
- Do not publish account-specific invocation evidence.

### Cost Considerations

This lab uses small Lambda invocations and CloudWatch Logs.

No EC2, RDS, NAT Gateway, or custom VPC resources are required.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 10-lambda-dependency-import-error

cd 10-lambda-dependency-import-error
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
python3 -m pip --version
zip -v
unzip -v
```

Verify AWS credentials:

```bash
aws sts get-caller-identity
```

### Step 3 — Configure Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab10"

export FUNCTION_NAME="lambda-lab10-import-error"

export ROLE_NAME="lambda-lab10-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"
```

### Step 4 — Save Resource Variables

```bash
cat > lab10-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
EOF
```

Restore later:

```bash
source lab10-resources.env
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

For a new lab, both should return not-found errors.

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

### Step 2 — Create IAM Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Lambda Lab 10 dependency import troubleshooting" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach Logging Policy

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
  --query "logGroups[?logGroupName=='${LOG_GROUP}'].{Name:logGroupName,Retention:retentionInDays}" \
  --output table \
  --region "$AWS_REGION"
```

---

## 9. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import logging

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 10 started")

    target_url = "https://example.com/api/orders"

    logger.info("Preparing external API request")

    request = requests.Request(
        method="GET",
        url=target_url,
        params={
            "order_id": "ORDER-1001"
        }
    )

    prepared = request.prepare()

    logger.info("Python requests dependency loaded")
    logger.info("HTTP request prepared successfully")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Dependency imported successfully",
            "dependency": "requests",
            "requests_version": requests.__version__,
            "http_method": prepared.method,
            "url": prepared.url
        })
    }
```

### Step 2 — Understand the Import

```python
import requests
```

This library must be available to the Lambda Python runtime.

The application prepares an HTTP request using:

```python
request = requests.Request(
    method="GET",
    url=target_url,
    params={"order_id": "ORDER-1001"}
)

prepared = request.prepare()
```

No actual HTTP request is sent.

This isolates the dependency import test from internet connectivity problems.

### Step 3 — Validate Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 4 — Create Test Event

Save as `test-event.json`:

```json
{
  "action": "verify-python-dependency",
  "order_id": "ORDER-1001"
}
```

---

## 10. Create the Broken Deployment ZIP

### Step 1 — Package Only the Handler

```bash
zip broken-function.zip lambda_function.py
```

### Step 2 — Inspect ZIP Contents

```bash
unzip -l broken-function.zip
```

Expected:

```text
lambda_function.py
```

Missing:

```text
requests/
urllib3/
certifi/
idna/
charset_normalizer/
```

### Step 3 — Verify Missing Dependency

```bash
python3 - <<'PY'
import zipfile

with zipfile.ZipFile("broken-function.zip") as archive:
    files = archive.namelist()

assert "lambda_function.py" in files

assert not any(
    name.startswith("requests/")
    for name in files
)

print("SUCCESS: Broken deployment ZIP verified")
print("Reason: requests dependency is missing")
PY
```

### Broken Package

```text
broken-function.zip
└── lambda_function.py
```

The application imports a library that is not provided in the deployment package.

---

## 11. Deploy the Broken Lambda Function

### Step 1 — Create Lambda

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13 \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://broken-function.zip \
  --memory-size 128 \
  --timeout 10 \
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
  --query '{Name:FunctionName,Runtime:Runtime,State:State,Handler:Handler,Memory:MemorySize,LastUpdateStatus:LastUpdateStatus}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
Runtime = python3.13
Handler = lambda_function.lambda_handler
```

### Step 4 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab10-broken-configuration.json
```

**Important:** An Active function does not guarantee that its dependencies can be imported during invocation.

---

## 12. Fault Injection — Reproduce Runtime.ImportModuleError

### Step 1 — Invoke Lambda

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab10-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab10-broken-invocation.json
```

Expected relevant fields:

```json
{
  "StatusCode": 200,
  "FunctionError": "Unhandled"
}
```

### Step 3 — Inspect Error Payload

```bash
python3 -m json.tool broken-response.json
```

Expected:

```json
{
  "errorMessage": "Unable to import module 'lambda_function': No module named 'requests'",
  "errorType": "Runtime.ImportModuleError"
}
```

Additional fields may appear.

### Step 4 — Verify the Error

```bash
python3 - <<'PY'
import json

with open("lab10-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    payload = json.load(file)

assert invocation["StatusCode"] == 200
assert invocation.get("FunctionError") == "Unhandled"

assert payload.get("errorType") == "Runtime.ImportModuleError"

assert "No module named 'requests'" in payload.get(
    "errorMessage", ""
)

print("SUCCESS: Runtime.ImportModuleError reproduced")
PY
```

### Step 5 — Decode Inline Logs

```bash
python3 - <<'PY'
import base64
import json

with open("lab10-broken-invocation.json") as file:
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
    print("No inline logs returned")
PY
```

### Broken-State Verification

| Check | Expected |
|---|---|
| Lambda deployment | Successful |
| Lambda state | Active |
| Handler file | Present |
| requests dependency | Missing |
| Runtime initialization | Failed |
| Handler executed | No |
| FunctionError | Unhandled |
| Runtime.ImportModuleError | Present |

---

## 13. Investigate CloudWatch Logs

### Step 1 — Read Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected:

```text
[ERROR] Runtime.ImportModuleError:
Unable to import module 'lambda_function':
No module named 'requests'
```

### Step 2 — Search Import Errors

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Runtime.ImportModuleError"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search Missing Module Messages

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"No module named"' \
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
  > lab10-broken-cloudwatch-evidence.json
```

### Important Observation

The handler's first log statement:

```text
Lambda Lab 10 started
```

does not appear for the failed invocation because Python fails while importing the module, before calling the handler.

This confirms that the failure occurs during runtime initialization.

---

## 14. Investigate the Deployment Package

### Step 1 — Inspect Lambda Handler Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Handler:Handler,Runtime:Runtime,Architectures:Architectures}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Handler = lambda_function.lambda_handler
Runtime = python3.13
Architecture = x86_64
```

### Step 2 — Inspect the Broken ZIP

```bash
unzip -l broken-function.zip
```

### Step 3 — Search for requests

```bash
unzip -Z1 broken-function.zip | grep '^requests/'
```

Expected: no matching files.

### Step 4 — Inspect the Source Import

```bash
grep -n 'import requests' lambda_function.py
```

Expected:

```text
import requests
```

### Investigation Findings

| Component | Finding |
|---|---|
| Lambda state | Active |
| Python runtime | Correct |
| Handler name | Correct |
| Handler file | Present |
| requests import | Required |
| requests package | Missing |
| IAM permissions | Sufficient for logging |
| VPC networking | Not involved |
| Root cause | Incomplete ZIP |

---

## 15. Root Cause Analysis

### Root Cause

The Lambda deployment ZIP contained the Python handler but omitted the required third-party `requests` library.

During initialization, Python attempted to import the dependency.

The runtime could not locate it in the available Python module paths.

Consequently, the import failed and Lambda reported `Runtime.ImportModuleError`.

### Root Cause Diagram

```text
Lambda Invocation
        |
        v
Python Runtime Initializes
        |
        v
Load lambda_function.py
        |
        v
Execute import requests
        |
        v
Search Python Module Paths
        |
        v
requests Not Found
        |
        v
ModuleNotFoundError
        |
        v
Runtime.ImportModuleError
        |
        v
Handler Never Executes
```

### Five Whys

**Why 1 — Why did Lambda fail?**

Python could not import the required library.

**Why 2 — Why was the import unsuccessful?**

The `requests` package was not available to the runtime.

**Why 3 — Why was the package unavailable?**

The deployment ZIP contained only the application source.

**Why 4 — Why was the dependency omitted?**

The packaging process did not install and include dependencies.

**Why 5 — How can this be prevented?**

Use reproducible builds, requirements files, artifact validation, and deployment tests.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-010 |
| Failure | Runtime.ImportModuleError |
| Missing Dependency | requests |
| Handler | Correct |
| Runtime | Python 3.13 |
| IAM Role | Correct |
| Root Cause | Missing deployment dependency |
| Remediation | Rebuild ZIP with dependencies |
| Python Source Changes | Not required |
| AWS Networking Changes | Not required |

---

## 16. Remediation — Rebuild the Deployment Package

### Step 1 — Create `requirements.txt`

```bash
cat > requirements.txt <<'EOF'
requests==2.32.3
EOF
```

The version is selected for this lab's reproducible example. For production, use a currently maintained, security-reviewed version and verify transitive dependency compatibility.

### Step 2 — Create Clean Build Directory

```bash
rm -rf package

mkdir -p package
```

Run this only inside the dedicated Lab 10 directory.

### Step 3 — Install Python Dependencies

```bash
python3 -m pip install \
  --target ./package \
  -r requirements.txt
```

### Step 4 — Inspect Installed Dependencies

```bash
ls package
```

Expected folders include:

```text
requests/
urllib3/
certifi/
idna/
charset_normalizer/
```

### Step 5 — Verify Dependency Import Locally

```bash
python3 - <<'PY'
import sys

sys.path.insert(0, "package")

import requests

print("requests version:", requests.__version__)
print("SUCCESS: Dependency installed")
PY
```

### Step 6 — Remove Old Recovered Package

```bash
rm -f function.zip
```

### Step 7 — Package Dependencies at ZIP Root

```bash
cd package

zip -qr ../function.zip .

cd ..
```

### Step 8 — Add Handler

```bash
zip -q function.zip lambda_function.py
```

### Step 9 — Inspect Recovered Package

```bash
unzip -l function.zip | head -35
```

### Step 10 — Verify Important Files

```bash
unzip -Z1 function.zip | grep -E '^(lambda_function.py|requests/__init__.py|urllib3/__init__.py)$'
```

Expected:

```text
requests/__init__.py
urllib3/__init__.py
lambda_function.py
```

### Step 11 — Validate ZIP Programmatically

```bash
python3 - <<'PY'
import zipfile

with zipfile.ZipFile("function.zip") as archive:
    files = set(archive.namelist())

required = {
    "lambda_function.py",
    "requests/__init__.py",
    "urllib3/__init__.py"
}

missing = required - files

assert not missing, f"Missing files: {missing}"

print("SUCCESS: Deployment package complete")
PY
```

### Broken vs. Recovered Package

| File or Dependency | Broken ZIP | Recovered ZIP |
|---|---|---|
| lambda_function.py | Present | Present |
| requests | Missing | Present |
| urllib3 | Missing | Present |
| certifi | Missing | Present |
| idna | Missing | Present |
| charset-normalizer | Missing | Present |
| Python module imports | Fail | Succeed |

---

## 17. Update Lambda with the Correct Package

### Step 1 — Update Function Code

```bash
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://function.zip \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Update

```bash
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Deployment

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,UpdateStatus:LastUpdateStatus,Runtime:Runtime,Handler:Handler,CodeSize:CodeSize}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
LastUpdateStatus = Successful
Runtime = python3.13
```

### Step 4 — Save Recovered Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab10-recovered-configuration.json
```

---

## 18. Verify Successful Recovery

### Step 1 — Invoke the Same Test Event

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --log-type Tail \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab10-healthy-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab10-healthy-invocation.json
```

Expected:

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
  "body": "{\"message\": \"Dependency imported successfully\", \"dependency\": \"requests\", \"requests_version\": \"2.32.3\", \"http_method\": \"GET\", \"url\": \"https://example.com/api/orders?order_id=ORDER-1001\"}"
}
```

### Step 4 — Verify Programmatically

```bash
python3 - <<'PY'
import json

with open("lab10-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation

assert response["statusCode"] == 200
assert body["dependency"] == "requests"
assert body["requests_version"] == "2.32.3"
assert body["http_method"] == "GET"
assert "ORDER-1001" in body["url"]

print("SUCCESS: Lambda dependency import restored")
print("SUCCESS: Python requests library loaded")
PY
```

### Step 5 — Verify CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Lambda Lab 10 started
Preparing external API request
Python requests dependency loaded
HTTP request prepared successfully
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"HTTP request prepared successfully"' \
  --query 'events[].message' \
  --output json \
  --region "$AWS_REGION" \
  > lab10-recovered-cloudwatch-evidence.json
```

### Recovery Verification

| Check | Broken | Recovered |
|---|---|---|
| Lambda function | Active | Active |
| Handler file | Present | Present |
| requests dependency | Missing | Included |
| Runtime initialization | Failed | Successful |
| FunctionError | Unhandled | Absent |
| Application statusCode | Not returned | 200 |
| Handler execution | Not started | Completed |
| CloudWatch evidence | Import failure | Successful execution |
| IAM role | Unchanged | Unchanged |
| Network configuration | Unchanged | Unchanged |

**Recovery is confirmed when the original Lambda function successfully imports `requests`, executes the handler, and returns statusCode 200.**

---

## 19. Production Troubleshooting Best Practices

### Standard Investigation Checklist

1. Verify the AWS account and Region.
2. Identify the failing Lambda function.
3. Verify the runtime and handler configuration.
4. Reproduce the invocation error.
5. Inspect the Lambda error payload.
6. Read CloudWatch Logs.
7. Determine whether the failure occurs during initialization.
8. Identify the missing Python module.
9. Inspect the deployment ZIP.
10. Verify whether the module exists at the archive root.
11. Review `requirements.txt`.
12. Check dependency version compatibility.
13. Check native binary compatibility if applicable.
14. Rebuild the deployment package.
15. Verify imports in the build environment.
16. Validate ZIP structure.
17. Update the Lambda function code.
18. Repeat the original invocation.
19. Verify successful runtime initialization.
20. Document findings and clean up.

### Common Import-Related Problems

| Problem | Possible Cause | Investigation |
|---|---|---|
| No module named requests | Missing package | Inspect ZIP |
| No module named lambda_function | Missing handler module | Check archive root |
| Runtime.HandlerNotFound | Incorrect handler function | Check Lambda handler |
| No module named shared_utils | Missing application module | Inspect deployment |
| Cannot import name | Version mismatch or circular import | Review package/code |
| Invalid ELF header | Binary incompatible with runtime | Check build platform |
| Missing shared object | Missing native library | Check Linux dependencies |
| Layer import fails | Incorrect layer structure | Inspect layer ZIP |
| Python version incompatibility | Unsupported package version | Check runtime and package |

---

## 20. CI/CD and DevSecOps Improvements

### Reproducible Builds

Define dependencies in a requirements file.

Install them in a clean build environment instead of relying on locally installed packages.

### Dependency Version Pinning

Pin package versions to reduce unexpected behavior between builds.

For more reproducible production builds, also lock transitive dependencies.

### Artifact Validation

Verify the ZIP includes the handler and required modules before deployment.

Example:

```bash
python3 - <<'PY'
import zipfile

with zipfile.ZipFile("function.zip") as archive:
    files = set(archive.namelist())

assert "lambda_function.py" in files
assert "requests/__init__.py" in files

print("PASS: Required deployment files present")
PY
```

### Security Scanning

Production pipelines should scan dependencies for known vulnerabilities and review package provenance.

### Runtime Compatibility

When packaging libraries with native extensions, build or select wheels compatible with Lambda's Linux runtime and CPU architecture.

### CI/CD Deployment Validation

A production pipeline can:

1. Validate Python syntax.
2. Install dependencies.
3. Verify module imports.
4. Build the deployment ZIP.
5. Inspect archive contents.
6. Perform dependency security scans.
7. Deploy to a test Lambda function.
8. Invoke a smoke-test event.
9. Verify the response.
10. Promote the approved artifact.

### Lambda Layers

Layers can provide reusable libraries across Lambda functions.

For Python layers, the expected package layout differs from a regular function ZIP and normally includes a top-level `python/` directory.

---

## 21. Cloud Security Engineering Considerations

### Software Supply Chain Security

Third-party dependencies can introduce security vulnerabilities.

Review and scan Python packages before deployment.

### Dependency Pinning

Uncontrolled dependency upgrades can introduce breaking changes or vulnerable versions.

### Least-Privilege IAM

This application only needs basic CloudWatch logging.

No additional AWS permissions are required for preparing the HTTP request.

### Secret Protection

Do not include API keys, database passwords, or other secrets in deployment archives.

### Artifact Integrity

Use a controlled build pipeline to reduce the risk of missing or modified deployment files.

### Logging

CloudWatch Logs should capture dependency errors without exposing sensitive application information.

---

## 22. AWS Resource Cleanup

**Warning:** Delete only resources created for Lab 10.

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
Project = Lambda-Troubleshooting-Lab10
```

### Step 2 — Verify IAM Role Ownership

```bash
aws iam list-role-tags \
  --role-name "$ROLE_NAME"
```

Confirm the same project tag.

### Step 3 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 4 — Detach IAM Policy

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 5 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 6 — Delete CloudWatch Logs

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 7 — Verify Cleanup

Verify Lambda deletion:

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected: `ResourceNotFoundException`.

Verify IAM role deletion:

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected: `NoSuchEntity`.

Verify CloudWatch deletion:

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

### Step 8 — Remove Generated Build Artifacts

From inside `10-lambda-dependency-import-error/`:

```bash
pwd
```

Verify the current directory.

Then:

```bash
rm -rf package

rm -f broken-function.zip function.zip
```

Keep your source code, `requirements.txt`, test event, and README.

### Cleanup Summary

| Resource | Expected State |
|---|---|
| Lambda function | Deleted |
| IAM execution role | Deleted |
| IAM policy attachment | Removed |
| CloudWatch log group | Deleted |
| Local build packages | Removed |
| EC2 | Not created |
| VPC | Not created |
| NAT Gateway | Not created |
| RDS | Not created |

---

## 23. Interview Questions and Answers

### Q1. What is Runtime.ImportModuleError?

An error reported when Lambda cannot import the handler module or a required dependency.

### Q2. Why did this Lambda function fail?

The deployment ZIP did not contain the `requests` library.

### Q3. Why can the application work locally but fail in Lambda?

The developer's computer may have dependencies installed that are missing from the deployment artifact.

### Q4. Does Lambda automatically install packages from requirements.txt?

No. Dependencies must be packaged or otherwise made available.

### Q5. What is the correct ZIP structure?

The handler and required dependency directories must be accessible from the Python import path, commonly at the ZIP root.

### Q6. What is the difference between ModuleNotFoundError and Runtime.ImportModuleError?

`ModuleNotFoundError` is a Python exception. `Runtime.ImportModuleError` is Lambda's reported initialization failure.

### Q7. What is Runtime.HandlerNotFound?

An error indicating that Lambda cannot locate the configured handler function.

### Q8. How did you identify the missing dependency?

I inspected the invocation error, CloudWatch Logs, and deployment ZIP contents.

### Q9. How did you fix the issue?

I installed the required dependency with pip, rebuilt the ZIP, and updated Lambda.

### Q10. Did the fix require IAM changes?

No. The issue was packaging-related.

### Q11. What is a Lambda layer?

A separate package that provides shared libraries or runtime content to compatible Lambda functions.

### Q12. Why can native Python libraries cause Lambda import errors?

Compiled libraries may be incompatible with Lambda's Linux runtime or CPU architecture.

### Q13. How can CI/CD prevent import errors?

Build in a controlled environment, verify dependencies, test imports, and validate deployment artifacts before release.

### Q14. What is the value of requirements.txt?

It defines Python dependency requirements and supports repeatable installation.

### Q15. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function that required the third-party requests library.

I intentionally created a broken deployment ZIP containing only the Python handler without the dependency.

When I invoked the function, Lambda returned Runtime.ImportModuleError because the requests package was missing.

I investigated CloudWatch Logs, the runtime configuration, and ZIP archive contents.

I identified the incomplete deployment artifact as the root cause.

I installed requests and its dependencies using pip, rebuilt the deployment ZIP with the correct root directory structure, and updated the Lambda function.

After remediation, I invoked the same test event and verified that the library imported successfully and the application returned statusCode 200.

I also reviewed how CI/CD dependency checks and reproducible builds can prevent similar production incidents.

Finally, I deleted all temporary AWS resources.

---

## 24. Repository Structure

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
│
├── 10-lambda-dependency-import-error/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── requirements.txt
│   ├── test-event.json
│   ├── broken-function.zip
│   ├── function.zip
│   ├── package/
│   ├── lab10-resources.env
│   ├── lab10-broken-configuration.json
│   ├── lab10-recovered-configuration.json
│   ├── lab10-broken-invocation.json
│   ├── lab10-healthy-invocation.json
│   ├── lab10-broken-cloudwatch-evidence.json
│   ├── lab10-recovered-cloudwatch-evidence.json
│   ├── broken-response.json
│   └── healthy-response.json
│
├── 11-lambda-concurrency-throttling/
└── 12-lambda-async-retry-dlq-failure/
```

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Production incident documentation |
| lambda_function.py | Python Lambda application |
| lambda-trust-policy.json | IAM trust policy |
| requirements.txt | Python dependencies |
| test-event.json | Lambda invocation payload |
| broken-function.zip | Incomplete deployment artifact |
| function.zip | Rebuilt deployment package |
| package/ | Installed Python dependencies |
| lab10-resources.env | Local AWS resource identifiers |
| lab10-broken-configuration.json | Initial Lambda configuration |
| lab10-recovered-configuration.json | Updated Lambda configuration |
| lab10-broken-invocation.json | Failed invocation metadata |
| lab10-healthy-invocation.json | Successful invocation metadata |
| lab10-broken-cloudwatch-evidence.json | Import error logs |
| lab10-recovered-cloudwatch-evidence.json | Successful execution logs |
| broken-response.json | Import failure response |
| healthy-response.json | Successful application response |

### Recommended Public GitHub Files

```text
10-lambda-dependency-import-error/
├── README.md
├── lambda_function.py
├── lambda-trust-policy.json
├── requirements.txt
└── test-event.json
```

Keep generated deployment archives, locally installed dependency directories, account-specific configuration, and raw execution evidence out of public GitHub commits.

### Recommended Root .gitignore

Add:

```gitignore
# Lambda Lab 10
10-lambda-dependency-import-error/package/
10-lambda-dependency-import-error/*.zip
10-lambda-dependency-import-error/lab10-resources.env
10-lambda-dependency-import-error/lab10-*-configuration.json
10-lambda-dependency-import-error/lab10-*-invocation.json
10-lambda-dependency-import-error/lab10-*-evidence.json
10-lambda-dependency-import-error/*-response.json

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

Files already tracked by Git are not automatically excluded when new `.gitignore` rules are added.

---

## 25. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how missing Python dependencies can cause AWS Lambda runtime initialization failures.

We created a Python application that imported the third-party requests library.

We intentionally deployed the function using a ZIP containing only the Python handler.

The function failed because the required dependency was missing.

CloudWatch Logs reported Runtime.ImportModuleError.

We inspected the Lambda configuration, source code, and ZIP contents to identify the problem.

We then installed the required dependencies into a build directory, rebuilt the ZIP with the correct structure, and updated Lambda.

After remediation, the function successfully imported requests and prepared an HTTP request.

We verified the successful application response without changing IAM or networking configuration.

Finally, we cleaned up the temporary AWS resources.

**Key Lesson:** A successful Lambda deployment does not guarantee successful runtime initialization. Required dependencies must be correctly packaged, compatible with the runtime, and available on the Python import path.

### Skills Demonstrated

- AWS Lambda
- Python 3.13
- Python module imports
- Third-party dependency management
- pip
- requirements.txt
- ZIP deployment packaging
- AWS CLI v2
- Linux Bash
- IAM execution roles
- CloudWatch Logs
- Runtime.ImportModuleError
- ModuleNotFoundError
- Lambda runtime initialization
- Deployment artifact inspection
- Lambda code updates
- Dependency compatibility
- CI/CD packaging checks
- DevSecOps dependency management
- Root cause analysis
- Recovery verification
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-010 |
| Scenario | Lambda Dependency Import Error |
| Function | lambda-lab10-import-error |
| Runtime | Python 3.13 |
| Missing Dependency | requests |
| Broken Deployment | broken-function.zip |
| Error | Runtime.ImportModuleError |
| Root Cause | Incomplete deployment package |
| Remediation | Package dependencies correctly |
| Recovered Deployment | function.zip |
| Import Recovery | Successful |
| Application Response | 200 |
| Source Code Changes | Not required |
| IAM Changes | Not required |
| Cleanup | Lambda, IAM, CloudWatch |
| Incident Status | Resolved after verification |

**Key Takeaway:** Cloud Engineers must understand Python dependency management, Lambda deployment packaging, runtime compatibility, and CI/CD artifact validation to troubleshoot production serverless applications.

---

## Official AWS Documentation

- [AWS Lambda — Python Deployment Packages](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
- [AWS Lambda — Python Layers](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html)
- [AWS Lambda — Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-execution.html)
- [AWS CLI — Update Function Code](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html)
- [AWS Lambda — CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)