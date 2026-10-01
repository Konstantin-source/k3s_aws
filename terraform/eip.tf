resource "aws_eip" "k3s_eip" {
  instance = aws_instance.k3s_server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}
