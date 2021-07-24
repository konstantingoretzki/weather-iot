# Define required providers
terraform {
required_version = ">= 0.14.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "1.43.0"
    }
  }
}

# Create a HAPROXY instance
resource "openstack_compute_instance_v2" "haproxy" {
  name            = "haproxy"
  image_id        = "ebd44144-3569-44d1-89cc-27ca22b89850"
  flavor_id       = "0cea52a5-6297-4793-adde-e2f8ab71c812"
  key_pair        = "SSH"
  security_groups = ["haproxy"]

  network {
    name = "public-belwue"
  }
}

# Create RabbitMQ instances
resource "openstack_compute_instance_v2" "rabbitmq" {
  for_each = toset( ["mq1", "mq2", "mq3"] )
  name            = each.key
  image_id        = "ebd44144-3569-44d1-89cc-27ca22b89850"
  flavor_id       = "0cea52a5-6297-4793-adde-e2f8ab71c812"
  key_pair        = "SSH"
  security_groups = ["rabbitmq"]

  network {
    name = "public-belwue"
  }
}

# Output VM IP addresses
output "haproxy-ip" {
 value = openstack_compute_instance_v2.haproxy.access_ip_v4
}
output "mq1-ip" {
 value = openstack_compute_instance_v2.rabbitmq["mq1"].access_ip_v4
}
output "mq2-ip" {
 value = openstack_compute_instance_v2.rabbitmq["mq2"].access_ip_v4
}
output "mq3-ip" {
 value = openstack_compute_instance_v2.rabbitmq["mq3"].access_ip_v4
}
