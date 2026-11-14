# Lab 07 — AWS Lambda RDS Connection Failure

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to troubleshoot an AWS Lambda function that cannot connect to an Amazon RDS PostgreSQL database because of an incorrect security group configuration.

In production, Lambda functions often communicate with private relational databases to retrieve customer information, process transactions, and perform background operations.

Even when Lambda and RDS are deployed inside the same VPC, connectivity can fail if security groups, subnet routing, DNS settings, or database configurations are incorrect.

In this lab, we deploy an RDS PostgreSQL instance and a Python Lambda function into private subnets across two Availability Zones.

We intentionally configure the RDS security group to allow PostgreSQL traffic from the wrong security group.

When the Lambda function attempts to establish a TCP connection to PostgreSQL, the connection times out.

We investigate the failure using AWS CLI, CloudWatch Logs, VPC route tables, security groups, and RDS configuration.

After identifying the root cause, we update the RDS inbound security group rule to allow TCP 5432 from the correct Lambda security group.

We then invoke the same Lambda function and verify that it can establish a TCP connection, authenticate with PostgreSQL, and execute a SQL query.

Finally, we remove the temporary RDS, Lambda, IAM, VPC, and CloudWatch resources.

### Troubleshooting Workflow

```text
Create Dedicated VPC
          |
          v
Create Two Private Subnets
          |
          v
Configure Private Route Table
          |
          v
Create Lambda Security Group
          |
          v
Create RDS Security Group
          |
          v
Create Wrong Security Group
          |
          v
Allow RDS Access from Wrong SG
          |
          v
Deploy Private RDS PostgreSQL
          |
          v
Create Python Lambda Application
          |
          v
Configure Lambda Execution Role
          |
          v
Deploy Lambda into VPC
          |
          v
Invoke Database Connection Test
          |
          v
TCP Connection Timeout
          |
          v
Investigate CloudWatch Logs
          |
          v
Inspect RDS Security Group
          |
          v
Identify Incorrect SG Reference
          |
          v
Allow TCP 5432 from Lambda SG
          |
          v
Repeat Lambda Invocation
          |
          v
PostgreSQL Connection Successful
          |
          v
Execute SQL Query
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
| Incident ID | INC-LAMBDA-007 |
| Lab Name | Lambda RDS Connection Failure |
| Difficulty | Intermediate |
| Primary AWS Services | AWS Lambda, Amazon RDS, Amazon VPC |
| Supporting Services | IAM, CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Tools | AWS CLI v2, Bash, Python |
| Lambda Runtime | Python 3.13 |
| Lambda Function | `lambda-lab07-rds-connection` |
| Lambda Execution Role | `lambda-lab07-execution-role` |
| PostgreSQL Driver | `pg8000` |
| VPC CIDR | `10.207.0.0/16` |
| Private Subnet A | `10.207.1.0/24` |
| Private Subnet B | `10.207.2.0/24` |
| Availability Zones | `us-east-1a`, `us-east-1b` |
| RDS Engine | PostgreSQL |
| RDS Instance | `lambda-lab07-postgres` |
| RDS Instance Class | `db.t4g.micro` |
| Storage | 20 GiB gp3 |
| Storage Encryption | Enabled |
| Public Accessibility | Disabled |
| Database Name | `labdb` |
| Database User | `labadmin` |
| Database Port | TCP 5432 |
| DB Subnet Group | `lambda-lab07-db-subnet-group` |
| Lambda Security Group | `lambda-lab07-client-sg` |
| RDS Security Group | `lambda-lab07-db-sg` |
| Incorrect Security Group | `lambda-lab07-wrong-sg` |
| Lambda Timeout | 15 seconds |
| TCP Connection Timeout | 4 seconds |
| Broken Application Response | 503 |
| Recovered Application Response | 200 |
| Root Cause | Incorrect RDS inbound SG reference |
| Remediation | Allow PostgreSQL from Lambda SG |
| Recovery Test | SQL SELECT query |
| NAT Gateway | Not required |
| Cleanup | RDS, Lambda, IAM, VPC, CloudWatch |

### Learning Objectives

- Understand Lambda-to-RDS private networking.
- Deploy RDS PostgreSQL in private subnets.
- Understand DB subnet groups.
- Create and manage security groups.
- Understand security group references.
- Reproduce TCP connection timeouts.
- Distinguish networking failures from database authentication failures.
- Deploy a Python PostgreSQL client in Lambda.
- Package Python dependencies for Lambda.
- Investigate CloudWatch exception logs.
- Inspect RDS endpoints and security groups.
- Diagnose incorrect inbound authorization.
- Restore database connectivity.
- Execute a real PostgreSQL SQL query.
- Understand why NAT is not needed for local VPC connectivity.
- Practice production-style root cause analysis.
- Perform safe resource cleanup.

---

## 2. Production Incident Scenario

### Incident Description

A company uses AWS Lambda to read and process data stored in Amazon RDS PostgreSQL.

The application runs inside a private VPC and communicates with the database using its private endpoint.

The infrastructure team deploys the database and attaches a security group that allows TCP 5432.

However, the inbound rule references the wrong source security group.

The Lambda function uses a different security group and cannot establish a database connection.

When the function invokes the PostgreSQL connection, the TCP handshake cannot complete.

The application returns a connection failure, while CloudWatch Logs report a socket timeout.

The Cloud Engineering team begins investigating.

The engineer confirms that:

- The RDS instance is available.
- The database endpoint exists.
- PostgreSQL is configured on port 5432.
- Lambda and RDS are in the same VPC.
- The VPC local route exists.
- Lambda outbound traffic is permitted.
- The RDS security group references the wrong source group.

The engineer removes the incorrect inbound rule and allows PostgreSQL traffic from the actual Lambda security group.

After the security group change, Lambda successfully connects to RDS and executes a SQL query.

### Incident Symptoms

- Lambda function is Active.
- RDS instance is Available.
- Database is not publicly accessible.
- Lambda application starts successfully.
- TCP connection to RDS times out.
- PostgreSQL authentication is never reached.
- CloudWatch records a connection failure.
- Database security group references the wrong source.
- Lambda returns an application-level 503 response.

### Business Impact

Lambda-to-RDS failures may affect:

- Customer order processing.
- Payment and transaction applications.
- Reporting workflows.
- Backend APIs.
- Data retrieval services.
- Scheduled database operations.
- Event-driven applications.
- Business automation.

### Objective

Identify the network authorization failure, correct the RDS security group, and verify a successful database connection and SQL query without exposing PostgreSQL to the public internet.

---

## 3. AWS Architecture

### Broken Architecture

```text
                  AWS CLI
                     |
                     v
               Lambda Invoke
                     |
                     v
