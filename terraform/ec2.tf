data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "k3s_key" {
  key_name_prefix = "${var.project_name}-key"
  public_key      = fileexists("~/.ssh/id_rsa.pub") ? file("~/.ssh/id_rsa.pub") : fileexists("~/.ssh/id_ed25519.pub") ? file("~/.ssh/id_ed25519.pub") : "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKPlaceholderDummyKeyForValidationOnly k3s-lab"
}

resource "aws_instance" "k3s_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.k3s.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.k3s_key.key_name

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true

    tags = {
      Name = "${var.project_name}-root-ebs"
    }
  }

  user_data = file("${path.module}/scripts/cloud-init.yaml")

  tags = {
    Name = "${var.project_name}-ec2"
  }
}
