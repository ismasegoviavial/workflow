terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.25.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

variable "gcp_project_id" {
  type        = string
  description = "ID del proyecto en Google Cloud Platform"
}

variable "gcp_region" {
  type        = string
  default     = "us-central1"
}

# 1. VPC Red Privada para Zero Public IP en Base de Datos
resource "google_compute_network" "workflow_vpc" {
  name                    = "workflow-platform-vpc"
  auto_create_subnetworks = true
}

# 2. Private Service Access para Cloud SQL
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "cloudsql-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.workflow_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.workflow_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# 3. Cloud SQL Instance (SQL Server 2022 con Private IP)
resource "google_sql_database_instance" "sqlserver_instance" {
  name             = "workflow-sqlserver-db"
  database_version = "SQLSERVER_2022_STANDARD"
  region           = var.gcp_region

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = "db-custom-2-7680" # 2 vCPU, 7.5 GB RAM
    ip_configuration {
      ipv4_enabled    = false # SIN IP PÚBLICA
      private_network = google_compute_network.workflow_vpc.id
    }
    backup_configuration {
      enabled            = true
      point_in_time_recovery_enabled = true # PITR
    }
  }
}

# 4. Google Secret Manager para Credenciales
resource "google_secret_manager_secret" "db_password" {
  secret_id = "workflow-db-password"
  replication {
    auto {}
  }
}

# 5. Service Account para Cloud Run con Principio de Menor Privilegio
resource "google_service_account" "workflow_engine_sa" {
  account_id   = "sa-workflow-engine"
  display_name = "Service Account para Motor de Workflows"
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.workflow_engine_sa.email}"
}
