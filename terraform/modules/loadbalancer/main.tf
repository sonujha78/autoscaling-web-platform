resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb"
    Environment = var.environment
  }
}

# Blue target group
resource "aws_lb_target_group" "blue" {
  name     = "asp-${var.environment}-tg-blue"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 15
    timeout             = 5
    matcher             = "200"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg-blue"
    Environment = var.environment
    Slot        = "blue"
  }
}

# Green target group (used during blue-green deploys)
resource "aws_lb_target_group" "green" {
  name     = "asp-${var.environment}-tg-green"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 15
    timeout             = 5
    matcher             = "200"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg-green"
    Environment = var.environment
    Slot        = "green"
  }
}

# Listener starts pointed at blue - orchestrator shifts weights via boto3 during deploys
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port               = 80
  protocol           = "HTTP"

  default_action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.blue.arn
        weight = 100
      }
      target_group {
        arn    = aws_lb_target_group.green.arn
        weight = 0
      }
    }
  }
}
