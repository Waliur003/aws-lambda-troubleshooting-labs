# Lab 06 — AWS Lambda No Internet Access in VPC

**AWS Lambda Troubleshooting Labs | Cloud Engineering & Cloud Security Engineering**

## Overview

This lab demonstrates how to investigate and resolve an AWS Lambda internet connectivity failure caused by incorrect Amazon VPC routing.

AWS Lambda functions can be connected to private subnets inside an Amazon VPC to access internal resources, such as private databases and application services.

However, a Lambda function connected to a VPC does not automatically have access to the public internet.

To access public IPv4 services from private subnets, the VPC must provide an appropriate outbound network path.

In this lab, we deploy a Python Lambda function into two private subnets across two Availability Zones.

The application attempts to access a public HTTPS website.

Initially, both private subnets are associated with a route table containing only the local VPC route. There is no NAT Gateway and no default route for internet-bound traffic.

The function starts successfully and can normally resolve the public hostname, but the HTTPS connection fails.

We investigate the Lambda configuration, CloudWatch Logs, DNS resolution, security group rules, network ACLs, subnet associations, and VPC route tables.

After identifying the missing outbound routing as the root cause, we create a public NAT Gateway, allocate an Elastic IP address, and add a default route to the private subnet route table.

We then repeat the original Lambda invocation and verify successful HTTPS connectivity.

Finally, we carefully delete the NAT Gateway, Elastic IP, Lambda function, network interfaces, VPC networking resources, IAM execution role, and CloudWatch log group.

This exercise demonstrates a common production networking incident for Cloud Engineers, DevOps Engineers, and Cloud Security Engineers.

### Troubleshooting Workflow

```text
Create Dedicated VPC
          |
          v
Create Public and Private Subnets
          |
          v
Attach Internet Gateway
          |
          v
Configure Public Route Table
          |
          v
Create Private Route Table
          |
          v
Omit NAT Default Route
          |
          v
Configure Lambda Security Group
          |
          v
Create Lambda VPC Execution Role
          |
          v
Deploy Python Lambda
          |
          v
Invoke HTTPS Connectivity Test
          |
          v
Outbound Connection Fails
          |
          v
Inspect CloudWatch Logs
          |
          v
Check DNS and Security Groups
          |
          v
Investigate Private Route Table
          |
          v
Identify Missing Default Route
          |
          v
Create NAT Gateway and Elastic IP
          |
          v
Add Private Default Route
          |
          v
Invoke Lambda Again
          |
          v
Verify HTTPS Success
          |
          v
Safely Clean Up AWS Resources
```

---

## 1. Lab Information

| Item | Configuration |
|---|---|
| Incident ID | INC-LAMBDA-006 |
| Lab | Lambda No Internet Access in VPC |
| Difficulty | Intermediate |
| Primary Services | AWS Lambda, Amazon VPC |
| Supporting Services | IAM, EC2 Networking, CloudWatch Logs |
| AWS Region | `us-east-1` |
| Operating System | WSL2 Ubuntu |
| Tools | AWS CLI v2, Bash, Python 3 |
| Lambda Runtime | Python 3.13 |
| Lambda Function | `lambda-lab06-no-internet` |
| Execution Role | `lambda-lab06-execution-role` |
| VPC CIDR | `10.206.0.0/16` |
| Public Subnet | `10.206.1.0/24` |
| Private Subnet A | `10.206.2.0/24` |
| Private Subnet B | `10.206.3.0/24` |
| Availability Zones | `us-east-1a`, `us-east-1b` |
| Security Group | `lambda-lab06-sg` |
| Public Route Table | `lambda-lab06-public-rt` |
| Private Route Table | `lambda-lab06-private-rt` |
| Internet Gateway | Dedicated lab IGW |
| Broken NAT Configuration | NAT Gateway absent |
| Recovered NAT Configuration | One public NAT Gateway |
| Elastic IP | Dedicated public IPv4 address |
| HTTP Port | TCP 443 |
| Test Destination | `https://example.com` |
| Function Memory | 128 MB |
| Function Timeout | 15 seconds |
| Client Request Timeout | 6 seconds |
| Broken Application Response | HTTP-style 503 |
| Recovered Application Response | HTTP-style 200 |
| Root Cause | Missing internet route in private subnets |
| Remediation | NAT Gateway and default route |
| Code Redeployment | Not required |
| Cleanup | Lambda, IAM, NAT, EIP, VPC, CloudWatch |

### Lab Objectives

- Understand Lambda networking inside an Amazon VPC.
- Create VPC subnets across two Availability Zones.
- Understand public and private subnet routing.
- Configure an Internet Gateway.
- Configure public and private route tables.
- Understand Lambda Hyperplane network interfaces.
- Configure Lambda security group outbound permissions.
- Create a VPC-enabled Lambda execution role.
- Test DNS resolution inside a private subnet.
- Reproduce outbound HTTPS connectivity failure.
- Analyze CloudWatch network exceptions.
- Diagnose a missing private default route.
- Understand NAT Gateway routing.
- Restore private-subnet internet access.
- Verify successful application execution.
- Understand NAT Gateway cost and availability considerations.
- Safely clean up networking resources.

---

## 2. Production Incident Scenario

### Incident Description

A company operates a Python AWS Lambda function that communicates with an external HTTPS API.

The function originally operated without customer-managed VPC networking.

Later, the infrastructure team connects the function to a VPC so it can access internal application resources.

The function is attached to two private subnets across two Availability Zones.

After the networking change, external HTTPS requests begin failing.

The Lambda function remains Active, its Python handler starts correctly, and the security group permits outbound HTTPS traffic.

However, the application cannot complete its request to the public endpoint.

CloudWatch Logs show that DNS resolution succeeds but the outbound HTTPS request fails after the configured network timeout.

The Cloud Engineering team begins investigating the VPC.

The engineer confirms that an Internet Gateway is attached to the VPC and the public subnet has a route to that gateway.

However, the Lambda function uses private subnets associated with a different route table.

The private route table contains only:

```text
10.206.0.0/16 -> local
```

It does not contain:

```text
0.0.0.0/0 -> NAT Gateway
```

Therefore, traffic destined for external public IPv4 addresses has no suitable route.

The engineer creates a NAT Gateway in the public subnet, associates an Elastic IP, and updates the private route table.

The new path allows the Lambda function to initiate outbound HTTPS connections while its network interfaces remain in private subnets.

The original test then succeeds without any application-code change.

### Incident Symptoms

- Lambda deployment succeeds.
- Lambda function becomes Active.
- Python handler executes.
- VPC subnets are correctly attached.
- DNS resolution normally succeeds.
- Security group permits outbound HTTPS.
- External HTTPS connection fails.
- Application returns a 503 response.
- Private route table lacks an internet default route.
- NAT Gateway is not configured.
- CloudWatch records network connectivity errors.

### Business Impact

This failure can affect:

- Third-party API integrations.
- Payment processing integrations.
- External notification services.
- SaaS API communication.
- Webhook delivery.
- External identity providers.
- Serverless background jobs.
- Application availability.
- Dependent business workflows.

### Objective

