resource "google_compute_network" "main" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = var.subnet_name
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.main.id
  ip_cidr_range = var.subnet_cidr

  secondary_ip_range {
    range_name    = var.pod_range_name
    ip_cidr_range = var.pod_cidr
  }

  secondary_ip_range {
    range_name    = var.service_range_name
    ip_cidr_range = var.service_cidr
  }
}

resource "google_compute_firewall" "internal" {
  name          = format("%s-allow-internal", var.network_name)
  project       = var.project_id
  network       = google_compute_network.main.name
  source_ranges = [var.subnet_cidr, var.pod_cidr, var.service_cidr]

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }
}

resource "google_container_cluster" "main" {
  name                = var.cluster_name
  project             = var.project_id
  location            = var.zone
  network             = google_compute_network.main.name
  subnetwork          = google_compute_subnetwork.main.name
  initial_node_count  = 0
  deletion_protection = false
  networking_mode     = "VPC_NATIVE"
  logging_service     = "none"
  monitoring_service  = "none"

  release_channel {
    channel = var.release_channel
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = var.pod_range_name
    services_secondary_range_name = var.service_range_name
  }

  workload_identity_config {
    workload_pool = format("%s.svc.id.goog", var.project_id)
  }

  dynamic "master_authorized_networks_config" {
    for_each = length(var.master_authorized_networks) == 0 ? [] : [true]

    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks

        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }
}

resource "google_container_node_pool" "main" {
  name       = format("%s-nodes", var.cluster_name)
  project    = var.project_id
  location   = var.zone
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  node_config {
    machine_type    = var.machine_type
    disk_size_gb    = var.node_disk_size_gb
    disk_type       = var.node_disk_type
    image_type      = "COS_CONTAINERD"
    service_account = var.node_service_account_email != "" ? var.node_service_account_email : null
    tags            = [format("%s-node", var.cluster_name)]
    metadata = {
      disable-legacy-endpoints = "true"
    }
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}


