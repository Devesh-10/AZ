################################################################################
# General
################################################################################

aws_region   = "us-east-1"
environment  = "preprod"
project_name = "mia"
owner        = "mia-team"

################################################################################
# Networking
################################################################################

vpc_cidr           = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
single_nat_gateway = true

################################################################################
# ECS Service Sizing (Pre-Prod — mirrors prod sizing at lower scale)
################################################################################

# Frontend: 2 tasks x 0.5 vCPU x 1 GB
frontend_desired_count = 2
frontend_cpu           = 512
frontend_memory        = 1024

# Backend API: 2 tasks x 1 vCPU x 2 GB
backend_desired_count = 2
backend_cpu           = 1024
backend_memory        = 2048

# LangGraph Agents: 2 tasks x 2 vCPU x 4 GB
agents_desired_count = 2
agents_cpu           = 2048
agents_memory        = 4096

################################################################################
# OpenSearch (Pre-Prod — 2 nodes for zone awareness testing)
################################################################################

opensearch_instance_type   = "t3.medium.search"
opensearch_instance_count  = 2
opensearch_ebs_volume_size = 100

################################################################################
# Feature Flags
################################################################################

enable_autoscaling         = true
enable_container_insights  = true
enable_deletion_protection = false
log_retention_days         = 30