Identify the missing outbound network path and restore external HTTPS connectivity without exposing the Lambda function directly to the public internet.

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
+---------------------------------------------------+
|                VPC 10.206.0.0/16                  |
|                                                   |
|  +---------------------------------------------+  |
|  |       Private Subnets — Two AZs              |  |
|  |                                             |  |
|  |  Private A             Private B            |  |
|  |  10.206.2.0/24        10.206.3.0/24          |  |
|  |       |                     |                |  |
|  |       +----------+----------+                |  |
|  |                  |                           |  |
|  |            Lambda Function                  |  |
|  |                  |                           |  |
|  |              HTTPS:443                      |  |
|  +------------------+--------------------------+  |
|                     |                             |
|                     v                             |
|             Private Route Table                   |
|                     |                             |
|             10.206.0.0/16 -> local                 |
|                     |                             |
|               NO DEFAULT ROUTE                    |
|                     |                             |
|                  BLOCKED                          |
|                                                   |
|   Public Subnet                                   |
|   10.206.1.0/24                                   |
|           |                                       |
|    Internet Gateway                               |
|                                                   |
|    No NAT Gateway                                 |
+---------------------------------------------------+
                     |
                     X
                     |
              Public Internet
                     |
              example.com:443
```

### Recovered Architecture

```text
                     AWS CLI
                        |
                        v
                  Lambda Invoke
                        |
                        v
+---------------------------------------------------+
|                VPC 10.206.0.0/16                  |
|                                                   |
|  +---------------------------------------------+  |
|  |          Private Subnets                    |  |
|  |                                             |  |
|  |  AZ A                  AZ B                  |  |
|  |  10.206.2.0/24        10.206.3.0/24          |  |
|  |       |                     |                |  |
|  |       +----------+----------+                |  |
|  |                  |                           |  |
|  |             AWS Lambda                      |  |
|  |                  |                           |  |
|  |             HTTPS Traffic                   |  |
|  +------------------+--------------------------+  |
|                     |                             |
|                     v                             |
|             Private Route Table                   |
|                     |                             |
|           0.0.0.0/0 -> NAT Gateway                |
|                     |                             |
|                     v                             |
|  +---------------------------------------------+  |
|  |         Public Subnet — AZ A                |  |
|  |         10.206.1.0/24                      |  |
|  |                                             |  |
|  |              NAT Gateway                    |  |
|  |                   |                         |  |
|  |               Elastic IP                    |  |
|  |                   |                         |  |
|  |            Public Route Table               |  |
|  |                   |                         |  |
|  |       0.0.0.0/0 -> Internet Gateway          |  |
|  +-------------------+-------------------------+  |
|                      |                            |
+----------------------+----------------------------+
                       |
                       v
                 Public Internet
                       |
                       v
                example.com:443
                       |
                       v
                HTTPS Successful
```

### Architecture Components

| Component | Purpose |
|---|---|
| Amazon VPC | Isolates the lab network |
| Public Subnet | Hosts the public NAT Gateway |
| Private Subnet A | Provides Lambda network access in AZ A |
| Private Subnet B | Provides Lambda network access in AZ B |
| Internet Gateway | Connects public routes to the internet |
| Public NAT Gateway | Provides outbound IPv4 connectivity |
| Elastic IP | Provides a public IPv4 address for NAT |
| Public Route Table | Directs internet traffic to IGW |
| Private Route Table | Directs internet traffic to NAT |
| Security Group | Allows outbound HTTPS |
| Network ACL | Controls subnet-level traffic |
| Lambda Hyperplane ENI | Enables Lambda connectivity through the VPC |
| IAM Execution Role | Grants Lambda network-interface and logging permissions |
| CloudWatch Logs | Records DNS and HTTPS test results |

---

## 4. Understanding Lambda VPC Internet Connectivity

### Why Does Lambda Need a VPC?

A Lambda function is attached to a customer-managed VPC when it must communicate with resources reachable through that VPC, such as:

- Private Amazon RDS databases.
- Internal application services.
- Private IP endpoints.
- VPC endpoints.
- Internal load balancers.

### Does Lambda Have Internet Access by Default?

Ordinary Lambda functions that are not attached to a customer-managed VPC normally have outbound internet access through the Lambda-managed networking environment.

After attaching a function to a customer VPC, its outbound connectivity depends on the VPC's network configuration.

### Does a Public Subnet Automatically Give Lambda Internet Access?

No.

A conventional VPC-connected Lambda function does not automatically receive a public IPv4 address just because a public subnet is selected.

### What Makes a Subnet Public?

A public subnet has a route to an Internet Gateway for the relevant internet-bound traffic.

Example:

```text
0.0.0.0/0 -> Internet Gateway
```

### What Makes a Subnet Private?

A private subnet does not have a direct internet route through an Internet Gateway.

Private subnets can still support outbound internet connections through a NAT Gateway.

### What Is a NAT Gateway?

A NAT Gateway allows resources with private IPv4 addresses to initiate outbound connections to public IPv4 destinations.

A public NAT Gateway uses an Elastic IP address and a public subnet with a route to an Internet Gateway.

### Does a NAT Gateway Allow Unsolicited Internet Connections into Lambda?

No.

The NAT Gateway does not make the Lambda function directly internet-accessible.

The function initiates outbound connections.

### What Is a Route Table?

A route table determines where packets are sent based on destination IP prefixes.

For this lab:

```text
Public:
10.206.0.0/16 -> local
0.0.0.0/0     -> Internet Gateway
```

```text
Private:
10.206.0.0/16 -> local
0.0.0.0/0     -> NAT Gateway
```

### Can DNS Work While HTTPS Fails?

Yes.

The Amazon-provided VPC DNS resolver can resolve public domain names even when a private subnet lacks an outbound route to the public internet.

DNS resolution and internet reachability are separate checks.

### What Is a Lambda Hyperplane ENI?

Lambda uses Hyperplane network interfaces to provide connectivity to customer VPC resources.

These interfaces are associated with configured subnet and security group combinations.

### Why Are Two Private Subnets Used?

Using subnets in different Availability Zones supports multi-AZ network placement.

However, this lab uses only one NAT Gateway, so the outbound internet path is not fully resilient.

### Is One NAT Gateway Production-Ready?

A single NAT Gateway is sufficient for this learning exercise.

For resilient production outbound connectivity, using NAT Gateways in multiple Availability Zones and routing each AZ locally is generally preferable.

### What Is the Difference Between a NAT Gateway and a VPC Endpoint?

A NAT Gateway provides general outbound IPv4 connectivity.

A VPC endpoint provides private connectivity to supported AWS services or endpoint services, reducing or eliminating the need for a general internet route for those destinations.

---

## 5. Prerequisites and Safety

### Requirements

- AWS account.
- AWS CLI v2.
- WSL2 Ubuntu.
- Bash.
- Python 3.
- ZIP and unzip utilities.
- Permission to manage VPC resources.
- Permission to allocate Elastic IPs.
- Permission to create NAT Gateways.
- Permission to manage IAM roles.
- Permission to deploy Lambda functions.
- CloudWatch Logs access.

### Important IAM Permission Groups

The deploying identity requires applicable permissions for:

```text
sts:GetCallerIdentity

ec2:CreateVpc
ec2:ModifyVpcAttribute
ec2:DescribeVpcs
ec2:DescribeVpcAttribute
ec2:CreateSubnet
ec2:DescribeSubnets
ec2:CreateInternetGateway
ec2:AttachInternetGateway
ec2:CreateRouteTable
ec2:CreateRoute
ec2:AssociateRouteTable
ec2:DescribeRouteTables
ec2:CreateSecurityGroup
ec2:AuthorizeSecurityGroupEgress
ec2:RevokeSecurityGroupEgress
ec2:DescribeSecurityGroups
ec2:DescribeNetworkAcls
ec2:DescribeNetworkInterfaces
ec2:AllocateAddress
ec2:CreateNatGateway
ec2:DescribeNatGateways
ec2:DeleteNatGateway
ec2:ReleaseAddress
ec2:DeleteRoute
ec2:DisassociateRouteTable
ec2:DeleteRouteTable
ec2:DeleteSecurityGroup
ec2:DeleteSubnet
ec2:DetachInternetGateway
ec2:DeleteInternetGateway
ec2:DeleteVpc

