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

No requirements

## Providers

| Name | Version |
|------|---------|
| aws | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| resource\_tags | Tags to apply to all resources | `map(any)` | {} | no |
| iam\_role\_prefix | Lambda IAM Execution Role Prefix - Will have region name appended to it | `string` | SESNotificationHandler | no |
| lambda\_name | Lambda Function Name | `string` | SESNotificationHandler | no |
| sns\_topic\_name | SNS Topic Name | `string` | SESNotificationHandler | no |
| ddb\_tbl\_name | DynamoDB Table Name | `string` | SESNotificationHandler | no |
| logs\_retention | CloudWatch Logs Retention (Days) | `number` | 180 | no |
| point\_in\_time\_recovery\_enabled | Enable Point-In-Time Recovery for DynamoDB | `bool` | false | no |
| retain\_dynamodb\_on\_destroy | Keep DynamoDB Table if destroying the Terraform | `bool` | false | no |

## Outputs

| Name | Description |
|------|-------------|
| sns\_topic\_arn | SNS Topic ARN |

## Note
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

## TODO

* Allow KMS

## License

[MIT License](LICENSE)