+------------------------------------------------+
|                Amazon VPC                      |
|              10.207.0.0/16                     |
|                                                |
|  Private Subnet A        Private Subnet B       |
|  10.207.1.0/24           10.207.2.0/24          |
|                                                |
|  +------------------+   +-------------------+  |
|  |   AWS Lambda     |   |  RDS PostgreSQL   |  |
|  |                  |   |                   |  |
|  |  Lambda-SG       |   |       DB-SG       |  |
|  |                  |   |                   |  |
|  |  Outbound 5432   |   | Inbound 5432 from |  |
|  |  to DB-SG        |   |     Wrong-SG      |  |
|  +--------+---------+   +---------+---------+  |
|           |                       |            |
|           +------ TCP 5432 ------X            |
|                                   |            |
|                             Traffic Blocked    |
|                                                |
|           Local VPC Routing Exists             |
|           No NAT Gateway Required              |
+------------------------------------------------+
                     |
                     v
             TCP Connection Timeout
                     |
                     v
              CloudWatch Logs
```

### Recovered Architecture

```text
                  AWS CLI
                     |
                     v
               Lambda Invoke
                     |
                     v
+------------------------------------------------+
|                Amazon VPC                      |
|              10.207.0.0/16                     |
|                                                |
|  Private Subnet A        Private Subnet B       |
|                                                |
|  +------------------+   +-------------------+  |
|  |   AWS Lambda     |   |  RDS PostgreSQL   |  |
|  |                  |   |                   |  |
|  |  Lambda-SG       |   |       DB-SG       |  |
|  |                  |   |                   |  |
|  |  Outbound 5432   |   | Inbound 5432 from |  |
|  |  to DB-SG        |   |     Lambda-SG     |  |
|  +--------+---------+   +---------+---------+  |
|           |                       |            |
|           +------ TCP 5432 ------>|            |
|                                   |            |
|                           Connection Allowed   |
|                                   |            |
|                           PostgreSQL Login     |
|                                   |            |
|                            SQL SELECT Query    |
|                                                |
+------------------------------------------------+
                     |
                     v
             Successful SQL Result
                     |
                     v
               statusCode: 200
```

### Architecture Components

| Component | Purpose |
|---|---|
| Amazon VPC | Private network environment |
| Private Subnet A | Lambda/RDS network placement |
| Private Subnet B | Additional AZ for DB subnet group and Lambda |
| Private Route Table | Local VPC connectivity |
| Lambda Security Group | Controls Lambda network traffic |
| RDS Security Group | Controls PostgreSQL inbound access |
| Wrong Security Group | Creates the intentional incident |
| Amazon RDS | Managed PostgreSQL database |
| DB Subnet Group | Defines subnets available to RDS |
| AWS Lambda | Runs database connectivity test |
| IAM Execution Role | Supports Lambda VPC access and logging |
| CloudWatch Logs | Records connection errors and successful queries |
| pg8000 | Python PostgreSQL database driver |

---

## 4. Understanding Lambda-to-RDS Connectivity

### How Does Lambda Connect to RDS?

A VPC-connected Lambda function communicates with an RDS instance through private network connectivity.

The client connects to the RDS endpoint using the database port.

For PostgreSQL:

```text
TCP 5432
```

### Does Lambda Need a NAT Gateway to Connect to Private RDS?

No.

When Lambda and RDS use reachable private addresses in the same VPC, communication uses VPC local routing.

A NAT Gateway is not required for this database connection.

### What Is a DB Subnet Group?

A DB subnet group is a collection of VPC subnets that RDS can use when placing database resources.

For this lab, the group contains one private subnet in each of two Availability Zones.

### What Is a Security Group Reference?

A security group rule can identify another security group as the source or destination instead of using a CIDR block.

Example:

```text
Inbound:
TCP 5432
Source: Lambda-SG
```

This permits eligible traffic from network interfaces associated with the referenced security group.

### Why Does the Wrong Security Group Cause a Timeout?

The database security group permits traffic from `Wrong-SG`, but the Lambda function uses `Lambda-SG`.

The Lambda source does not match the allowed source.

Therefore, the database security group blocks the inbound connection.

### What Is the Difference Between Timeout and Authentication Failure?

**Connection timeout:**

```text
Lambda cannot establish TCP connectivity.
```

**Authentication failure:**

```text
Lambda connects to PostgreSQL,
but the database rejects the credentials.
```

These are different troubleshooting categories.

### Is a Successful TCP Connection Enough?

No.

TCP connectivity only confirms that a network connection can be established.

A complete database test should also verify authentication and SQL execution.

### Why Use pg8000?

`pg8000` is a pure-Python PostgreSQL driver.

It allows the function to establish a PostgreSQL connection and execute SQL without requiring a compiled `psycopg2` library.

### Why Is RDS Private?

The database does not need to accept connections from the public internet.

Private network placement and security group restrictions reduce unnecessary exposure.

### What Is RDS Proxy?

Amazon RDS Proxy is a managed database proxy that can pool database connections and help Lambda applications handle high connection concurrency.

RDS Proxy is not required for this controlled exercise.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Python 3.
- Python pip.
- ZIP and unzip.
- Permissions to manage VPC resources.
- Permissions to create and delete RDS instances.
- Permissions to manage IAM roles.
- Permissions to deploy Lambda functions.
- CloudWatch Logs access.

### Required AWS Permission Categories

```text
sts:GetCallerIdentity

ec2:CreateVpc
ec2:ModifyVpcAttribute
ec2:CreateSubnet
ec2:CreateRouteTable
ec2:AssociateRouteTable
ec2:CreateSecurityGroup
ec2:AuthorizeSecurityGroupIngress
ec2:AuthorizeSecurityGroupEgress
ec2:RevokeSecurityGroupIngress
ec2:RevokeSecurityGroupEgress
ec2:DescribeSecurityGroups
ec2:DescribeSubnets
ec2:DescribeRouteTables
ec2:DescribeNetworkAcls
ec2:DescribeNetworkInterfaces
ec2:DeleteSecurityGroup
ec2:DisassociateRouteTable
ec2:DeleteRouteTable
ec2:DeleteSubnet
ec2:DeleteVpc

rds:CreateDBSubnetGroup
rds:DescribeDBSubnetGroups
rds:CreateDBInstance
rds:DescribeDBInstances
rds:ListTagsForResource
rds:DeleteDBInstance
rds:DeleteDBSubnetGroup

iam:CreateRole
iam:AttachRolePolicy
iam:ListAttachedRolePolicies
iam:DetachRolePolicy
iam:DeleteRole
iam:PassRole

