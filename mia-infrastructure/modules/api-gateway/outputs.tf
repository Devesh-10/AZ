output "websocket_api_id" {
  description = "ID of the WebSocket API"
  value       = aws_apigatewayv2_api.websocket.id
}

output "websocket_api_endpoint" {
  description = "WebSocket API endpoint URL"
  value       = aws_apigatewayv2_api.websocket.api_endpoint
}

output "websocket_stage_invoke_url" {
  description = "WebSocket stage invoke URL"
  value       = aws_apigatewayv2_stage.this.invoke_url
}
