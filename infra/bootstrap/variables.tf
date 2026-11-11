variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "state_bucket_name" {
  type    = string
  default = ""
}

variable "billing_account_id" {
  type    = string
  default = ""
}

variable "monthly_budget_usd" {
  type    = number
  default = 20
}

variable "budget_notification_emails" {
  type    = set(string)
  default = []
}
