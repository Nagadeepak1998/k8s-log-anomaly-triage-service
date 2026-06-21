variable "aws_region" {
  type        = string
  description = "AWS region for the ECR and CloudWatch skeleton."
  default     = "us-west-2"
}

variable "repository_name" {
  type        = string
  description = "ECR repository name."
  default     = "k8s-log-anomaly-triage-service"
}

variable "service_name" {
  type        = string
  description = "Logical service name for logging resources."
  default     = "k8s-log-anomaly-triage-service"
}
