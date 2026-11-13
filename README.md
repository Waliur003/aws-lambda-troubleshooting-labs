# AWS Lambda Troubleshooting Labs

**12 Production-Style AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This repository contains 12 hands-on AWS Lambda troubleshooting labs designed to simulate real production incidents encountered by Cloud Engineers, Cloud Security Engineers, DevOps Engineers, and Site Reliability Engineers.

AWS Lambda is a serverless compute service that runs application code without requiring engineers to manage servers.

Although AWS manages the underlying compute infrastructure, engineers remain responsible for troubleshooting application errors, function configurations, networking, dependencies, permissions, and integrations with other AWS services.

In production environments, AWS Lambda failures can interrupt automated workflows, prevent event processing, cause application timeouts, increase costs, and affect critical business operations.

This repository focuses on reproducing, investigating, and resolving these failures using AWS CLI, Linux Bash, Python, Amazon CloudWatch, and other AWS services.

Each lab follows a structured production incident response workflow.

The goal is to develop practical troubleshooting experience that can be demonstrated during Cloud Engineering and Cloud Security Engineering job interviews.

### Repository Objectives

- Understand AWS Lambda architecture and execution behavior.
- Investigate runtime and handler errors.
- Troubleshoot function timeouts.
- Identify missing environment variables.
- Investigate IAM authorization failures.
- Diagnose VPC networking issues.
- Troubleshoot Lambda-to-RDS connectivity.
- Identify memory exhaustion.
- Investigate missing event triggers.
- Resolve dependency import errors.
- Diagnose concurrency and throttling.
- Troubleshoot asynchronous retries and failed-event delivery.
- Use AWS CLI to investigate real AWS resources.
- Analyze CloudWatch logs and metrics.
- Practice root cause analysis and remediation.
- Verify recovery using actual AWS API responses.
- Safely remove temporary infrastructure.

---

## 1. Technologies Used

| Technology | Purpose |
|---|---|
| AWS Lambda | Serverless compute |
| AWS CLI v2 | Deployment, configuration, and troubleshooting |
| Python 3 | Lambda function code and diagnostic scripts |
| Linux / WSL2 Ubuntu | Command-line working environment |
| Bash | Automation and troubleshooting |
| Amazon CloudWatch Logs | Runtime and error investigation |
| Amazon CloudWatch Metrics | Duration, errors, throttles, and concurrency |
| AWS IAM | Execution roles and authorization |
| Amazon VPC | Private networking |
| Amazon EC2 Networking | Subnets, routes, and security groups |
| NAT Gateway | Outbound internet access from private subnets |
| Amazon RDS | Database connectivity troubleshooting |
| Amazon EventBridge | Event-driven Lambda invocation |
| Amazon S3 | Event sources and deployment artifacts |
| Amazon SQS | Asynchronous failure handling and queues |
| AWS STS | Identity verification |
| Git and GitHub | Source control and incident documentation |

### Primary Environment

```text
Operating System: WSL2 Ubuntu
Shell: Bash
AWS Region: us-east-1
AWS CLI: Version 2
Runtime: Supported Python 3.x Lambda runtime
Infrastructure: AWS CLI
Documentation: GitHub Markdown
```

The runtime version is selected from currently supported AWS Lambda Python runtimes when each lab is deployed.

---

## 2. Repository Structure

```text
aws-lambda-troubleshooting-labs/
│
├── README.md
├── .gitignore
│
├── 01-lambda-runtime-error/
│   └── README.md
│
├── 02-handler-not-found/
│   └── README.md
│
├── 03-lambda-timeout/
│   └── README.md
│
├── 04-missing-environment-variable/
│   └── README.md
│
├── 05-lambda-access-denied/
│   └── README.md
│
├── 06-lambda-no-internet-vpc/
│   └── README.md
│
├── 07-lambda-rds-connection-failure/
│   └── README.md
│
├── 08-lambda-memory-exhaustion/
│   └── README.md
│
├── 09-lambda-event-not-triggering/
│   └── README.md
│
├── 10-lambda-dependency-import-error/
│   └── README.md
│
├── 11-lambda-concurrency-throttling/
│   └── README.md
│
└── 12-lambda-async-retry-dlq-failure/
    └── README.md
```

