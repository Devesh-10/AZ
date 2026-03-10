terraform {
  backend "s3" {
    bucket       = "mia-terraform-state"
    key          = "environments/prod/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
