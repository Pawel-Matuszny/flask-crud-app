resource "google_sql_database_instance" "master" {
  name             = "${var.project}-sql"
  database_version = "POSTGRES_11"


  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = true
      require_ssl = true
      authorized_networks {
        value = "34.118.30.233"
      }
      authorized_networks {
        value = "34.118.109.58"
      }
    }
  }
}

resource "google_sql_ssl_cert" "client_cert" {
  common_name = "client-ssl"
  instance    = google_sql_database_instance.master.name
}