The folders represent the planned lab structure. Individual lab files, scripts, configurations, and evidence are added as each practical exercise is completed.

---

## 3. Troubleshooting Lab Catalog

| Lab | Scenario | Primary Troubleshooting Area | Difficulty |
|---|---|---|---|
| 01 | Lambda Runtime Error | Runtime exceptions and logs | Beginner |
| 02 | Handler Not Found | Handler configuration | Beginner |
| 03 | Lambda Timeout | Duration and timeout settings | Beginner |
| 04 | Missing Environment Variable | Function configuration | Beginner |
| 05 | Lambda AccessDenied | Execution role permissions | Intermediate |
| 06 | Lambda Cannot Reach Internet from VPC | Subnets, NAT, routes | Advanced |
| 07 | Lambda Cannot Connect to RDS | Database and VPC connectivity | Advanced |
| 08 | Lambda Memory Exhaustion | Memory utilization | Intermediate |
| 09 | Lambda Event Not Triggering | Event sources and permissions | Intermediate |
| 10 | Lambda Dependency Import Error | Python packages and deployment | Intermediate |
| 11 | Lambda Reserved Concurrency / Throttling | Scaling and concurrency limits | Advanced |
| 12 | Lambda Asynchronous Retry and DLQ Failure | Retries, SQS, failure handling | Advanced |

---

## 4. Lab 01 — Lambda Runtime Error

**Folder:** `01-lambda-runtime-error/`

### Production Scenario

An AWS Lambda function is deployed successfully.

However, when the application invokes the function, execution fails with a Python runtime exception.

The Cloud Engineering team must investigate the CloudWatch logs, identify the failed operation, and correct the application code.

### Common Symptoms

- Lambda function exists and can be invoked.
- Function returns an error.
- CloudWatch Logs show a Python exception.
- Error metrics increase.
- Business logic does not complete.

### Troubleshooting Focus

- Lambda invocation response.
- Python exceptions.
- CloudWatch log groups.
- CloudWatch log streams.
- Stack traces.
- Runtime error identification.
- Code correction.
- Recovery verification.

### Expected Outcome

Identify the runtime exception, correct the code, redeploy the function, and verify successful invocation.

---

## 5. Lab 02 — Handler Not Found

**Folder:** `02-handler-not-found/`

### Production Scenario

A Lambda deployment completes successfully, but the function fails during initialization because the configured handler cannot be found.

The engineer must determine whether the handler name, Python module, or deployment package is incorrect.

### Common Symptoms

```text
Runtime.HandlerNotFound
```

Other runtime and import-related errors may appear depending on the deployment configuration.

### Troubleshooting Focus

- Handler configuration.
- Python module names.
- Python function names.
- Deployment ZIP structure.
- Lambda initialization errors.
- AWS CLI configuration inspection.
- Handler remediation.

### Expected Outcome

Correct the handler setting or deployment structure and verify successful invocation.

---

## 6. Lab 03 — Lambda Timeout

**Folder:** `03-lambda-timeout/`

### Production Scenario

A Lambda function begins execution but does not finish before its configured timeout.

The application fails, and CloudWatch shows that the function exceeded its allowed execution time.

### Common Symptoms

```text
Task timed out after ... seconds
```

### Troubleshooting Focus

- Function timeout settings.
- CloudWatch Duration metric.
- Slow application operations.
- External API latency.
- Blocking code.
- Performance investigation.
- Timeout configuration.
- Application optimization.

### Expected Outcome

Identify why execution exceeds the configured timeout and restore successful function completion.

---

## 7. Lab 04 — Missing Environment Variable

