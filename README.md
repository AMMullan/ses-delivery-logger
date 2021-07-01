# Terraform Module for handling SES Notifications

This Terraform module creates a DynamoDB database to enable you to track SES notifications in order for you to track bounces/complaints and ensure you don't get blacklisted by AWS.

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

## TODO

* Allow KMS

## License

[MIT License](LICENSE)