lambda:CreateFunction
lambda:GetFunctionConfiguration
lambda:GetFunction
lambda:InvokeFunction
lambda:DeleteFunction
lambda:ListTags

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:FilterLogEvents
logs:DeleteLogGroup
```

Additional describe, tagging, and service-dependent permissions may be needed in restricted AWS environments.

### Safety Rules

- Create a dedicated lab VPC.
- Never modify production RDS security groups.
- Keep PostgreSQL private.
- Never allow TCP 5432 from `0.0.0.0/0`.
- Use a randomly generated lab password.
- Do not commit database credentials.
- Do not print passwords in logs.
- Verify project tags before cleanup.
- Delete the database after testing.
- Do not manually delete Lambda-managed ENIs.

### Cost Warning

Amazon RDS incurs charges for compute and storage.

This lab uses a small single-AZ database to minimize costs.

Delete the database and associated resources after completing the exercise.

---

## 6. Prepare the Linux Environment

### Step 1 — Create the Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 07-lambda-rds-connection-failure

cd 07-lambda-rds-connection-failure
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
python3 -m pip --version
zip -v
```

Install dependencies if necessary:

```bash
sudo apt update
sudo apt install -y python3-pip zip unzip
```

### Step 3 — Configure Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account --output text)

export PROJECT_TAG="Lambda-Troubleshooting-Lab07"

export VPC_CIDR="10.207.0.0/16"
export PRIVATE_A_CIDR="10.207.1.0/24"
export PRIVATE_B_CIDR="10.207.2.0/24"

export AZ_A="us-east-1a"
export AZ_B="us-east-1b"

export FUNCTION_NAME="lambda-lab07-rds-connection"

export ROLE_NAME="lambda-lab07-execution-role"

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export DB_INSTANCE_ID="lambda-lab07-postgres"

export DB_SUBNET_GROUP="lambda-lab07-db-subnet-group"

export DB_NAME="labdb"
export DB_USER="labadmin"
export DB_PORT="5432"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"
```

### Step 4 — Generate the Database Password

```bash
export DB_PASSWORD=$(python3 - <<'PY'
import secrets
import string

alphabet = string.ascii_letters + string.digits

print(
    ''.join(
        secrets.choice(alphabet)
        for _ in range(28)
    )
)
PY
)
```

Store locally:

```bash
umask 077

printf '%s' "$DB_PASSWORD" > lab07-db-password.txt

chmod 600 lab07-db-password.txt
```

### Step 5 — Save Lab Resource Identifiers

```bash
cat > lab07-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export ACCOUNT_ID="$ACCOUNT_ID"
export PROJECT_TAG="$PROJECT_TAG"
export AZ_A="$AZ_A"
export AZ_B="$AZ_B"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export DB_INSTANCE_ID="$DB_INSTANCE_ID"
export DB_SUBNET_GROUP="$DB_SUBNET_GROUP"
export DB_NAME="$DB_NAME"
export DB_USER="$DB_USER"
export DB_PORT="$DB_PORT"
export LOG_GROUP="$LOG_GROUP"
EOF

chmod 600 lab07-resources.env
```

Restore in another session:

```bash
source lab07-resources.env

export DB_PASSWORD="$(cat lab07-db-password.txt)"
```

### Step 6 — Check Existing Resources

```bash
aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --region "$AWS_REGION"
```

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

```bash
aws iam get-role \
  --role-name "$ROLE_NAME"
