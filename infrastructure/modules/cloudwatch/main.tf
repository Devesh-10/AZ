################################################################################
# ECS Service Log Groups
################################################################################

resource "aws_cloudwatch_log_group" "ecs_services" {
  for_each = toset(var.ecs_service_names)

  name              = "/ecs/${var.name_prefix}/${each.key}"
  retention_in_days = var.log_retention_days

  tags = {
    Name    = "${var.name_prefix}-${each.key}-logs"
    Service = each.key
  }
}

################################################################################
# ALB Access Logs (optional — stored in S3)
################################################################################

resource "aws_cloudwatch_log_group" "alb" {
  name              = "/aws/alb/${var.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.name_prefix}-alb-logs"
  }
}

################################################################################
# CloudWatch Alarms
################################################################################

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  for_each = toset(var.ecs_service_names)

  alarm_name          = "${var.name_prefix}-${each.key}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = "${var.name_prefix}-${each.key}"
  }

  alarm_description = "ECS ${each.key} CPU utilization is above ${var.cpu_alarm_threshold}%"

  tags = {
    Name    = "${var.name_prefix}-${each.key}-cpu-alarm"
    Service = each.key
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  for_each = toset(var.ecs_service_names)

  alarm_name          = "${var.name_prefix}-${each.key}-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = "${var.name_prefix}-${each.key}"
  }

  alarm_description = "ECS ${each.key} memory utilization is above ${var.memory_alarm_threshold}%"

  tags = {
    Name    = "${var.name_prefix}-${each.key}-memory-alarm"
    Service = each.key
  }
}
