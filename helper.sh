#!/bin/bash

# Function to create a Docker network
create_network() {
  local name=$1
  local driver=$2
  local gateway=$3
  local subnet=$4

  echo "Creating network: $name"
  docker network create \
    --driver="$driver" \
    --gateway="$gateway" \
    --subnet="$subnet" \
    "$name"

  if [ $? -eq 0 ]; then
    echo "Network $name created successfully."
  else
    echo "Failed to create network $name."
  fi
}

# Create tk-proxy network
create_network "tk-proxy" "bridge" "172.18.0.1" "172.18.0.0/16"

# Create ts-proxy network
create_network "ts-proxy" "bridge" "172.19.0.1" "172.19.0.0/16"

# List all Docker networks
echo -e "\nListing all Docker networks:"
docker network ls