```

Expected: resources do not exist in a fresh lab.

---

## 7. Create the Private VPC

### Step 1 — Create VPC

```bash
export VPC_ID=$(aws ec2 create-vpc \
  --cidr-block "$VPC_CIDR" \
  --tag-specifications \
  "ResourceType=vpc,Tags=[{Key=Name,Value=lambda-lab07-vpc},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'Vpc.VpcId' \
  --output text \
  --region "$AWS_REGION")

echo "$VPC_ID"

echo "export VPC_ID=$VPC_ID" >> lab07-resources.env
```

### Step 2 — Enable DNS Support

```bash
aws ec2 modify-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --enable-dns-support \
  --region "$AWS_REGION"
```

### Step 3 — Enable DNS Hostnames

```bash
aws ec2 modify-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --enable-dns-hostnames \
  --region "$AWS_REGION"
```

### Step 4 — Create Private Subnet A

```bash
export PRIVATE_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block "$PRIVATE_A_CIDR" \
  --availability-zone "$AZ_A" \
  --tag-specifications \
  "ResourceType=subnet,Tags=[{Key=Name,Value=lambda-lab07-private-a},{Key=Project,Value=$PROJECT_TAG}]" \
  --query Subnet.SubnetId \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_SUBNET_A=$PRIVATE_SUBNET_A" >> lab07-resources.env
```

### Step 5 — Create Private Subnet B

```bash
export PRIVATE_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block "$PRIVATE_B_CIDR" \
  --availability-zone "$AZ_B" \
  --tag-specifications \
  "ResourceType=subnet,Tags=[{Key=Name,Value=lambda-lab07-private-b},{Key=Project,Value=$PROJECT_TAG}]" \
  --query Subnet.SubnetId \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_SUBNET_B=$PRIVATE_SUBNET_B" >> lab07-resources.env
```

### Step 6 — Verify Subnets

```bash
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Subnet:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone}' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
10.207.1.0/24 → us-east-1a
10.207.2.0/24 → us-east-1b
```

---

## 8. Configure Private Routing

### Step 1 — Create Route Table

```bash
export PRIVATE_RT_ID=$(aws ec2 create-route-table \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=route-table,Tags=[{Key=Name,Value=lambda-lab07-private-rt},{Key=Project,Value=$PROJECT_TAG}]" \
  --query RouteTable.RouteTableId \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_RT_ID=$PRIVATE_RT_ID" >> lab07-resources.env
```

### Step 2 — Associate Private Subnet A

```bash
export ASSOC_A=$(aws ec2 associate-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --subnet-id "$PRIVATE_SUBNET_A" \
  --query AssociationId \
  --output text \
  --region "$AWS_REGION")

echo "export ASSOC_A=$ASSOC_A" >> lab07-resources.env
```

### Step 3 — Associate Private Subnet B

```bash
export ASSOC_B=$(aws ec2 associate-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --subnet-id "$PRIVATE_SUBNET_B" \
  --query AssociationId \
  --output text \
  --region "$AWS_REGION")

echo "export ASSOC_B=$ASSOC_B" >> lab07-resources.env
```

### Step 4 — Verify Routing

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
10.207.0.0/16 → local
```

Because Lambda and RDS communicate using private VPC networking, no NAT Gateway is needed for the database connection.

---

## 9. Create Security Groups

### Security Group Design

| Group | Purpose |
|---|---|
| Lambda SG | Database client |
| DB SG | PostgreSQL database |
| Wrong SG | Intentional incorrect reference |

### Step 1 — Create Lambda Security Group

```bash
export LAMBDA_SG_ID=$(aws ec2 create-security-group \
  --group-name lambda-lab07-client-sg \
  --description "Lambda PostgreSQL client" \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=security-group,Tags=[{Key=Name,Value=lambda-lab07-client-sg},{Key=Project,Value=$PROJECT_TAG}]" \
  --query GroupId \
  --output text \
  --region "$AWS_REGION")

echo "export LAMBDA_SG_ID=$LAMBDA_SG_ID" >> lab07-resources.env
```

### Step 2 — Create Database Security Group

```bash
export DB_SG_ID=$(aws ec2 create-security-group \
  --group-name lambda-lab07-db-sg \
  --description "RDS PostgreSQL security group" \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=security-group,Tags=[{Key=Name,Value=lambda-lab07-db-sg},{Key=Project,Value=$PROJECT_TAG}]" \
  --query GroupId \
  --output text \
  --region "$AWS_REGION")

echo "export DB_SG_ID=$DB_SG_ID" >> lab07-resources.env
```

### Step 3 — Create Wrong Security Group

```bash
export WRONG_SG_ID=$(aws ec2 create-security-group \
  --group-name lambda-lab07-wrong-sg \
  --description "Intentional incorrect security group" \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=security-group,Tags=[{Key=Name,Value=lambda-lab07-wrong-sg},{Key=Project,Value=$PROJECT_TAG}]" \
  --query GroupId \
  --output text \
  --region "$AWS_REGION")

echo "export WRONG_SG_ID=$WRONG_SG_ID" >> lab07-resources.env
```

### Step 4 — Remove Lambda Default Outbound Access

```bash
aws ec2 revoke-security-group-egress \
  --group-id "$LAMBDA_SG_ID" \
  --ip-permissions \
  '[{"IpProtocol":"-1","IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]' \
  --region "$AWS_REGION"
```

### Step 5 — Allow Lambda Egress to Database

```bash
aws ec2 authorize-security-group-egress \
  --group-id "$LAMBDA_SG_ID" \
  --ip-permissions \
  "[{\"IpProtocol\":\"tcp\",\"FromPort\":5432,\"ToPort\":5432,\"UserIdGroupPairs\":[{\"GroupId\":\"$DB_SG_ID\"}]}]" \
  --region "$AWS_REGION"
```

### Step 6 — Create the Incorrect RDS Inbound Rule

```bash
aws ec2 authorize-security-group-ingress \
  --group-id "$DB_SG_ID" \
  --protocol tcp \
  --port 5432 \
  --source-group "$WRONG_SG_ID" \
  --region "$AWS_REGION"
```

### Step 7 — Verify Security Group Rules

```bash
aws ec2 describe-security-groups \
  --group-ids "$LAMBDA_SG_ID" "$DB_SG_ID" "$WRONG_SG_ID" \
  --query 'SecurityGroups[].{Name:GroupName,ID:GroupId,Ingress:IpPermissions,Egress:IpPermissionsEgress}' \
  --output json \
  --region "$AWS_REGION"
```

### Broken Security Group Configuration

```text
Lambda SG:
  Outbound TCP 5432 → DB SG

Database SG:
  Inbound TCP 5432 ← Wrong SG

Actual Lambda Source:
  Lambda SG
```

The database security group does not authorize the Lambda source.

This is the intentional fault.

---

## 10. Create RDS PostgreSQL

### Step 1 — Create DB Subnet Group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name "$DB_SUBNET_GROUP" \
  --db-subnet-group-description "Private subnet group for Lambda Lab 07" \
  --subnet-ids "$PRIVATE_SUBNET_A" "$PRIVATE_SUBNET_B" \
  --tags "Key=Project,Value=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Verify DB Subnet Group

```bash
aws rds describe-db-subnet-groups \
  --db-subnet-group-name "$DB_SUBNET_GROUP" \
  --query 'DBSubnetGroups[].{Name:DBSubnetGroupName,Vpc:VpcId,Subnets:Subnets[].SubnetIdentifier}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --engine postgres \
  --db-instance-class db.t4g.micro \
  --allocated-storage 20 \
  --storage-type gp3 \
  --master-username "$DB_USER" \
  --master-user-password "$DB_PASSWORD" \
  --db-name "$DB_NAME" \
  --db-subnet-group-name "$DB_SUBNET_GROUP" \
  --vpc-security-group-ids "$DB_SG_ID" \
  --no-publicly-accessible \
  --no-multi-az \
  --storage-encrypted \
  --backup-retention-period 0 \
  --no-deletion-protection \
  --tags "Key=Project,Value=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

This is a disposable lab database. For production, use stronger credential management, backup policies, and TLS verification.

### Step 4 — Wait for RDS Availability

```bash
aws rds wait db-instance-available \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --region "$AWS_REGION"
```

### Step 5 — Retrieve the RDS Endpoint

```bash
export DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text \
  --region "$AWS_REGION")

echo "$DB_HOST"

echo "export DB_HOST=$DB_HOST" >> lab07-resources.env
```

### Step 6 — Verify RDS Configuration

```bash
aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query 'DBInstances[].{Status:DBInstanceStatus,Engine:Engine,Host:Endpoint.Address,Port:Endpoint.Port,Public:PubliclyAccessible,SecurityGroups:VpcSecurityGroups}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Status = available
Engine = postgres
Port = 5432
PubliclyAccessible = false
```

---

## 11. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import logging
import os
import socket

import pg8000.dbapi

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 07 started")

    host = os.environ["DB_HOST"]
    port = int(os.environ.get("DB_PORT", "5432"))
    database = os.environ["DB_NAME"]
    username = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    logger.info("Database connection test started")

    try:
        with socket.create_connection(
            (host, port),
            timeout=4
        ):
            logger.info(
                "TCP connectivity to PostgreSQL succeeded"
            )

    except (socket.timeout, OSError) as exc:
        logger.exception("PostgreSQL TCP connection failed")

        return {
            "statusCode": 503,
            "body": json.dumps({
                "status": "failed",
                "stage": "tcp",
                "error_type": type(exc).__name__
            })
        }

    connection = None

    try:
        connection = pg8000.dbapi.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=4
        )

        cursor = connection.cursor()

        cursor.execute(
            "SELECT current_database(), current_user, 1 + 1"
        )

        result = cursor.fetchone()

        logger.info("PostgreSQL SQL query succeeded")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "database": result[0],
                "username": result[1],
                "calculation": result[2]
            })
        }

    except Exception as exc:
        logger.error(
            "PostgreSQL SQL connection or query failed: %s",
            type(exc).__name__
        )

        return {
            "statusCode": 503,
            "body": json.dumps({
                "status": "failed",
                "stage": "sql",
                "error_type": type(exc).__name__
            })
        }

    finally:
        if connection is not None:
            connection.close()
```

### Step 2 — Understand TCP Diagnostics

```python
socket.create_connection((host, port), timeout=4)
```

This checks whether Lambda can establish a TCP connection to PostgreSQL.

When the security group blocks the connection, the attempt should time out.

### Step 3 — Understand Database Authentication

```python
connection = pg8000.dbapi.connect(
    host=host,
    port=port,
    database=database,
    user=username,
    password=password,
    timeout=4
)
```