**Folder:** `04-missing-environment-variable/`

### Production Scenario

A Lambda function depends on an environment variable that was omitted during deployment.

The function raises an exception because its required configuration is missing.

### Common Symptoms

```text
KeyError
Missing required configuration
```

### Troubleshooting Focus

- Lambda environment variables.
- Function configuration.
- Python environment access.
- Missing application configuration.
- Deployment mistakes.
- Safe configuration updates.

### Expected Outcome

Identify the missing variable, update the Lambda configuration, and verify successful execution.

Sensitive credentials should not be placed directly in source code or exposed through logs. Use a suitable AWS secrets management service for actual secrets.

---

## 8. Lab 05 — Lambda AccessDenied

**Folder:** `05-lambda-access-denied/`

### Production Scenario

A Lambda function attempts to access an AWS resource but its execution role lacks the required authorization.

For example, a function attempts to read an S3 object but receives an AccessDenied error.

### Common Symptoms

```text
AccessDenied
AccessDeniedException
```

### Troubleshooting Focus

- Lambda execution role.
- IAM permissions policies.
- S3 resource permissions.
- Identity-based versus resource-based authorization.
- STS caller identity.
- CloudWatch errors.
- Least-privilege remediation.

### Expected Outcome

Identify the missing permission, apply the minimum necessary authorization, and verify successful access.

---

## 9. Lab 06 — Lambda Cannot Reach Internet from VPC

**Folder:** `06-lambda-no-internet-vpc/`

### Production Scenario

A Lambda function is attached to private subnets inside a VPC.

The function attempts to connect to a public HTTPS endpoint but the request times out.

The engineer must investigate the VPC routing and outbound network configuration.

### Common Symptoms

```text
Connection timed out
Network unreachable
```

### Troubleshooting Focus

- Lambda VPC configuration.
- Private subnets.
- Route tables.
- NAT Gateway.
- Internet Gateway.
- Security group egress.
- Network ACL rules.
- DNS resolution.
- Outbound HTTPS connectivity.

### Expected Outcome

Identify the missing outbound connectivity path and verify that the function can reach the intended external endpoint.

Attaching a Lambda function to a public subnet alone does not give it normal internet access through an Internet Gateway.

---

## 10. Lab 07 — Lambda Cannot Connect to RDS

**Folder:** `07-lambda-rds-connection-failure/`

### Production Scenario

A Lambda function needs to connect to a private Amazon RDS PostgreSQL database.

The Lambda function is deployed, but the connection fails or times out.

The engineer must investigate networking, security groups, database endpoint configuration, and authentication.

### Common Symptoms

```text
Connection timed out
Connection refused
Authentication failed
```

### Troubleshooting Focus

- Lambda and RDS VPC configuration.
- Private subnet routing.
- Security groups.
- Database port 5432.
- RDS endpoint resolution.
- Database availability.
- Connection timeout.
- PostgreSQL authentication.
- Database connection handling.

### Expected Outcome

Identify the connectivity failure and verify a successful database connection.

---

## 11. Lab 08 — Lambda Memory Exhaustion

**Folder:** `08-lambda-memory-exhaustion/`

### Production Scenario

A Lambda function processes a workload that requires more memory than its configured limit.

The function terminates unexpectedly or fails to complete.

### Common Symptoms

```text
Runtime.OutOfMemory
```

The exact log message varies by runtime and execution environment.

### Troubleshooting Focus

- Lambda memory configuration.
- CloudWatch REPORT entries.
- Max Memory Used.
- Memory-intensive Python operations.
- Resource consumption.
- Application optimization.
- Memory allocation adjustment.

### Expected Outcome

Identify memory pressure, correct the workload or memory configuration, and verify stable function execution.

---

## 12. Lab 09 — Lambda Event Not Triggering

**Folder:** `09-lambda-event-not-triggering/`

### Production Scenario

An application expects a Lambda function to run after an AWS event, but no invocation occurs.

