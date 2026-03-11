################################################################################
# ALB Security Group
################################################################################

resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  vpc_id      = var.vpc_id
  description = "Security group for Application Load Balancer"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-alb-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "Allow HTTP from internet"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "Allow HTTPS from internet"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_ecs" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.ecs_services.id
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow traffic to ECS services"
}

################################################################################
# ECS Services Security Group
################################################################################

resource "aws_security_group" "ecs_services" {
  name_prefix = "${var.name_prefix}-ecs-"
  vpc_id      = var.vpc_id
  description = "Security group for ECS Fargate services"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-ecs-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id            = aws_security_group.ecs_services.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow traffic from ALB"
}

# Allow ECS services to communicate with each other
resource "aws_vpc_security_group_ingress_rule" "ecs_internal" {
  security_group_id            = aws_security_group.ecs_services.id
  referenced_security_group_id = aws_security_group.ecs_services.id
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow internal ECS service-to-service traffic"
}

resource "aws_vpc_security_group_egress_rule" "ecs_all_outbound" {
  security_group_id = aws_security_group.ecs_services.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound (NAT Gateway for Bedrock, external APIs)"
}

################################################################################
# OpenSearch Security Group
################################################################################

resource "aws_security_group" "opensearch" {
  name_prefix = "${var.name_prefix}-opensearch-"
  vpc_id      = var.vpc_id
  description = "Security group for OpenSearch domain"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-opensearch-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "opensearch_from_ecs" {
  security_group_id            = aws_security_group.opensearch.id
  referenced_security_group_id = aws_security_group.ecs_services.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "Allow HTTPS from ECS services"
}

resource "aws_vpc_security_group_egress_rule" "opensearch_outbound" {
  security_group_id = aws_security_group.opensearch.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}
