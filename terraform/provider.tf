provider "google" {
 credentials = file("CREDENTIALS_FILE.json")
 project     = var.project
 zone        = "${var.region}-c"
 region      = var.region
}
