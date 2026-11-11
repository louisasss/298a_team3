locals {
  services = toset([
    "billingbudgets.googleapis.com",
    "cloudbilling.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "monitoring.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
  ])
  bucket_name = var.state_bucket_name != "" ? var.state_bucket_name : format("%s-tfstate-%s", var.project_id, random_id.bucket.hex)
}

resource "google_project_service" "required" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "random_id" "bucket" {
  byte_length = 4
}

resource "google_storage_bucket" "state" {
  name                        = local.bucket_name
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.required]
}

resource "google_service_account" "terraform" {
  account_id   = "d298a-terraform"
  display_name = "D298A Terraform deployment identity"
  project      = var.project_id
}

resource "google_service_account" "gke_nodes" {
  account_id   = "d298a-gke-nodes"
  display_name = "D298A GKE node identity"
  project      = var.project_id
}

resource "google_project_iam_member" "terraform_roles" {
  for_each = toset([
    "roles/compute.networkAdmin",
    "roles/container.admin",
    "roles/iam.serviceAccountUser",
    "roles/serviceusage.serviceUsageAdmin",
  ])
  project = var.project_id
  role    = each.value
  member  = format("serviceAccount:%s", google_service_account.terraform.email)
}

resource "google_project_iam_member" "node_roles" {
  for_each = toset([
    "roles/container.defaultNodeServiceAccount",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = format("serviceAccount:%s", google_service_account.gke_nodes.email)
}

resource "google_storage_bucket_iam_member" "terraform_state" {
  bucket = google_storage_bucket.state.name
  role   = "roles/storage.objectAdmin"
  member = format("serviceAccount:%s", google_service_account.terraform.email)
}

resource "google_monitoring_notification_channel" "budget_email" {
  for_each     = var.budget_notification_emails
  project      = var.project_id
  display_name = format("D298A budget - %s", each.value)
  type         = "email"
  labels = {
    email_address = each.value
  }
}

resource "google_billing_budget" "project" {
  count           = var.billing_account_id == "" ? 0 : 1
  billing_account = format("billingAccounts/%s", var.billing_account_id)
  display_name    = "D298A project monthly budget"

  budget_filter {
    projects = [format("projects/%s", var.project_id)]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  threshold_rules {
    threshold_percent = 0.25
  }

  threshold_rules {
    threshold_percent = 0.50
  }

  threshold_rules {
    threshold_percent = 0.75
  }

  threshold_rules {
    threshold_percent = 1.00
  }

  all_updates_rule {
    disable_default_iam_recipients = true
    monitoring_notification_channels = [
      for channel in google_monitoring_notification_channel.budget_email : channel.id
    ]
  }

  depends_on = [google_project_service.required]
}