This performs the database connection and authentication.

### Step 4 — Understand SQL Verification

```sql
SELECT current_database(), current_user, 1 + 1;
```

Expected values:

```text
Database: labdb
User: labadmin
Calculation: 2
```

### Step 5 — Validate Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 6 — Package the PostgreSQL Driver

```bash
mkdir -p package

python3 -m pip install \
  --target package \
  pg8000
```

```bash
cd package
zip -qr ../function.zip .
cd ..
```

```bash
zip -q function.zip lambda_function.py
```

Verify:

```bash
unzip -l function.zip | head -30
```

For a repeatable production build, pin dependency versions and use an appropriate Lambda-compatible build environment.

### Step 7 — Create Lambda Environment Configuration

```bash
python3 - <<'PY'
import json
import os

configuration = {
    "Variables": {
        "DB_HOST": os.environ["DB_HOST"],
        "DB_PORT": os.environ["DB_PORT"],
        "DB_NAME": os.environ["DB_NAME"],
        "DB_USER": os.environ["DB_USER"],
        "DB_PASSWORD": os.environ["DB_PASSWORD"]
    }
}

with open("lambda-environment.json", "w") as file:
    json.dump(configuration, file, indent=2)

os.chmod("lambda-environment.json", 0o600)

print("Lambda environment configuration created")
PY
```

**Security warning:** The generated environment file contains the database password. Do not publish it. For production use, prefer Secrets Manager.

### Step 8 — Create Test Event

Save as `test-event.json`:

```json
{
  "action": "test-postgresql-connectivity"
}
```

---

## 12. Create the Lambda Execution Role

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
  --description "Lambda RDS troubleshooting Lab 07 execution role" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach VPC Execution Policy

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
```

### Step 4 — Verify Permissions

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaVPCAccessExecutionRole
```

---

## 13. Configure CloudWatch Logs

### Step 1 — Create Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Set Seven-Day Retention

```bash
aws logs put-retention-policy \
  --log-group-name "$LOG_GROUP" \
  --retention-in-days 7 \
  --region "$AWS_REGION"
```

---

## 14. Deploy Lambda with the Broken Networking Configuration

### Step 1 — Deploy Lambda

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
  --vpc-config "SubnetIds=$PRIVATE_SUBNET_A,$PRIVATE_SUBNET_B,SecurityGroupIds=$LAMBDA_SG_ID" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Lambda Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 3 — Verify VPC Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Function:FunctionName,State:State,Runtime:Runtime,Timeout:Timeout,Vpc:VpcConfig}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
State = Active
VPC = Lab VPC
Subnets = Private A, Private B
Security Group = Lambda SG
```

Avoid printing the full environment configuration because it contains the database password.

---

## 15. Fault Injection — Reproduce RDS Connection Timeout

### Step 1 — Invoke Lambda

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --cli-read-timeout 30 \
  --log-type Tail \
  --region "$AWS_REGION" \
  broken-response.json \
  > lab07-broken-invocation.json
```

### Step 2 — Inspect the Response

```bash
python3 -m json.tool broken-response.json
```

Expected structure:

```json
{
  "statusCode": 503,
  "body": "{\"status\": \"failed\", \"stage\": \"tcp\", \"error_type\": \"TimeoutError\"}"
}
```

Actual exception names may vary.

### Step 3 — Verify Failure

```bash
python3 - <<'PY'
import json

with open("lab07-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation

assert response["statusCode"] == 503
assert body["status"] == "failed"
assert body["stage"] == "tcp"

print("SUCCESS: Lambda-to-RDS TCP failure reproduced")
print("Error type:", body["error_type"])
PY
```

### Important Observation

The Lambda function catches the socket error.

Therefore:

```text
Lambda Invoke StatusCode = 200
FunctionError = absent
Application statusCode = 503
```

The Lambda runtime completed the handler, but the application reported failure.

### Broken-State Verification

| Check | Expected |
|---|---|
| Lambda Active | Yes |
| RDS Available | Yes |
| RDS Endpoint | Valid |
| Lambda SG Egress | Allowed |
| DB SG Ingress | Wrong source |
| TCP Connection | Timeout |
| PostgreSQL Authentication | Not reached |
| SQL Query | Not executed |
| Application Response | 503 |

---

## 16. Investigate CloudWatch Logs

### Step 1 — Read Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected messages:

```text
Lambda Lab 07 started
Database connection test started
PostgreSQL TCP connection failed
```

