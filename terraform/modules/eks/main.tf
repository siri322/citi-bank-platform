# This is a stub for the EKS module.
# In a real project, this would define aws_eks_cluster, aws_eks_node_group, aws_iam_role, etc.

variable "cluster_name" { type = string }
variable "cluster_version" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "environment" { type = string }
variable "node_groups" { type = map(any) }

output "cluster_endpoint" {
  value = "https://dummy-endpoint.eks.amazonaws.com"
}
