output "session_turns_table_name" {
  description = "Name of the session turns DynamoDB table"
  value       = aws_dynamodb_table.session_turns.name
}

output "session_turns_table_arn" {
  description = "ARN of the session turns DynamoDB table"
  value       = aws_dynamodb_table.session_turns.arn
}

output "chat_sessions_table_name" {
  description = "Name of the chat sessions DynamoDB table"
  value       = aws_dynamodb_table.chat_sessions.name
}

output "chat_sessions_table_arn" {
  description = "ARN of the chat sessions DynamoDB table"
  value       = aws_dynamodb_table.chat_sessions.arn
}
