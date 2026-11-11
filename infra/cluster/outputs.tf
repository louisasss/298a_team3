output "cluster_name" { value = google_container_cluster.main.name }
output "cluster_location" { value = google_container_cluster.main.location }
output "network_name" { value = google_compute_network.main.name }
output "node_pool_name" { value = google_container_node_pool.main.name }
