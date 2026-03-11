################################################################################
# General
################################################################################

aws_region   = "us-east-1"
environment  = "prod"
project_name = "sa"
owner        = "sa-team"

################################################################################
# Networking
################################################################################

vpc_cidr           = "10.12.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
single_nat_gateway = false  # One NAT per AZ for high availability

################################################################################
# ECS Service Sizing (Prod — full scale)
################################################################################

frontend_desired_count = 2
frontend_cpu           = 512
frontend_memory        = 1024

backend_desired_count = 4
backend_cpu           = 1024
backend_memory        = 2048

agents_desired_count = 4
agents_cpu           = 2048
agents_memory        = 4096

################################################################################
# OpenSearch (Prod — production-grade)
################################################################################

opensearch_instance_type   = "r6g.large.search"
opensearch_instance_count  = 2
opensearch_ebs_volume_size = 100

################################################################################
# Feature Flags
################################################################################

enable_autoscaling         = true
enable_container_insights  = true
enable_deletion_protection = true
log_retention_days         = 90
