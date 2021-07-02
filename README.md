# Terraform Module for handling SES Notifications

This Terraform module creates a DynamoDB database to enable you to track SES notifications in order for you to track bounces/complaints and ensure you don't get blacklisted by AWS.

## Process Flow
1. SES is configured to use the SNS Topic created (the only manual part of this)
2. SNS sends the message to Lambda
3. Lambda captures information from the SES message and inserts it into DynamoDB

## Usage
```hcl
module "ses_handler" {
  source  = "github.com/AMMullan/ses-notification-handler"
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 0.12.26 |
| aws | >= 3.1.5 |

## Providers

| Name | Version |
|------|---------|
| aws | >= 3.1.5 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| resource\_tags | Tags to apply to all resources | `map(any)` | {} | no |
| iam\_role\_prefix | Lambda IAM Execution Role Prefix - Will have region name appended to it | `string` | SESNotificationHandler | no |
| lambda\_name | Lambda Function Name | `string` | SESNotificationHandler | no |
| sns\_topic\_name | SNS Topic Name | `string` | SESNotificationHandler | no |
| ddb\_tbl\_name | DynamoDB Table Name | `string` | SESNotificationHandler | no |
| ddb\_encrypted | Enable DynamoDB Table Encryption | `bool` | true | no |
| ddb\_billing\_mode | Capacity Billing - PAY_PER_REQUEST or PROVISIONED | `string` | PAY_PER_REQUEST | no |
| ddb\_provisioned\_read | DynamoDB Provisioned Read Capacity Units | `number` | 0 | no |
| ddb\_provisioned\_write | DynamoDB Provisioned Write Capacity Units | `number` | 0 | no |
| logs\_retention | CloudWatch Logs Retention (Days) | `number` | 180 | no |
| point\_in\_time\_recovery\_enabled | Enable Point-In-Time Recovery for DynamoDB | `bool` | false | no |

> If **ddb_billing_mode** is configured with PROVISIONED, then **ddb_provisioned_read** and **ddb_provisioned_write** must be greater than 0 or you will logically get an error.

## Outputs

| Name | Description |
|------|-------------|
| sns\_topic\_arn | SNS Topic ARN |

## Notes
You can also use default tags to tag all resources in your Terraform project, i.e.
```hcl
provider "aws" {
  region = "eu-west-1"

   default_tags {
     tags = {
       Name        = "Provider Tag"
       Environment = "Test"
     }
   }
}
```
DynamoDB:
 * Table is encrypted at rest by default using the AWS Managed KMS Key.
 * The Table will **NOT** be destroyed if the module is removed so you will need to ensure that this table is removed manually should you wish.

## License

[MIT License](LICENSE)