iam:CreateRole
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
lambda:ListTags
lambda:DeleteFunction

logs:CreateLogGroup
logs:PutRetentionPolicy
logs:DescribeLogGroups
logs:FilterLogEvents
logs:DeleteLogGroup
```

Additional IAM and EC2 permissions may be required by organizational policies and Lambda VPC networking operations.

### Safety Rules

- Create a dedicated lab VPC.
- Never change production route tables.
- Do not reuse shared security groups.
- Verify project tags before cleanup.
- Do not manually delete Lambda-managed ENIs.
- Do not delete the execution role before Lambda releases its ENIs.
- Delete the NAT Gateway when testing is complete.
- Release the Elastic IP after deleting the NAT Gateway.
- Do not commit real account identifiers or network evidence to GitHub.

### Cost Warning

**This lab creates billable resources.**

A NAT Gateway has hourly and data-processing charges. An Elastic IP/public IPv4 address can also generate charges.

The lab uses one NAT Gateway to reduce costs.

Avoid leaving the NAT Gateway deployed after the exercise.

---

## 6. Prepare WSL Ubuntu

### Step 1 — Create Lab Directory

```bash
cd ~/aws-lambda-troubleshooting-labs

mkdir -p 06-lambda-no-internet-vpc

cd 06-lambda-no-internet-vpc
```

### Step 2 — Verify Tools

```bash
aws --version
python3 --version
zip -v

aws sts get-caller-identity
```

Install ZIP if necessary:

```bash
sudo apt update
sudo apt install -y zip unzip
```

### Step 3 — Configure Variables

```bash
export AWS_REGION="us-east-1"
export AWS_PAGER=""

export AZ_A="us-east-1a"
export AZ_B="us-east-1b"

export PROJECT_TAG="Lambda-Troubleshooting-Lab06"

export VPC_CIDR="10.206.0.0/16"
export PUBLIC_CIDR="10.206.1.0/24"
export PRIVATE_A_CIDR="10.206.2.0/24"
export PRIVATE_B_CIDR="10.206.3.0/24"

export FUNCTION_NAME="lambda-lab06-no-internet"

export ROLE_NAME="lambda-lab06-execution-role"

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

export LOG_GROUP="/aws/lambda/${FUNCTION_NAME}"
```

### Step 4 — Save Lab Variables

```bash
cat > lab06-resources.env <<EOF
export AWS_REGION="$AWS_REGION"
export AZ_A="$AZ_A"
export AZ_B="$AZ_B"
export PROJECT_TAG="$PROJECT_TAG"
export FUNCTION_NAME="$FUNCTION_NAME"
export ROLE_NAME="$ROLE_NAME"
export ROLE_ARN="$ROLE_ARN"
export LOG_GROUP="$LOG_GROUP"
EOF
```

Each AWS resource ID will be appended to this file after creation.

Restore in a new terminal using:

```bash
source lab06-resources.env
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

Expected for a fresh lab: both resources do not exist.

---

## 7. Create the VPC

### Step 1 — Create a Dedicated VPC

```bash
export VPC_ID=$(aws ec2 create-vpc \
  --cidr-block "$VPC_CIDR" \
  --tag-specifications \
  "ResourceType=vpc,Tags=[{Key=Name,Value=lambda-lab06-vpc},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'Vpc.VpcId' \
  --output text \
  --region "$AWS_REGION")

echo "$VPC_ID"
```

Save:

```bash
echo "export VPC_ID=$VPC_ID" >> lab06-resources.env
```

### Step 2 — Enable VPC DNS Support

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

### Step 4 — Verify DNS Settings

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsSupport \
  --region "$AWS_REGION"
```

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsHostnames \
  --region "$AWS_REGION"
```

Expected:

```text
Value = true
```

---

## 8. Create Public and Private Subnets

### Step 1 — Create Public Subnet A

```bash
export PUBLIC_SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block "$PUBLIC_CIDR" \
  --availability-zone "$AZ_A" \
  --tag-specifications \
  "ResourceType=subnet,Tags=[{Key=Name,Value=lambda-lab06-public-a},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'Subnet.SubnetId' \
  --output text \
  --region "$AWS_REGION")

echo "export PUBLIC_SUBNET_ID=$PUBLIC_SUBNET_ID" >> lab06-resources.env
```

### Step 2 — Create Private Subnet A

```bash
export PRIVATE_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block "$PRIVATE_A_CIDR" \
  --availability-zone "$AZ_A" \
  --tag-specifications \
  "ResourceType=subnet,Tags=[{Key=Name,Value=lambda-lab06-private-a},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'Subnet.SubnetId' \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_SUBNET_A=$PRIVATE_SUBNET_A" >> lab06-resources.env
```

### Step 3 — Create Private Subnet B

```bash
export PRIVATE_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block "$PRIVATE_B_CIDR" \
  --availability-zone "$AZ_B" \
  --tag-specifications \
  "ResourceType=subnet,Tags=[{Key=Name,Value=lambda-lab06-private-b},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'Subnet.SubnetId' \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_SUBNET_B=$PRIVATE_SUBNET_B" >> lab06-resources.env
```

### Step 4 — Verify Subnets

```bash
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Subnet:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone}' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
Public A     10.206.1.0/24    us-east-1a
Private A    10.206.2.0/24    us-east-1a
Private B    10.206.3.0/24    us-east-1b
```

---

## 9. Create the Internet Gateway and Public Routing

### Step 1 — Create Internet Gateway

```bash
export IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications \
  "ResourceType=internet-gateway,Tags=[{Key=Name,Value=lambda-lab06-igw},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'InternetGateway.InternetGatewayId' \
  --output text \
  --region "$AWS_REGION")

echo "export IGW_ID=$IGW_ID" >> lab06-resources.env
```

### Step 2 — Attach Internet Gateway

```bash
aws ec2 attach-internet-gateway \
  --internet-gateway-id "$IGW_ID" \
  --vpc-id "$VPC_ID" \
  --region "$AWS_REGION"
```

### Step 3 — Create Public Route Table

```bash
export PUBLIC_RT_ID=$(aws ec2 create-route-table \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=route-table,Tags=[{Key=Name,Value=lambda-lab06-public-rt},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'RouteTable.RouteTableId' \
  --output text \
  --region "$AWS_REGION")

echo "export PUBLIC_RT_ID=$PUBLIC_RT_ID" >> lab06-resources.env
```

### Step 4 — Add Internet Route

```bash
aws ec2 create-route \
  --route-table-id "$PUBLIC_RT_ID" \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id "$IGW_ID" \
  --region "$AWS_REGION"
```

### Step 5 — Associate Public Subnet

```bash
export PUBLIC_ASSOC_ID=$(aws ec2 associate-route-table \
  --route-table-id "$PUBLIC_RT_ID" \
  --subnet-id "$PUBLIC_SUBNET_ID" \
  --query AssociationId \
  --output text \
  --region "$AWS_REGION")

echo "export PUBLIC_ASSOC_ID=$PUBLIC_ASSOC_ID" >> lab06-resources.env
```

