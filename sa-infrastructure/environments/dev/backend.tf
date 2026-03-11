terraform {
  backend "s3" {
    bucket       = "sa-terraform-state"
    key          = "environments/dev/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
