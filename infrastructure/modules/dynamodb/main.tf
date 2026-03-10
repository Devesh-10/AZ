################################################################################
# Session Turns Table
################################################################################

resource "aws_dynamodb_table" "session_turns" {
  name         = "${var.name_prefix}-mia-session-turns"
  billing_mode = var.billing_mode
  hash_key     = "session_id"
  range_key    = "turn_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "turn_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-mia-session-turns"
  }
}

################################################################################
# Chat Sessions Table
################################################################################

resource "aws_dynamodb_table" "chat_sessions" {
  name         = "${var.name_prefix}-mia-chat-sessions"
  billing_mode = var.billing_mode
  hash_key     = "user_id"
  range_key    = "session_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-mia-chat-sessions"
  }
}