The engineer must investigate the event source and Lambda integration.

### Common Symptoms

- No function invocation.
- No new application log stream.
- Trigger appears configured incorrectly.
- Expected business event is not processed.

### Troubleshooting Focus

- EventBridge rules.
- EventBridge event patterns.
- Event targets.
- Lambda resource-based permissions.
- Event source configuration.
- CloudWatch invocation metrics.
- Trigger verification.

### Expected Outcome

Identify the event routing or permission problem and confirm that the expected event invokes the Lambda function.

---

## 13. Lab 10 — Lambda Dependency Import Error

**Folder:** `10-lambda-dependency-import-error/`

### Production Scenario

A Python Lambda function imports a library that is not included in its deployment package or compatible Lambda layer.

The function fails during initialization.

### Common Symptoms

```text
Runtime.ImportModuleError
No module named ...
```

### Troubleshooting Focus

- Python dependencies.
- pip.
- Deployment ZIP structure.
- Lambda layers.
- Python package compatibility.
- Native dependencies.
- Runtime version.
- Import failures.

### Expected Outcome

Package dependencies correctly, redeploy the function, and verify successful initialization.

---

## 14. Lab 11 — Lambda Reserved Concurrency / Throttling

**Folder:** `11-lambda-concurrency-throttling/`

### Production Scenario

A Lambda function receives more simultaneous requests than its available concurrency permits.

Some requests are throttled, causing application failures or delays.

### Common Symptoms

```text
TooManyRequestsException
```

### Troubleshooting Focus

- Reserved concurrency.
- ConcurrentExecutions metric.
- Throttles metric.
- Function-level concurrency limits.
- Regional account concurrency quotas.
- Synchronous invocation failure.
- Traffic control.
- Retry behavior.

### Expected Outcome

Identify whether function-level or account-level concurrency restrictions are causing throttling and apply an appropriate remediation.

The exercise must not increase traffic enough to disrupt unrelated workloads in the AWS account.

---

## 15. Lab 12 — Lambda Asynchronous Retry and DLQ Failure

**Folder:** `12-lambda-async-retry-dlq-failure/`

### Production Scenario

A Lambda function processes asynchronous events but repeatedly fails.

The application expects failed events to reach a dead-letter queue or an on-failure destination.

However, the configured failure-handling path does not work as expected.

### Common Symptoms

- Repeated function errors.
- Multiple invocation attempts.
- Failed events not found in expected queue.
- Incorrect destination configuration.
- Delivery failure metrics.

### Troubleshooting Focus

- Asynchronous invocation.
- Event retry configuration.
- MaximumRetryAttempts.
- MaximumEventAgeInSeconds.
- Amazon SQS.
- Dead-letter queues.
- On-failure destinations.
- IAM permissions.
- DeadLetterErrors.
- DestinationDeliveryFailures.
- Failed-event recovery.

### Expected Outcome

Identify the retry or delivery failure and verify that failed events are handled according to the intended configuration.

Retry behavior depends on the invocation method and source. Function-managed asynchronous retries differ from retries managed by services such as SQS.

---

## 16. Standard Production Troubleshooting Methodology

Every lab follows the same investigation framework.

### Step 1 — Understand the Incident

Identify the symptoms, affected resources, and expected application behavior.

### Step 2 — Create a Controlled Environment

Provision dedicated AWS resources using AWS CLI and Bash.

### Step 3 — Establish a Healthy Baseline

Verify normal operation before introducing the fault whenever practical.

### Step 4 — Inject the Failure

Introduce a specific, reproducible misconfiguration or application error.

### Step 5 — Reproduce the Incident

Invoke the function or generate the triggering event.

Confirm the expected failure occurred.

### Step 6 — Collect Evidence

Inspect the relevant AWS API responses, Lambda configuration, CloudWatch metrics, and log entries.

### Step 7 — Investigate the Root Cause

Determine which configuration, permission, dependency, or application behavior caused the failure.

