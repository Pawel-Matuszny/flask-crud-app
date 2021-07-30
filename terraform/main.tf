resource "google_compute_network" "vpc" {
  name                    = "${var.project}-vpc2"
  auto_create_subnetworks = "false"
}


resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project}-subnet"
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/16"
}


resource "google_container_cluster" "primary" {
  name               = var.cluster
  location           = "${var.region}-c"
  initial_node_count = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
  resource_usage_export_config {
    enable_network_egress_metering = false
    enable_resource_consumption_metering = true

    bigquery_destination {
      dataset_id = "k8s_monitor"
    }
  }


  node_config {
    machine_type = var.machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]

    labels = {
      app = var.app_name
    }

    tags = ["app", var.app_name]
  }

}

resource "google_container_node_pool" "primary_preemptible_nodes" {
  name       = "${var.project}-node-pool"
  cluster    = google_container_cluster.primary.id
  node_count = 1

  node_config {
    preemptible  = true
    machine_type = "${var.machine_type}"

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
