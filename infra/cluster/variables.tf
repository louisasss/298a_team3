variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "cluster_name" {
  type    = string
  default = "d298a-dev"
}

variable "network_name" {
  type    = string
  default = "d298a-dev-vpc"
}

variable "subnet_name" {
  type    = string
  default = "d298a-dev-subnet"
}

variable "subnet_cidr" {
  type    = string
  default = "10.10.0.0/20"
}

variable "pod_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "service_cidr" {
  type    = string
  default = "10.30.0.0/20"
}

variable "pod_range_name" {
  type    = string
  default = "d298a-pods"
}

variable "service_range_name" {
  type    = string
  default = "d298a-services"
}

variable "machine_type" {
  type    = string
  default = "e2-standard-2"
}

variable "node_count" {
  type    = number
  default = 1
}

variable "node_disk_size_gb" {
  type    = number
  default = 30
}

variable "node_disk_type" {
  type    = string
  default = "pd-standard"
}

variable "node_service_account_email" {
  type    = string
  default = ""
}

variable "release_channel" {
  type    = string
  default = "REGULAR"
}

variable "master_authorized_networks" {
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