### Step 6 — Verify Public Route

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PUBLIC_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
10.206.0.0/16 -> local
0.0.0.0/0     -> Internet Gateway
```

---

## 10. Configure the Broken Private Route Table

### Step 1 — Create Private Route Table

```bash
export PRIVATE_RT_ID=$(aws ec2 create-route-table \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=route-table,Tags=[{Key=Name,Value=lambda-lab06-private-rt},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'RouteTable.RouteTableId' \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_RT_ID=$PRIVATE_RT_ID" >> lab06-resources.env
```

### Step 2 — Associate Private Subnet A

```bash
export PRIVATE_ASSOC_A=$(aws ec2 associate-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --subnet-id "$PRIVATE_SUBNET_A" \
  --query AssociationId \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_ASSOC_A=$PRIVATE_ASSOC_A" >> lab06-resources.env
```

### Step 3 — Associate Private Subnet B

```bash
export PRIVATE_ASSOC_B=$(aws ec2 associate-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --subnet-id "$PRIVATE_SUBNET_B" \
  --query AssociationId \
  --output text \
  --region "$AWS_REGION")

echo "export PRIVATE_ASSOC_B=$PRIVATE_ASSOC_B" >> lab06-resources.env
```

### Step 4 — Inspect the Private Routes

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
Destination       Target
10.206.0.0/16     local
```

Notice that no default route exists.

### Broken Configuration

```text
0.0.0.0/0 -> MISSING
```

This missing internet route is the intentional fault.

---

<WritingBlock id="68422" variant="document">## 11. Create the Lambda Security Group

### Step 1 — Create Security Group

```bash
export LAMBDA_SG_ID=$(aws ec2 create-security-group \
  --group-name lambda-lab06-sg \
  --description "Outbound HTTPS for Lambda Lab 06" \
  --vpc-id "$VPC_ID" \
  --tag-specifications \
  "ResourceType=security-group,Tags=[{Key=Name,Value=lambda-lab06-sg},{Key=Project,Value=$PROJECT_TAG}]" \
  --query GroupId \
  --output text \
  --region "$AWS_REGION")

echo "export LAMBDA_SG_ID=$LAMBDA_SG_ID" >> lab06-resources.env
```

### Step 2 — Remove Default Outbound Access

```bash
aws ec2 revoke-security-group-egress \
  --group-id "$LAMBDA_SG_ID" \
  --ip-permissions \
  '[{"IpProtocol":"-1","IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]' \
  --region "$AWS_REGION"
```

### Step 3 — Allow Outbound HTTPS

```bash
aws ec2 authorize-security-group-egress \
  --group-id "$LAMBDA_SG_ID" \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region "$AWS_REGION"
```

### Step 4 — Verify Security Group

```bash
aws ec2 describe-security-groups \
  --group-ids "$LAMBDA_SG_ID" \
  --query 'SecurityGroups[].{Inbound:IpPermissions,Outbound:IpPermissionsEgress}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
Inbound rules: None
Outbound: TCP 443 -> 0.0.0.0/0
```

### Important Observation

The security group allows HTTPS traffic.

However, a security group cannot create a missing network route.

Even with outbound TCP 443 allowed, Lambda cannot reach public IPv4 destinations without appropriate routing.

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

### Step 2 — Create Execution Role

```bash
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Lambda Lab 06 VPC execution role" \
  --tags "Key=Project,Value=$PROJECT_TAG"
```

### Step 3 — Attach VPC Access Policy

```bash
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
```

### Step 4 — Verify Role

```bash
aws iam list-attached-role-policies \
  --role-name "$ROLE_NAME" \
  --output table
```

Expected:

```text
AWSLambdaVPCAccessExecutionRole
```

### Understanding the Policy

`AWSLambdaVPCAccessExecutionRole` includes permissions for basic logging and EC2 network-interface operations required by Lambda VPC integration.

It does not configure NAT routing or automatically provide internet connectivity.

---

## 13. Configure CloudWatch Logs

### Step 1 — Create Log Group

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Set Log Retention

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

Expected:

```text
Retention = 7 days
```

---

## 14. Create the Python Lambda Application

### Step 1 — Create `lambda_function.py`

```python
import json
import logging
import socket
import time
import urllib.error
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TARGET_URL = "https://example.com"


def lambda_handler(event, context):
    logger.info("Lambda Lab 06 started")
    logger.info("Testing outbound HTTPS connectivity")

    hostname = "example.com"

    try:
        ip = socket.gethostbyname(hostname)
        logger.info(
            "DNS resolution succeeded for %s",
            hostname
        )
        logger.info("Resolved IP: %s", ip)

    except socket.gaierror as exc:
        logger.exception("DNS resolution failed")

        return {
            "statusCode": 503,
            "body": json.dumps({
                "network_status": "failed",
                "stage": "dns",
                "error": str(exc)
            })
        }

    start = time.monotonic()

    try:
        with urllib.request.urlopen(
            TARGET_URL,
            timeout=6
        ) as response:
            status = response.status
            response.read(256)

        elapsed = round(
            time.monotonic() - start,
            3
        )

        logger.info(
            "Outbound HTTPS request succeeded"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "network_status": "success",
                "http_status": status,
                "duration_seconds": elapsed
            })
        }

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError
    ) as exc:
        elapsed = round(
            time.monotonic() - start,
            3
        )

        logger.exception(
            "Outbound HTTPS request failed"
        )

        return {
            "statusCode": 503,
            "body": json.dumps({
                "network_status": "failed",
                "stage": "https",
                "error_type": type(exc).__name__,
                "duration_seconds": elapsed
            })
        }
```

### Step 2 — Understand DNS Testing

```python
socket.gethostbyname("example.com")
```

This resolves a hostname to an IPv4 address.

Successful DNS resolution does not prove that an HTTPS connection can reach the resolved address.

### Step 3 — Understand HTTPS Testing

```python
urllib.request.urlopen(
    "https://example.com",
    timeout=6
)
```

This attempts an outbound HTTPS connection using TCP 443.

The six-second client timeout prevents the request from waiting indefinitely.

### Step 4 — Understand Error Handling

The function catches network exceptions and returns a structured application response:

```json
{
  "statusCode": 503,
  "body": "..."
}
```

A handled network failure generally does not create a Lambda `FunctionError`.

The Lambda invocation itself can succeed while the application's response reports a connectivity failure.

### Step 5 — Validate Python Syntax

```bash
python3 - <<'PY'
import ast
from pathlib import Path

ast.parse(Path("lambda_function.py").read_text())

print("SUCCESS: Python syntax valid")
PY
```

### Step 6 — Package the Function

```bash
zip function.zip lambda_function.py
```

Verify:

```bash
unzip -l function.zip
```

### Step 7 — Create Test Event

Save as `test-event.json`:

```json
{
  "test": "outbound-internet-connectivity"
}
```

---

## 15. Deploy Lambda into Private Subnets

### Step 1 — Create Lambda

```bash
aws lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13 \
  --role "$ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 15 \
  --memory-size 128 \
  --architectures x86_64 \
  --vpc-config "SubnetIds=$PRIVATE_SUBNET_A,$PRIVATE_SUBNET_B,SecurityGroupIds=$LAMBDA_SG_ID" \
  --tags "Project=$PROJECT_TAG" \
  --region "$AWS_REGION"
```

### Step 2 — Wait for Activation

```bash
aws lambda wait function-active-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Lambda may remain in Pending while its VPC network interfaces are prepared.

### Step 3 — Inspect VPC Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --query '{Name:FunctionName,State:State,Role:Role,Timeout:Timeout,Vpc:VpcConfig}' \
  --output json \
  --region "$AWS_REGION"
```

Verify:

- Function state is Active.
- VPC ID matches the dedicated lab VPC.
- Both private subnet IDs are configured.
- The Lambda security group is attached.

### Step 4 — Save Broken Configuration

```bash
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --output json \
  --region "$AWS_REGION" \
  > lab06-broken-configuration.json
```

---

## 16. Fault Injection — Reproduce Internet Connectivity Failure

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
  > lab06-broken-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab06-broken-invocation.json
```

Expected relevant field:

```json
{
  "StatusCode": 200
}
```

Because the application catches network errors, `FunctionError` should normally be absent.

### Step 3 — Inspect Application Response

```bash
python3 -m json.tool broken-response.json
```

Expected structure:

```json
{
  "statusCode": 503,
  "body": "{\"network_status\": \"failed\", \"stage\": \"https\", \"error_type\": \"URLError\", \"duration_seconds\": 6.0}"
}
```

The actual exception type and duration may differ.

### Step 4 — Verify the Broken State

```bash
python3 - <<'PY'
import json

with open("lab06-broken-invocation.json") as file:
    invocation = json.load(file)

with open("broken-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation
assert response["statusCode"] == 503
assert body["network_status"] == "failed"

print("Failure stage:", body["stage"])

assert body["stage"] == "https", (
    "Expected HTTPS failure. "
    "Investigate DNS separately if the failure stage differs."
)

print("SUCCESS: Outbound HTTPS failure reproduced")
PY
```

### Step 5 — Interpret the Result

For a successful reproduction of this specific routing problem:

```text
DNS Resolution = Successful
HTTPS Connection = Failed
Application Status = 503
```

If DNS resolution fails instead, investigate DNS configuration before concluding that NAT routing is the cause.

### Broken-State Verification

| Check | Expected |
|---|---|
| Lambda deployed | Yes |
| Function Active | Yes |
| VPC attached | Yes |
| Two private subnets | Yes |
| Security group egress | TCP 443 allowed |
| DNS settings | Enabled |
| NAT Gateway | Missing |
| Private internet route | Missing |
| Outbound HTTPS | Failed |
| Application response | 503 |

---

## 17. Investigate CloudWatch Logs

### Step 1 — Read Recent Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Expected application messages resemble:

```text
Lambda Lab 06 started
Testing outbound HTTPS connectivity
DNS resolution succeeded for example.com
Outbound HTTPS request failed
```

### Step 2 — Search for Connectivity Errors

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Outbound HTTPS request failed"' \
  --query 'events[].{Timestamp:timestamp,Message:message}' \
  --output json \
  --region "$AWS_REGION"
```

### Step 3 — Search DNS Messages

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"DNS resolution succeeded"' \
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
  > lab06-broken-cloudwatch-evidence.json
```

### CloudWatch Findings

The application handler executes and attempts an outbound connection.

The DNS lookup succeeds in the expected test path.

The HTTPS request fails.

This suggests investigating the network path rather than immediately changing the Python code or Lambda runtime configuration.

---

## 18. Investigate VPC Routing

### Step 1 — Inspect Private Route Table

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].{Routes:Routes,Associations:Associations}' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
10.206.0.0/16 -> local
```

Missing:

```text
0.0.0.0/0 -> NAT Gateway
```

### Step 2 — Inspect Private Subnet Associations

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].Associations[].SubnetId' \
  --output table \
  --region "$AWS_REGION"
```

Both private subnet IDs should be present.

### Step 3 — Inspect Public Route Table

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PUBLIC_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
0.0.0.0/0 -> Internet Gateway
```

### Step 4 — Inspect Security Group Egress

```bash
aws ec2 describe-security-groups \
  --group-ids "$LAMBDA_SG_ID" \
  --query 'SecurityGroups[].IpPermissionsEgress' \
  --output json \
  --region "$AWS_REGION"
```

Expected:

```text
TCP 443 -> 0.0.0.0/0
```

### Step 5 — Inspect Network ACLs

```bash
aws ec2 describe-network-acls \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{Acl:NetworkAclId,Entries:Entries}' \
  --output json \
  --region "$AWS_REGION"
```

The default network ACL normally allows inbound and outbound traffic.

### Step 6 — Verify DNS Support

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsSupport \
  --region "$AWS_REGION"
```

Expected:

```text
Value = true
```

### Investigation Findings

| Component | Observation |
|---|---|
| VPC | Correctly configured |
| Lambda VPC attachment | Correct |
| Internet Gateway | Attached |
| Public subnet route | Correct |
| Private subnet associations | Correct |
| Security group outbound | HTTPS allowed |
| Default NACL | Permissive |
| DNS support | Enabled |
| NAT Gateway | Missing |
| Private default route | Missing |
| Root cause | No path to public IPv4 internet |

---

## 19. Root Cause Analysis

### Root Cause

The Lambda function was attached to private subnets that did not have an internet-bound default route.

The private route table contained only the VPC local route.

When the application attempted to connect to a public IP address, the subnet route table did not provide a matching route for the destination.

The request therefore could not reach the public HTTPS service.

The Internet Gateway attached to the VPC did not solve the problem because the private subnets were not configured to use a NAT Gateway.

### Root Cause Diagram

```text
Lambda Function
       |
       v
Private Subnet
       |
       v
Route Table Lookup
       |
       v
Destination: Public IPv4
       |
       v
No 0.0.0.0/0 Route
       |
       v
No Outbound Internet Path
       |
       v
HTTPS Connection Failure
       |
       v
Application Returns 503
```

### Five Whys

**Why 1 — Why did the Lambda function fail?**

The application could not reach the external HTTPS endpoint.

**Why 2 — Why couldn't it connect?**

The private subnets had no route to public IPv4 destinations.

**Why 3 — Why was the route missing?**

No NAT Gateway or private default route had been configured.

**Why 4 — Why didn't the Internet Gateway provide connectivity?**

The Lambda function used private subnets, and no NAT-based outbound path connected those subnets to the Internet Gateway.

**Why 5 — How can the problem be prevented?**

Validate subnet routing, NAT configuration, security group egress, and application connectivity whenever deploying VPC-connected Lambda functions that require external services.

### Root Cause Summary

| Item | Finding |
|---|---|
| Incident | INC-LAMBDA-006 |
| AWS Services | Lambda, VPC |
| Failed Operation | Outbound HTTPS |
| Destination | example.com:443 |
| Failure Category | Network routing |
| DNS | Expected to resolve |
| Security Group | HTTPS permitted |
| Broken Route | Missing 0.0.0.0/0 |
| Missing Component | NAT Gateway |
| Root Cause | No private outbound internet path |
| Remediation | Public NAT and private default route |
| Code Redeployment | Not required |

---

<WritingBlock id="68423" variant="document">## 20. Remediation — Create NAT Gateway and Restore Routing

### Step 1 — Allocate an Elastic IP

```bash
export EIP_ALLOC_ID=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications \
  "ResourceType=elastic-ip,Tags=[{Key=Name,Value=lambda-lab06-nat-eip},{Key=Project,Value=$PROJECT_TAG}]" \
  --query AllocationId \
  --output text \
  --region "$AWS_REGION")

echo "$EIP_ALLOC_ID"

echo "export EIP_ALLOC_ID=$EIP_ALLOC_ID" >> lab06-resources.env
```

### Step 2 — Create the Public NAT Gateway

```bash
export NAT_GW_ID=$(aws ec2 create-nat-gateway \
  --subnet-id "$PUBLIC_SUBNET_ID" \
  --allocation-id "$EIP_ALLOC_ID" \
  --connectivity-type public \
  --tag-specifications \
  "ResourceType=natgateway,Tags=[{Key=Name,Value=lambda-lab06-nat},{Key=Project,Value=$PROJECT_TAG}]" \
  --query 'NatGateway.NatGatewayId' \
  --output text \
  --region "$AWS_REGION")

echo "$NAT_GW_ID"

echo "export NAT_GW_ID=$NAT_GW_ID" >> lab06-resources.env
```

### Step 3 — Wait for NAT Availability

```bash
aws ec2 wait nat-gateway-available \
  --nat-gateway-ids "$NAT_GW_ID" \
  --region "$AWS_REGION"
```

### Step 4 — Verify NAT Gateway

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids "$NAT_GW_ID" \
  --query 'NatGateways[].{Id:NatGatewayId,State:State,Subnet:SubnetId}' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
State = available
```

### Step 5 — Add Private Default Route

```bash
aws ec2 create-route \
  --route-table-id "$PRIVATE_RT_ID" \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id "$NAT_GW_ID" \
  --region "$AWS_REGION"
```

### Step 6 — Verify Private Routing

```bash
aws ec2 describe-route-tables \
  --route-table-ids "$PRIVATE_RT_ID" \
  --query 'RouteTables[].Routes' \
  --output table \
  --region "$AWS_REGION"
```

Expected:

```text
10.206.0.0/16 -> local
0.0.0.0/0     -> NAT Gateway
```

### Step 7 — Understand the Recovered Path

```text
Lambda Function
       |
       v
Private Subnet
       |
       v
0.0.0.0/0 -> NAT Gateway
       |
       v
Public Subnet
       |
       v
NAT Gateway with Elastic IP
       |
       v
0.0.0.0/0 -> Internet Gateway
       |
       v
Public Internet
       |
       v
example.com:443
```

### Remediation Comparison

| Component | Before | After |
|---|---|---|
| Lambda function | Active | Active |
| Private subnets | Two | Two |
| Internet Gateway | Attached | Attached |
| NAT Gateway | Missing | Available |
| Elastic IP | Missing | Allocated |
| Private default route | Missing | NAT Gateway |
| Security group | HTTPS allowed | Unchanged |
| Python code | Unchanged | Unchanged |
| Expected outbound result | Failure | Success |

---

## 21. Verify Successful Recovery

### Step 1 — Invoke the Original Test

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
  > lab06-healthy-invocation.json
```

### Step 2 — Inspect Invocation Metadata

```bash
python3 -m json.tool lab06-healthy-invocation.json
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

Expected structure:

```json
{
  "statusCode": 200,
  "body": "{\"network_status\": \"success\", \"http_status\": 200, \"duration_seconds\": 0.3}"
}
```

The duration shown is illustrative. Actual latency will vary.

### Step 4 — Verify with Python

```bash
python3 - <<'PY'
import json

with open("lab06-healthy-invocation.json") as file:
    invocation = json.load(file)

with open("healthy-response.json") as file:
    response = json.load(file)

body = json.loads(response["body"])

assert invocation["StatusCode"] == 200
assert "FunctionError" not in invocation

assert response["statusCode"] == 200
assert body["network_status"] == "success"
assert body["http_status"] == 200

print("SUCCESS: Lambda internet access restored")
PY
```

Expected:

```text
SUCCESS: Lambda internet access restored
```

### Step 5 — Inspect CloudWatch Logs

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --region "$AWS_REGION"
```

Look for:

```text
DNS resolution succeeded for example.com
Outbound HTTPS request succeeded
```

### Step 6 — Save Recovery Evidence

```bash
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern '"Outbound HTTPS request succeeded"' \
  --output json \
  --region "$AWS_REGION" \
  > lab06-recovered-cloudwatch-evidence.json
```

### Recovery Verification

| Check | Broken | Recovered |
|---|---|---|
| Lambda state | Active | Active |
| DNS resolution | Succeeds | Succeeds |
| Private default route | Missing | Present |
| NAT Gateway | Missing | Available |
| HTTPS connection | Fails | Succeeds |
| Application statusCode | 503 | 200 |
| FunctionError | Absent for handled failure | Absent |
| Code changes | None | None |

**Recovery is confirmed when the original Lambda function successfully connects to the public HTTPS endpoint through the NAT Gateway.**

---

## 22. Production Troubleshooting Best Practices

### Investigation Checklist

1. Verify AWS account and Region.
2. Identify the failing Lambda function.
3. Confirm Lambda state is Active.
4. Inspect the VPC configuration.
5. Identify the configured subnets.
6. Identify the Lambda security group.
7. Reproduce the external connection failure.
8. Review CloudWatch Logs.
9. Separate DNS failures from TCP connectivity failures.
10. Inspect security group outbound rules.
11. Inspect network ACL rules.
12. Identify the route tables associated with each subnet.
13. Inspect the public subnet default route.
14. Inspect the private subnet default route.
15. Verify the Internet Gateway attachment.
16. Verify NAT Gateway existence and availability.
17. Identify the root cause.
18. Apply the appropriate networking remediation.
19. Repeat the original invocation.
20. Confirm successful external connectivity.
21. Document findings.
22. Remove temporary AWS resources.

### Common Lambda VPC Connectivity Problems

| Problem | Symptom | Investigation |
|---|---|---|
| Missing NAT Gateway | External connection timeout | Inspect NAT Gateways |
| Missing private route | Public IP unreachable | Inspect route tables |
| NAT in wrong subnet | Internet connectivity fails | Inspect NAT subnet and public routes |
| Missing Internet Gateway | Public NAT has no internet path | Inspect IGW |
| Security group blocks egress | TCP connection denied or times out | Inspect SG rules |
| NACL blocks return traffic | Connection times out | Inspect ephemeral port rules |
| VPC DNS disabled | Hostname resolution fails | Check DNS attributes |
| Wrong subnet association | Unexpected routing behavior | Inspect subnet route tables |
| Missing VPC permissions | Lambda VPC setup fails | Check execution role |
| Lambda ENI not ready | Function Pending | Inspect Lambda state |
| NAT unavailable | Outbound traffic fails | Inspect NAT state |
| Cross-AZ NAT dependency | Reduced resilience | Review AZ-specific NAT routing |

### Production Recommendations

- Deploy Lambda across multiple Availability Zones when appropriate.
- Prefer an AZ-local NAT Gateway for each private subnet's outbound path in resilient production designs.
- Use VPC endpoints for supported AWS services where appropriate.
- Monitor NAT Gateway availability, traffic, and costs.
- Use application-level HTTP timeouts.
- Avoid broad security group egress when narrower destinations are practical.
- Validate route tables through Infrastructure as Code.
- Consider VPC Flow Logs and Reachability Analyzer for deeper troubleshooting.
- Keep outbound traffic restricted to required destinations.
- Automate network connectivity smoke tests.

---

## 23. Cloud Security Considerations

### Private Subnets

Private subnets reduce direct exposure to public IPv4 networks.

They do not automatically guarantee security.

Network controls, IAM, application security, and monitoring are still necessary.

### Security Groups

The lab allows outbound TCP 443.

Production environments should restrict outbound access according to the application's needs.

### Network ACLs

NACLs are stateless.

When custom NACLs are used, both outbound connections and return traffic must be permitted.

### NAT Gateway

A NAT Gateway supports outbound connectivity but does not provide inbound public access to the Lambda function.

### VPC Endpoints

For supported AWS services, VPC endpoints can provide private connectivity without general public internet access.

### Least-Privilege IAM

The Lambda execution role should grant only the permissions needed to configure VPC access and run the application.

Review managed permissions carefully in production.

### Logging

CloudWatch Logs should capture connectivity failures without exposing credentials or sensitive payloads.

---

## 24. AWS Resource Cleanup

**Cost-sensitive cleanup: remove the NAT Gateway and release the Elastic IP after testing.**

Delete only the resources created for Lab 06.

### Step 1 — Verify Resource Ownership

```bash
aws ec2 describe-vpcs \
  --vpc-ids "$VPC_ID" \
  --query 'Vpcs[].{Id:VpcId,Tags:Tags}' \
  --output json \
  --region "$AWS_REGION"
```

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids "$NAT_GW_ID" \
  --query 'NatGateways[].{Id:NatGatewayId,Tags:Tags}' \
  --output json \
  --region "$AWS_REGION"
```

Confirm the project tag:

```text
Lambda-Troubleshooting-Lab06
```

### Step 2 — Delete Private NAT Route

```bash
aws ec2 delete-route \
  --route-table-id "$PRIVATE_RT_ID" \
  --destination-cidr-block 0.0.0.0/0 \
  --region "$AWS_REGION"
```

### Step 3 — Delete NAT Gateway

```bash
aws ec2 delete-nat-gateway \
  --nat-gateway-id "$NAT_GW_ID" \
  --region "$AWS_REGION"
```

### Step 4 — Wait for NAT Deletion

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids "$NAT_GW_ID" \
  --query 'NatGateways[].State' \
  --output text \
  --region "$AWS_REGION"
```

Repeat the status check until the NAT Gateway is deleted.

### Step 5 — Release Elastic IP

Only after NAT deletion completes:

```bash
aws ec2 release-address \
  --allocation-id "$EIP_ALLOC_ID" \
  --region "$AWS_REGION"
```

### Step 6 — Verify Lambda Ownership

```bash
aws lambda list-tags \
  --resource "$(aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --query Configuration.FunctionArn \
    --output text \
    --region "$AWS_REGION")" \
  --region "$AWS_REGION"
```

Confirm the Lambda project tag.

### Step 7 — Delete Lambda Function

```bash
aws lambda delete-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

### Step 8 — Inspect Hyperplane ENIs

```bash
aws ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkInterfaces[].{Id:NetworkInterfaceId,Type:InterfaceType,Status:Status,Description:Description}' \
  --output table \
  --region "$AWS_REGION"
```

Lambda may take time to release Hyperplane network interfaces after function deletion.

**Do not manually delete Lambda-managed network interfaces.**

Do not delete the execution role while Lambda still needs its permissions to clean up network interfaces.

### Step 9 — Detach IAM Policy

After Lambda-managed ENI cleanup finishes:

```bash
aws iam detach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
```

### Step 10 — Delete IAM Role

```bash
aws iam delete-role \
  --role-name "$ROLE_NAME"
```

### Step 11 — Disassociate Private Route Tables

```bash
aws ec2 disassociate-route-table \
  --association-id "$PRIVATE_ASSOC_A" \
  --region "$AWS_REGION"
```

```bash
aws ec2 disassociate-route-table \
  --association-id "$PRIVATE_ASSOC_B" \
  --region "$AWS_REGION"
```

### Step 12 — Disassociate Public Route Table

```bash
aws ec2 disassociate-route-table \
  --association-id "$PUBLIC_ASSOC_ID" \
  --region "$AWS_REGION"
```

### Step 13 — Delete Custom Route Tables

```bash
aws ec2 delete-route-table \
  --route-table-id "$PRIVATE_RT_ID" \
  --region "$AWS_REGION"
```

```bash
aws ec2 delete-route-table \
  --route-table-id "$PUBLIC_RT_ID" \
  --region "$AWS_REGION"
```

### Step 14 — Delete Security Group

After ENI cleanup:

```bash
aws ec2 delete-security-group \
  --group-id "$LAMBDA_SG_ID" \
  --region "$AWS_REGION"
```

### Step 15 — Delete Private Subnets

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

### Step 16 — Delete Public Subnet

```bash
aws ec2 delete-subnet \
  --subnet-id "$PUBLIC_SUBNET_ID" \
  --region "$AWS_REGION"
```

### Step 17 — Detach Internet Gateway

```bash
aws ec2 detach-internet-gateway \
  --internet-gateway-id "$IGW_ID" \
  --vpc-id "$VPC_ID" \
  --region "$AWS_REGION"
```

### Step 18 — Delete Internet Gateway

```bash
aws ec2 delete-internet-gateway \
  --internet-gateway-id "$IGW_ID" \
  --region "$AWS_REGION"
```

### Step 19 — Delete VPC

```bash
aws ec2 delete-vpc \
  --vpc-id "$VPC_ID" \
  --region "$AWS_REGION"
```

### Step 20 — Delete CloudWatch Log Group

```bash
aws logs delete-log-group \
  --log-group-name "$LOG_GROUP" \
  --region "$AWS_REGION"
```

### Step 21 — Verify Cleanup

Check Lambda:

```bash
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION"
```

Expected:

```text
ResourceNotFoundException
```

Check VPC:

```bash
aws ec2 describe-vpcs \
  --vpc-ids "$VPC_ID" \
  --region "$AWS_REGION"
```

Expected: VPC not found.

Check Elastic IP:

```bash
aws ec2 describe-addresses \
  --allocation-ids "$EIP_ALLOC_ID" \
  --region "$AWS_REGION"
```

Expected: the allocation no longer exists.

Check NAT Gateway:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids "$NAT_GW_ID" \
  --query 'NatGateways[].State' \
  --output text \
  --region "$AWS_REGION"
```

Expected: deleted or no longer returned after AWS removes the deleted record.

### Cleanup Summary

| Resource | Expected State |
|---|---|
| Lambda function | Deleted |
| NAT Gateway | Deleted |
| Elastic IP | Released |
| Lambda Hyperplane ENIs | Released |
| IAM execution role | Deleted |
| Security group | Deleted |
| Public subnet | Deleted |
| Private subnet A | Deleted |
| Private subnet B | Deleted |
| Custom route tables | Deleted |
| Internet Gateway | Deleted |
| VPC | Deleted |
| CloudWatch log group | Deleted |

---

<WritingBlock id="68424" variant="document">## 25. Interview Questions and Answers

### Q1. Why can Lambda lose internet access after being attached to a VPC?

A VPC-connected Lambda function uses the configured VPC networking. If the selected subnets do not have an appropriate route to public destinations, external requests fail.

### Q2. Does a public subnet automatically give Lambda internet access?

No. Conventional VPC-connected Lambda functions do not receive public IPv4 addresses simply by being placed in a public subnet.

### Q3. What is a NAT Gateway?

A managed networking service that allows resources using private IPv4 addresses to initiate outbound connections.

### Q4. Where should a public NAT Gateway be placed?

In a public subnet with an appropriate route to an Internet Gateway.

### Q5. What route should private subnets use for outbound IPv4 traffic?

```text
0.0.0.0/0 -> NAT Gateway
```

### Q6. What route should the public subnet use?

```text
0.0.0.0/0 -> Internet Gateway
```

### Q7. Why can DNS resolution succeed while HTTPS fails?

The VPC resolver may resolve the hostname even though no route exists to reach the resulting public IP address.

### Q8. Can security groups cause internet connectivity failures?

Yes. Incorrect outbound security group rules can block the destination protocol or port.

### Q9. Can network ACLs cause the same failure?

Yes. Custom NACL rules may block outgoing traffic or return traffic.

### Q10. What is AWSLambdaVPCAccessExecutionRole?

An AWS-managed IAM policy providing permissions for Lambda VPC network-interface operations and basic logging.

### Q11. Why might Lambda remain in Pending after VPC configuration?

Lambda may be preparing the Hyperplane network interfaces required for the selected subnets and security groups.

### Q12. Is one NAT Gateway sufficient for production high availability?

Not generally. Deploying NAT Gateways across multiple Availability Zones reduces single-AZ dependencies.

### Q13. How do NAT Gateways differ from VPC endpoints?

NAT Gateways support outbound IPv4 internet connectivity. VPC endpoints provide private access to supported services.

### Q14. Does Lambda need IAM permission to access an ordinary public website?

Not for a basic outbound HTTPS request. Network connectivity and application configuration determine whether that request works.

### Q15. How would you troubleshoot a Lambda timeout when calling an external API?

Inspect CloudWatch Logs, DNS resolution, subnet routes, NAT Gateway state, security group rules, NACLs, and the external service.

### Q16. Can an Internet Gateway alone fix private-subnet connectivity?

No. Private IPv4 resources generally need NAT-based routing for outbound public IPv4 connections.

### Q17. What is a Hyperplane ENI?

A network interface used by Lambda to provide connectivity between Lambda execution environments and resources inside a customer VPC.

### Q18. Why shouldn't you delete the Lambda execution role immediately after deleting the function?

Lambda may still need permissions to clean up its VPC network interfaces.

### Q19. What are two important NAT Gateway cost considerations?

NAT Gateways incur time-based and traffic-processing charges. Public IPv4 addresses can also incur charges.

### Q20. How would you explain this lab in an interview?

I deployed a Python AWS Lambda function into two private subnets across two Availability Zones.

The function attempted to access an external HTTPS website.

I intentionally configured the private route table without an internet default route and did not create a NAT Gateway.

The Lambda function started successfully, and DNS resolution worked, but the outbound HTTPS connection failed.

I investigated the CloudWatch logs, VPC configuration, security group rules, DNS settings, network ACLs, and route tables.

I found that the private subnets did not have a route to public IPv4 destinations.

I created a public NAT Gateway with an Elastic IP and added a default route from the private subnets to the NAT Gateway.

After remediation, I invoked the same Lambda function and verified successful HTTPS connectivity.

I then removed the NAT Gateway, Elastic IP, Lambda function, IAM role, VPC resources, and CloudWatch log group.

---

## 26. Repository Structure

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
│
├── 06-lambda-no-internet-vpc/
│   ├── README.md
│   ├── lambda_function.py
│   ├── lambda-trust-policy.json
│   ├── test-event.json
│   ├── function.zip
│   ├── lab06-resources.env
│   ├── lab06-broken-configuration.json
│   ├── lab06-broken-invocation.json
│   ├── lab06-broken-cloudwatch-evidence.json
│   ├── lab06-healthy-invocation.json
│   ├── lab06-recovered-cloudwatch-evidence.json
│   ├── broken-response.json
│   └── healthy-response.json
│
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
| README.md | Complete production incident documentation |
| lambda_function.py | Python network connectivity application |
| lambda-trust-policy.json | Lambda execution role trust policy |
| test-event.json | Lambda connectivity test payload |
| function.zip | Generated deployment package |
| lab06-resources.env | Local AWS resource identifiers |
| lab06-broken-configuration.json | Lambda VPC configuration evidence |
| lab06-broken-invocation.json | Failed connectivity invocation metadata |
| lab06-broken-cloudwatch-evidence.json | Network failure logs |
| lab06-healthy-invocation.json | Recovered invocation metadata |
| lab06-recovered-cloudwatch-evidence.json | Successful connectivity logs |
| broken-response.json | Failed connectivity response |
| healthy-response.json | Successful HTTPS response |

### Recommended GitHub Files

Publish:

```text
README.md
lambda_function.py
lambda-trust-policy.json
test-event.json
```

Keep generated AWS account data, deployment archives, invocation outputs, and raw CloudWatch evidence local unless reviewed and sanitized.

### Recommended Root .gitignore

Before using `git add .`, ensure the root `.gitignore` contains:

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Generated deployment archives
*.zip

# Local Lambda Lab 06 resources
**/lab06-resources.env

# Configuration evidence
**/lab06-*-configuration.json

# Invocation evidence
**/lab06-*-invocation.json

# CloudWatch evidence
**/lab06-*-evidence.json

# Lambda Lab 06 responses
06-lambda-no-internet-vpc/broken-response.json
06-lambda-no-internet-vpc/healthy-response.json

# Credentials and secrets
.env
.env.*
*.pem
*.key
```

---

## 27. Lessons Learned and Skills Demonstrated

### Lessons Learned

This lab demonstrates how VPC routing can prevent AWS Lambda functions from accessing public internet services.

We created a dedicated VPC with one public subnet and two private subnets across two Availability Zones.

We configured an Internet Gateway and public routing but intentionally omitted the NAT Gateway and private default route.

We deployed a Python Lambda function into the private subnets and attempted to connect to an external HTTPS endpoint.

The function started successfully but could not complete its external request.

We investigated the application response, CloudWatch Logs, Lambda networking configuration, DNS, security groups, NACLs, and subnet route tables.

The root cause was the absence of a route from the private subnets to public IPv4 destinations.

We created a public NAT Gateway, allocated an Elastic IP, and configured the private route table to forward internet-bound traffic through NAT.

After remediation, the same Lambda function successfully connected to the external HTTPS endpoint without code changes.

Finally, we removed the temporary networking resources to prevent ongoing AWS charges.

**Key Lesson:** A VPC-connected Lambda function requires correct subnet routing for external connectivity. Security group outbound permissions alone are not sufficient.

### Skills Demonstrated

- AWS Lambda
- Amazon VPC
- Public and private subnet architecture
- Multi-AZ networking
- Internet Gateway
- NAT Gateway
- Elastic IP
- Route tables
- Subnet associations
- Security groups
- Network ACLs
- DNS troubleshooting
- HTTPS connectivity testing
- Python 3.13
- urllib
- Linux Bash
- AWS CLI v2
- IAM execution roles
- AWSLambdaVPCAccessExecutionRole
- Lambda Hyperplane ENIs
- CloudWatch Logs
- Network root cause analysis
- Connectivity remediation
- AWS cost awareness
- AWS resource cleanup

### Final Outcome

| Item | Expected Result |
|---|---|
| Incident | INC-LAMBDA-006 |
| Scenario | Lambda No Internet Access in VPC |
| Function | lambda-lab06-no-internet |
| VPC CIDR | 10.206.0.0/16 |
| Private Subnets | Two |
| Availability Zones | Two |
| Broken Condition | Missing NAT and default route |
| Root Cause | No outbound internet routing |
| Remediation | Public NAT Gateway and private default route |
| Recovery | Successful outbound HTTPS |
| Application Response | 200 |
| Source Code Changes | None |
| Cleanup | All temporary resources deleted |
| Incident Status | Resolved after verification |

**Key Takeaway:** Troubleshooting Lambda connectivity requires examining the complete network path: Lambda VPC configuration, subnets, route tables, gateways, security groups, DNS, and the external destination.

---

## Official AWS Documentation

- [AWS Lambda — Internet Access for VPC-Connected Functions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html)
- [AWS Lambda — VPC Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
- [AWS Lambda — Troubleshoot Networking](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-networking.html)
- [Amazon VPC — NAT Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [Amazon VPC — Route Tables](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html)
- [Amazon VPC — Internet Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
- [AWS Lambda — Execution Roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [Amazon VPC Pricing](https://aws.amazon.com/vpc/pricing/)