### Step 8 — Apply Remediation

Fix the specific underlying problem.

Avoid unnecessary broad permission changes or network access.

### Step 9 — Verify Recovery

Repeat the same operation and confirm successful behavior using real AWS responses and logs.

### Step 10 — Clean Up Resources

Delete temporary Lambda functions, log groups where appropriate, execution roles, supporting infrastructure, and other lab-created resources.

### Incident Workflow

```text
Production Symptom
        |
        v
Confirm Failure
        |
        v
Inspect Lambda Configuration
        |
        v
Review CloudWatch Logs
        |
        v
Check Related AWS Services
        |
        v
Identify Root Cause
        |
        v
Apply Remediation
        |
        v
Invoke or Trigger Again
        |
        v
Verify Successful Recovery
        |
        v
Preserve Evidence and Cleanup
```

---

## 17. AWS Lambda Troubleshooting Commands

These commands are used repeatedly throughout the repository.

### List Lambda Functions

```bash
aws lambda list-functions \
  --region us-east-1
```

### Inspect Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

### Inspect Function Details

```bash
aws lambda get-function \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

### Invoke Lambda

```bash
aws lambda invoke \
  --function-name FUNCTION_NAME \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  --region us-east-1 \
  response.json
```

### View Invocation Response

```bash
cat response.json
```

### Inspect Recent CloudWatch Logs

```bash
aws logs tail "/aws/lambda/FUNCTION_NAME" \
  --since 10m \
  --region us-east-1
```

### Follow Logs During Investigation

```bash
aws logs tail "/aws/lambda/FUNCTION_NAME" \
  --follow \
  --region us-east-1
```

### Inspect Lambda Metrics

Use CloudWatch metrics such as:

```text
Invocations
Errors
Duration
Throttles
ConcurrentExecutions
AsyncEventsDropped
DeadLetterErrors
DestinationDeliveryFailures
```

Metric availability and applicability depend on the function and invocation configuration.

### Inspect Lambda Permissions

```bash
aws lambda get-policy \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

A function without a resource-based policy may return a not-found error for this operation. This does not automatically mean the execution role is missing.

### Inspect Reserved Concurrency

```bash
aws lambda get-function-concurrency \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

### Inspect Event Source Mappings

```bash
aws lambda list-event-source-mappings \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

### Inspect Async Invocation Configuration

```bash
aws lambda get-function-event-invoke-config \
  --function-name FUNCTION_NAME \
  --region us-east-1
```

Some functions may not have an explicitly configured asynchronous invocation configuration.

---

## 18. CloudWatch Investigation Strategy

CloudWatch is one of the primary tools used in Lambda troubleshooting.

### Important Log Information

- Invocation request ID.
- Python traceback.
- Exception type.
- Error message.
- START and END records.
- REPORT records.
- Duration.
- Billed duration.
- Configured memory.
- Max memory used.

### Important Metrics

| Metric | Investigation Purpose |
|---|---|
| Invocations | Determines whether the function ran |
| Errors | Identifies failed invocations |
| Duration | Investigates slow execution |
| Throttles | Detects rejected invocation requests |
| ConcurrentExecutions | Analyzes concurrent activity |
| AsyncEventsDropped | Investigates dropped asynchronous events |
| DeadLetterErrors | Investigates DLQ delivery failures |
| DestinationDeliveryFailures | Investigates destination delivery problems |

A common troubleshooting approach is to compare the Lambda invocation response with the CloudWatch log entries for the same request ID.

---

## 19. Security Best Practices

All labs are performed with security-focused resource configurations.

### IAM Security

- Use dedicated execution roles.
- Apply least-privilege permissions.
- Avoid unnecessary wildcard access.
- Verify the role being used.
- Remove temporary roles after the lab.

### Network Security

- Keep private workloads in appropriate subnets.
- Avoid exposing database endpoints unnecessarily.
- Restrict security group ingress.
- Use only required outbound connectivity.
- Prefer private AWS service access where appropriate.

