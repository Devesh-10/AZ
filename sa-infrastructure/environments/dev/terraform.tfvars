################################################################################
# General
################################################################################

aws_region   = "us-east-1"
environment  = "dev"
project_name = "sa"
owner        = "sa-team"

################################################################################
# Networking
################################################################################

vpc_cidr           = "10.10.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
single_nat_gateway = true

################################################################################
# ECS Service Sizing (Dev — minimal)
################################################################################

# Frontend: 1 task x 0.5 vCPU x 1 GB
frontend_desired_count = 1
frontend_cpu           = 512
frontend_memory        = 1024

# Backend API: 1 task x 1 vCPU x 2 GB
backend_desired_count = 1
backend_cpu           = 1024
backend_memory        = 2048

# LangGraph Agents: 1 task x 2 vCPU x 4 GB
agents_desired_count = 1
agents_cpu           = 2048
agents_memory        = 4096

################################################################################
# OpenSearch (Dev — single node, smaller instance)
################################################################################

opensearch_instance_type   = "t3.small.search"
opensearch_instance_count  = 1
opensearch_ebs_volume_size = 50

################################################################################
# Feature Flags
################################################################################

enable_autoscaling         = false
enable_container_insights  = false
enable_deletion_protection = false
log_retention_days         = 7
