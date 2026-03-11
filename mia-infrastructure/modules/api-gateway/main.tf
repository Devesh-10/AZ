################################################################################
# WebSocket API Gateway
################################################################################

resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${var.name_prefix}-websocket"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = {
    Name = "${var.name_prefix}-websocket-api"
  }
}

################################################################################
# Integration (proxy to backend ECS service via ALB)
################################################################################

resource "aws_apigatewayv2_integration" "backend" {
  api_id             = aws_apigatewayv2_api.websocket.id
  integration_type   = "HTTP_PROXY"
  integration_uri    = "http://${var.backend_alb_dns}:${var.backend_port}/ws"
  integration_method = "POST"
}

################################################################################
# Routes
################################################################################

resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "send_message" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "sendMessage"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

################################################################################
# Stage
################################################################################

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = var.stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      eventType      = "$context.eventType"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      connectionId   = "$context.connectionId"
    })
  }

  tags = {
    Name = "${var.name_prefix}-websocket-stage"
  }
}

################################################################################
# CloudWatch Log Group
################################################################################

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.name_prefix}-websocket"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.name_prefix}-apigw-logs"
  }
}