### Application Security

- Avoid logging secrets or credentials.
- Validate application inputs.
- Use environment variables for nonsecret configuration.
- Use appropriate secrets management for sensitive information.
- Handle exceptions safely.
- Implement idempotent event processing where required.

### Operational Security

- Monitor function errors and throttling.
- Configure appropriate retry behavior.
- Use failure destinations or DLQs when required.
- Protect audit logs.
- Document changes and cleanup.
- Review the costs of networking and database services.

---

## 20. Cost Management and Cleanup

Most basic Lambda labs use small execution workloads and short test durations.

However, some advanced labs create supporting AWS infrastructure that can generate charges.

### Resources Requiring Special Attention

| Resource | Cost Consideration |
|---|---|
| Lambda | Requests and execution duration |
| CloudWatch Logs | Ingestion and retention |
| NAT Gateway | Hourly and data processing charges |
| Amazon RDS | Instance and storage charges |
| VPC networking | Depends on created components |
| Amazon SQS | API requests and usage |
| EventBridge | Event usage depending on source and configuration |

### Cleanup Requirements

After each practical lab:

1. Delete the temporary Lambda function.
2. Delete dedicated event sources or triggers.
3. Delete lab IAM policies and roles.
4. Remove temporary networking resources.
5. Delete disposable database resources.
6. Delete SQS queues and EventBridge rules created for the lab.
7. Remove dedicated log groups when appropriate.
8. Verify no unintended billable resources remain.

Never delete shared or existing production resources during cleanup.

The exact cleanup procedure is provided separately for every lab.

---

## 21. Skills Demonstrated

This repository develops practical skills in:

- AWS Lambda architecture.
- Serverless application troubleshooting.
- Python exception investigation.
- Lambda runtime and handler configuration.
- Timeout analysis.
- Environment variable troubleshooting.
- IAM authorization investigation.
- AWS VPC networking.
- NAT Gateway and route analysis.
- Private database connectivity.
- RDS PostgreSQL.
- Lambda memory optimization.
- EventBridge event delivery.
- Lambda dependency packaging.
- Concurrency and throttling.
- Asynchronous retries.
- Amazon SQS and dead-letter queues.
- CloudWatch monitoring.
- AWS CLI troubleshooting.
- Linux Bash automation.
- Root cause analysis.
- Incident recovery verification.
- AWS resource cleanup.

### Career Relevance

These scenarios are relevant to the responsibilities of:

- Cloud Engineer
- Cloud Security Engineer
- Junior Cloud Engineer
- Cloud Operations Engineer
- DevOps Engineer
- Platform Engineer
- Site Reliability Engineer
- Infrastructure Engineer

### Expected Learning Outcome

By completing these 12 labs, an engineer should be better prepared to diagnose common AWS Lambda production failures, determine their root causes, apply targeted remediations, and explain investigation findings during technical interviews.

The repository provides a foundation for production troubleshooting experience, but practical job readiness also requires broader experience with application architecture, monitoring, deployment practices, and incident response.

---

## Official AWS Documentation

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)
- [Troubleshooting Lambda Invocation Issues](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-invocation.html)
- [Troubleshooting Lambda Configuration](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-configuration.html)
- [Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [Lambda VPC Networking](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
- [Lambda Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)
- [Lambda Asynchronous Invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html)
- [Asynchronous Retry Handling](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)

---

## Conclusion

This repository contains 12 production-style AWS Lambda troubleshooting scenarios.

Each lab focuses on reproducing a real technical problem, investigating it with AWS CLI and CloudWatch, identifying the root cause, applying remediation, and verifying recovery.

The purpose of this repository is to build practical AWS Lambda troubleshooting knowledge that supports Cloud Engineering, Cloud Security Engineering, DevOps, and infrastructure operations careers.

**Focus: Reproduce the failure. Investigate the evidence. Identify the root cause. Apply remediation. Verify recovery.**
