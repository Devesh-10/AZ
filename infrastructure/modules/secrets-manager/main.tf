resource "aws_secretsmanager_secret" "this" {
  for_each = toset(var.secret_names)

  name                    = "${var.name_prefix}/${each.key}"
  description             = "Secret for ${each.key}"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Name = "${var.name_prefix}-${each.key}"
  }
}

# Placeholder values — to be updated manually or via CI/CD
resource "aws_secretsmanager_secret_version" "this" {
  for_each = aws_secretsmanager_secret.this

  secret_id     = each.value.id
  secret_string = jsonencode({ "placeholder" = "UPDATE_ME" })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