### Step 2 — Search TCP Failure Logs

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"PostgreSQL TCP connection failed"' \
  --query 'events[].{Timestamp:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Save Failure Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --output json \
  --region "$AWS_REGION" \
  > lab07-broken-cloudwatch-evidence.json
```

### CloudWatch Finding

The application begins the database connection test, but the TCP connection cannot be established.

PostgreSQL authentication is not reached.

The next investigation focuses on network reachability rather than SQL credentials.

---

## 17. Investigate AWS Networking

### Step 1 — Verify RDS Availability

```bash
aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query 'DBInstances[].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Port:Endpoint.Port,Public:PubliclyAccessible}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Status = available
Port = 5432
Public = false
```

### Step 2 — Inspect RDS Security Group Association

```bash
aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query 'DBInstances[].VpcSecurityGroups' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Inspect Database Inbound Rules

```bash
aws ec2 describe-security-groups \
  --group-ids "$DB_SG_ID" \
  --query 'SecurityGroups[].IpPermissions' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
TCP 5432
Source: WRONG_SG_ID
```

### Step 4 — Inspect Lambda Security Group Egress

```bash
aws ec2 describe-security-groups \
  --group-ids "$LAMBDA_SG_ID" \
  --query 'SecurityGroups[].IpPermissionsEgress' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
TCP 5432
Destination: DB_SG_ID
```

### Step 5 — Inspect Private Routing

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
10.207.0.0/16 → local
```

### Step 6 — Inspect NACLs

```bash
aws ec2 describe-network-acls \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --output json \
  --region "$AWS_REGION"
```

### Investigation Findings

| Component | Finding |
|---|---|
| Lambda state | Active |
| RDS state | Available |
| VPC | Same |
| Private subnet routing | Correct |
| DNS support | Enabled |
| Lambda egress | PostgreSQL permitted |
| Database ingress | Wrong security group |
| Root cause | RDS inbound SG misconfiguration |

---

## 18. Root Cause Analysis

### Root Cause

The database security group allowed inbound PostgreSQL traffic from the wrong source security group.

The Lambda function used a different security group.

Because the Lambda source did not match the allowed source, the database security group blocked the connection.

### Root Cause Diagram

```text
Lambda Invoked
      |
      v
Python Handler Starts
      |
      v
TCP Connection to RDS:5432
      |
      v
Lambda SG Egress Check
      |
      v
Egress Allowed
      |
      v
RDS SG Ingress Check
      |
      v
Allowed Source = Wrong SG
      |
      v
Actual Source = Lambda SG
      |
      v
No Matching Rule
      |
      v
Connection Blocked
      |
      v
TCP Timeout
      |
      v
Application Returns 503
```

### Five Whys

**Why 1 — Why did Lambda fail?**

The TCP connection to PostgreSQL timed out.

**Why 2 — Why did the TCP connection time out?**

The RDS security group blocked the incoming connection.

**Why 3 — Why did the security group block it?**

The inbound rule referenced the wrong source security group.

**Why 4 — Why didn't correct routing resolve the issue?**

Routing and security group authorization are separate network controls.

**Why 5 — How can the issue be prevented?**

Review security group references, manage infrastructure through Terraform, and run database connectivity tests during deployment.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-007 |
| Affected Services | Lambda and RDS |
| Protocol | TCP |
| Port | 5432 |
| Error | Connection timeout |
| Cause | Incorrect inbound SG reference |
| Routing | Correct |
| Authentication | Not reached |
| Remediation | Allow Lambda SG |
| Code Redeployment | Not required |
| Verification | Successful SQL query |

---

## 19. Remediation — Correct Database Security Group

### Step 1 — Remove Incorrect Rule

```bash
aws ec2 revoke-security-group-ingress \
  --group-id "$DB_SG_ID" \
  --protocol tcp \
  --port 5432 \
  --source-group "$WRONG_SG_ID" \
  --region "$AWS_REGION"
```

### Step 2 — Allow Lambda Security Group

```bash
aws ec2 authorize-security-group-ingress \
  --group-id "$DB_SG_ID" \
  --protocol tcp \
  --port 5432 \
  --source-group "$LAMBDA_SG_ID" \
  --region "$AWS_REGION"
```

### Step 3 — Verify Corrected Inbound Rule

```bash
aws ec2 describe-security-groups \
  --group-ids "$DB_SG_ID" \
  --query 'SecurityGroups[].IpPermissions' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
TCP 5432 ← Lambda SG
```

### Before and After

| Setting | Broken | Recovered |
|---|---|---|
| Lambda SG Egress | DB SG | DB SG |
| DB SG Ingress | Wrong SG | Lambda SG |
| Database Private | Yes | Yes |
| VPC Local Route | Present | Present |
| NAT Gateway | Not used | Not used |
| Source Code | Unchanged | Unchanged |
| TCP Connection | Timeout | Successful |

---

## 20. Verify Successful Recovery

### Step 1 — Invoke Lambda Again

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --invocation-type RequestResponse \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://test-event.json \
  --cli-read-timeout 30 \
  --log-type Tail \
  --region "$AWS_REGION" \
  healthy-response.json \
  > lab07-healthy-invocation.json
```

### Step 2 — Inspect Application Response

```bash
python3 -m json.tool healthy-response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"status\": \"success\", \"database\": \"labdb\", \"username\": \"labadmin\", \"calculation\": 2}"
}
```

### Step 3 — Verify Recovery Programmatically

```bash
python3 - <<'PY'
import json

with open("lab07-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation

assert response["statusCode"] == 200
assert body["status"] == "success"

assert body["database"] == "labdb"
assert body["username"] == "labadmin"
assert body["calculation"] == 2

print("SUCCESS: Lambda RDS connection restored")
print("SUCCESS: PostgreSQL SQL query executed")
PY
```

### Step 4 — Verify CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
Lambda Lab 07 started
Database connection test started
TCP connectivity to PostgreSQL succeeded
PostgreSQL SQL query succeeded
```

### Step 5 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"PostgreSQL SQL query succeeded"' \
  --output json \
  --region "$AWS_REGION" \
  > lab07-recovered-cloudwatch-evidence.json
```

### Recovery Comparison

| Check | Broken | Recovered |
|---|---|---|
| Lambda state | Active | Active |
| RDS state | Available | Available |
| DB SG source | Wrong SG | Lambda SG |
| TCP connection | Timeout | Successful |
| PostgreSQL authentication | Not reached | Successful |
| SQL query | Not executed | Executed |
| Application statusCode | 503 | 200 |
| FunctionError | Absent for handled error | Absent |
| Code redeployment | No | No |

**Recovery is verified when Lambda establishes a PostgreSQL connection, authenticates successfully, and executes the SQL query without errors.**

---

## 21. Production Troubleshooting Best Practices

### Investigation Checklist

1. Identify the failing Lambda function.
2. Verify the AWS Region.
3. Confirm Lambda is Active.
4. Confirm RDS is Available.
5. Inspect the RDS endpoint.
6. Verify the database port.
7. Inspect Lambda VPC configuration.
8. Confirm Lambda and RDS network reachability.
9. Inspect Lambda security group egress.
10. Inspect RDS security group ingress.
11. Verify security group source references.
12. Inspect route tables.
13. Inspect NACL rules.
14. Check database connection errors.
15. Determine whether failure occurs at DNS, TCP, authentication, or SQL.
16. Identify the root cause.
17. Apply targeted remediation.
18. Repeat the original invocation.
19. Verify SQL execution.
20. Document and clean up.

### Common Lambda-to-RDS Failures

| Failure | Possible Cause | Investigation |
|---|---|---|
| DNS lookup fails | Incorrect endpoint or DNS configuration | VPC DNS, RDS endpoint |
| TCP timeout | SG, NACL, or routing issue | Network configuration |
| Connection refused | Wrong port or unavailable listener | Database port and status |
| Authentication rejected | Wrong credentials | Database username/password |
| Database not found | Incorrect DB name | RDS and PostgreSQL configuration |
| Too many connections | High connection concurrency | RDS connection metrics |
| Query takes too long | Slow SQL | Query performance |
| Lambda timeout | Execution exceeds limit | Lambda Duration and logs |
| TLS error | Certificate or SSL configuration | RDS CA and client settings |

### Production Recommendations

- Use private RDS endpoints.
- Restrict PostgreSQL access to required security groups.
- Avoid public inbound database rules.
- Use Secrets Manager for credentials.
- Require and verify TLS for database connections.
- Use application-specific database users.
- Consider RDS Proxy for connection pooling.
- Monitor database connections and CPU.
- Monitor Lambda execution errors.
- Use Terraform for network configuration.
- Run post-deployment connectivity checks.

---

## 22. Cloud Security Considerations

### Private Database Networking

The RDS instance is not publicly accessible.

This reduces direct internet exposure.

### Security Group References

Security group references provide more targeted network authorization than broad CIDR rules when applications communicate within a VPC.

### Database Credentials

The hands-on lab uses a locally generated password and passes it through the Lambda environment configuration.

For production applications, use AWS Secrets Manager and a controlled secret retrieval mechanism.

### Database Encryption

The RDS instance is created with storage encryption enabled.

### TLS

Production database clients should require appropriate TLS settings and verify certificates.

The TCP test in this lab is only a connectivity check, not a TLS verification.

### IAM Least Privilege

The Lambda execution role should contain only the permissions required for application operation and VPC integration.

### Database Least Privilege

Production applications should not normally use the RDS master user.

Create a dedicated user with permissions limited to required database operations.

---

## 23. Resource Cleanup

**Important:** RDS is a billable resource. Delete the database once testing is complete.

Before cleanup, verify that every resource belongs to Lab 07.

### Step 1 — Verify RDS Tags

```bash
aws rds list-tags-for-resource \
  --resource-name "$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --query 'DBInstances[0].DBInstanceArn' \
    --output text \
    --region "$AWS_REGION")" \
  --region "$AWS_REGION"
```

Confirm:

```text
Project = Lambda-Troubleshooting-Lab07
```

### Step 2 — Verify VPC Tags

```bash
aws ec2 describe-vpcs \
  --vpc-ids "$VPC_ID" \
  --query 'Vpcs[].Tags' \
  --region "$AWS_REGION"
```

### Step 3 — Verify Lambda Tags

```bash
aws lambda list-tags \
  --resource "$(aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --query Configuration.FunctionArn \
    --output text \
    --region "$AWS_REGION")" \
  --region "$AWS_REGION"
```

### Step 4 — Delete RDS

```bash
aws rds delete-db-instance \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --skip-final-snapshot \
  --delete-automated-backups \
  --region "$AWS_REGION"
```

This skips the final snapshot because the database contains disposable lab data.

Do not skip production backups without an approved retention and recovery plan.

### Step 5 — Wait for RDS Deletion

```bash
aws rds wait db-instance-deleted \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --region "$AWS_REGION"
```

### Step 6 — Delete Lambda

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 7 — Inspect Remaining Network Interfaces

```bash
aws ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkInterfaces[].{ID:NetworkInterfaceId,Type:InterfaceType,Status:Status,Description:Description}' \
  --output table \
  --region "$AWS_REGION"
```

Lambda may need additional time to release its Hyperplane network interfaces.

Do not manually delete Lambda-managed ENIs.

Keep the execution role until Lambda has completed its network-interface cleanup.

### Step 8 — Delete DB Subnet Group

```bash
aws rds delete-db-subnet-group \
  --db-subnet-group-name "$DB_SUBNET_GROUP" \
  --region "$AWS_REGION"
```

### Step 9 — Remove RDS Inbound Rule

```bash
aws ec2 revoke-security-group-ingress \
  --group-id "$DB_SG_ID" \
  --protocol tcp \
  --port 5432 \
  --source-group "$LAMBDA_SG_ID" \
  --region "$AWS_REGION"
```

### Step 10 — Remove Lambda Outbound Rule

```bash
aws ec2 revoke-security-group-egress \
  --group-id "$LAMBDA_SG_ID" \
  --ip-permissions \
  "[{\"IpProtocol\":\"tcp\",\"FromPort\":5432,\"ToPort\":5432,\"UserIdGroupPairs\":[{\"GroupId\":\"$DB_SG_ID\"}]}]" \
  --region "$AWS_REGION"
```

### Step 11 — Delete Security Groups

After the RDS and Lambda network interfaces have been released:

```bash
aws ec2 delete-security-group \
  --group-id "$DB_SG_ID" \
  --region "$AWS_REGION"
```

```bash
aws ec2 delete-security-group \
  --group-id "$LAMBDA_SG_ID" \
  --region "$AWS_REGION"
```

```bash
aws ec2 delete-security-group \
  --group-id "$WRONG_SG_ID" \
  --region "$AWS_REGION"
```

### Step 12 — Detach IAM Policy

After Lambda ENI cleanup:

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
```

### Step 13 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 14 — Disassociate Route Tables

```bash
aws ec2 disassociate-route-table \
  --association-id "$ASSOC_A" \
  --region "$AWS_REGION"
```

```bash
aws ec2 disassociate-route-table \
  --association-id "$ASSOC_B" \
  --region "$AWS_REGION"
```

### Step 15 — Delete Private Route Table

```bash
aws ec2 delete-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --region "$AWS_REGION"
```

### Step 16 — Delete Private Subnets

```bash
aws ec2 delete-subnet \
  --subnet-id "$PRIVATE_SUBNET_A" \
  --region "$AWS_REGION"
```

```bash
aws ec2 delete-subnet \
  --subnet-id "$PRIVATE_SUBNET_B" \
  --region "$AWS_REGION"
```

### Step 17 — Delete VPC

```bash
aws ec2 delete-vpc \
  --vpc-id "$VPC_ID" \
  --region "$AWS_REGION"
```

### Step 18 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 19 — Remove Local Credentials

After confirming the RDS instance and Lambda function are deleted:

```bash
rm -f lab07-db-password.txt

rm -f lambda-environment.json
```

### Cleanup Verification

| Resource | Expected State |
|---|---|
| RDS PostgreSQL | Deleted |
| RDS DB subnet group | Deleted |
| Lambda function | Deleted |
| Lambda Hyperplane ENIs | Released |
| IAM execution role | Deleted |
| Lambda SG | Deleted |
| RDS SG | Deleted |
| Wrong SG | Deleted |
| Private subnets | Deleted |
| Custom route table | Deleted |
| VPC | Deleted |
| CloudWatch log group | Deleted |
| NAT Gateway | Never created |

---

## 24. Interview Questions and Answers

### Q1. Why can Lambda fail to connect to RDS?

Incorrect security groups, routes, DNS settings, credentials, database availability, or connection limits can cause failures.

### Q2. What caused the failure in this lab?

The RDS security group allowed PostgreSQL traffic from the wrong source security group.

### Q3. What port does PostgreSQL normally use?

TCP port 5432.

### Q4. Does Lambda require a NAT Gateway to access private RDS in the same VPC?

No. The VPC local route allows communication between reachable private addresses.

### Q5. How do you fix an incorrect RDS security group?

Allow inbound PostgreSQL traffic from the Lambda function's actual security group.

### Q6. What is the difference between a TCP timeout and an authentication failure?

A TCP timeout means the connection could not be established. An authentication failure means the database rejected the credentials after network connectivity succeeded.

### Q7. Why use security group references instead of broad CIDR blocks?

They allow rules to reference approved network interfaces associated with a specific security group.

### Q8. What is the purpose of a DB subnet group?

It defines the VPC subnets available for RDS database placement.

### Q9. How do you verify SQL connectivity from Lambda?

Connect using a PostgreSQL driver and execute a query such as:

```sql
SELECT current_database(), current_user, 1 + 1;
```

### Q10. What is Amazon RDS Proxy?

A managed database proxy that can pool connections and help applications manage database connection demand.

### Q11. Does an available RDS instance guarantee connectivity?

No. Security groups, routes, NACLs, DNS, and credentials can still prevent successful connections.

### Q12. Why should RDS normally remain private?

Private networking reduces unnecessary direct internet exposure.

### Q13. What does AWSLambdaVPCAccessExecutionRole provide?

Permissions supporting Lambda VPC network-interface operations and basic CloudWatch logging.

### Q14. Can Lambda return StatusCode 200 while the application fails?

Yes. The Invoke API can succeed while application code returns an error response such as statusCode 503.

### Q15. How would you describe this lab in an interview?

I deployed a Python AWS Lambda function and an RDS PostgreSQL database into private subnets inside the same VPC.

I intentionally configured the database security group to allow PostgreSQL traffic from the wrong security group.

When Lambda attempted to connect, the TCP connection timed out.

I investigated CloudWatch Logs, the RDS endpoint, database availability, VPC routing, Lambda security group egress, and RDS security group ingress.

I identified the incorrect database security group source reference as the root cause.

I removed the incorrect rule and allowed port 5432 from the correct Lambda security group.

I invoked the same Lambda function again and verified a successful PostgreSQL connection and SQL query.

I also confirmed that the database remained private and that no NAT Gateway was required.

Finally, I deleted the temporary database, Lambda function, IAM role, VPC networking resources, and CloudWatch logs.

---

## 25. Repository Structure

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
│
├── 07-lambda-rds-connection-failure/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── test-event.json
│   ├── function.zip
│   ├── package/
│   ├── lab07-resources.env
│   ├── lab07-db-password.txt
│   ├── lambda-environment.json
│   ├── lab07-broken-invocation.json
│   ├── lab07-healthy-invocation.json
│   ├── lab07-broken-cloudwatch-evidence.json
│   ├── lab07-recovered-cloudwatch-evidence.json
│   ├── broken-response.json
│   └── healthy-response.json
│
├── 08-lambda-memory-exhaustion/
├── 09-lambda-event-not-triggering/
├── 10-lambda-dependency-import-error/
├── 11-lambda-concurrency-throttling/
└── 12-lambda-async-retry-dlq-failure/
```

### File Descriptions

| File | Purpose |
|---|---|
| README.md | Complete incident documentation |
| lambda_function.py | PostgreSQL connectivity application |
| lambda-trust-policy.json | Lambda IAM trust policy |
| test-event.json | Lambda invocation payload |
| function.zip | Generated deployment package |
| package/ | PostgreSQL driver and dependencies |
| lab07-resources.env | Local AWS resource identifiers |
| lab07-db-password.txt | Sensitive local database password |
| lambda-environment.json | Sensitive Lambda environment settings |
| lab07-broken-invocation.json | Failed invocation metadata |
| lab07-healthy-invocation.json | Recovered invocation metadata |
| lab07-broken-cloudwatch-evidence.json | Connection failure logs |
| lab07-recovered-cloudwatch-evidence.json | Successful SQL execution logs |
| broken-response.json | Failed application response |
| healthy-response.json | Successful SQL response |

### Recommended Public GitHub Files

Only these files are needed for the public lab:

```text
07-lambda-rds-connection-failure/
├── README.md
├── lambda_function.py
├── lambda-trust-policy.json
└── test-event.json
```

Keep generated dependencies, AWS resource identifiers, database passwords, and execution evidence out of public commits.

### Required Root .gitignore

Before running `git add .`, make sure your root `.gitignore` includes:

```gitignore
# Lambda Lab 07
07-lambda-rds-connection-failure/package/
07-lambda-rds-connection-failure/function.zip
07-lambda-rds-connection-failure/lab07-resources.env
07-lambda-rds-connection-failure/lab07-db-password.txt
07-lambda-rds-connection-failure/lambda-environment.json
07-lambda-rds-connection-failure/lab07-*-invocation.json
07-lambda-rds-connection-failure/lab07-*-evidence.json
07-lambda-rds-connection-failure/*-response.json
```

Ensure these files have not previously been tracked by Git. `.gitignore` does not untrack files that were already committed.

---

## 26. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how an AWS Lambda function can fail to connect to a private RDS database even when both services use the same VPC.

We created a VPC with two private subnets across two Availability Zones.

We deployed a private RDS PostgreSQL instance and a Python Lambda function using the pg8000 database driver.

We intentionally configured the database security group to allow TCP 5432 from the wrong security group.

The Lambda application attempted a TCP connection, which timed out.

We investigated the application response, CloudWatch Logs, RDS configuration, security groups, subnet routing, and NACLs.

The investigation identified the incorrect RDS security group reference as the root cause.

We corrected the inbound rule to allow PostgreSQL traffic from Lambda's actual security group.

After remediation, Lambda successfully connected to PostgreSQL, authenticated, and executed a SQL SELECT query.

Finally, we removed the temporary database and networking resources.

**Key Lesson:** Private connectivity between Lambda and RDS depends on correct security group authorization as well as routing. A connection timeout should be investigated at the network layer before changing database credentials or application code.

### Skills Demonstrated

- AWS Lambda
- Amazon RDS PostgreSQL
- Amazon VPC
- Private subnet architecture
- DB subnet groups
- Security group references
- AWS CLI v2
- Linux Bash
- Python 3.13
- pg8000 PostgreSQL driver
- Python dependency packaging
- TCP connectivity diagnostics
- Database authentication
- SQL query verification
- IAM execution roles
- AWSLambdaVPCAccessExecutionRole
- CloudWatch Logs
- VPC route tables
- Network ACL investigation
- Root cause analysis
- Network remediation
- RDS cost management
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-007 |
| Scenario | Lambda RDS Connection Failure |
| Lambda | lambda-lab07-rds-connection |
| Database | PostgreSQL |
| DB Port | 5432 |
| Initial Configuration | Wrong DB SG source |
| Failure | TCP connection timeout |
| Root Cause | Incorrect SG reference |
| Remediation | Authorize Lambda SG |
| TCP Recovery | Successful |
| Database Authentication | Successful |
| SQL Result | 2 |
| Application Response | 200 |
| Code Redeployment | Not required |
| Cleanup | RDS, Lambda, IAM, VPC, CloudWatch |
| Incident Status | Resolved after recovery verification |

**Key Takeaway:** Production Lambda-to-RDS troubleshooting requires validating each stage of the connection: DNS, VPC routing, security groups, TCP connectivity, database authentication, and SQL execution.

---

## Official AWS Documentation

- [AWS Lambda — Connect to RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [AWS — Connecting Lambda to Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/lambda-rds-connect.html)
- [AWS Lambda — VPC Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
- [Amazon RDS — DB Subnet Groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html)
- [Amazon VPC — Security Group Rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
- [AWS Lambda — Python Deployment Packages](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
- [Amazon RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)
- [Amazon RDS Pricing](https://aws.amazon.com/rds/postgresql/pricing/)