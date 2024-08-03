docker network create \
    --driver=bridge \
    --gateway=172.20.0.1 \
    --subnet=172.20.0.0/16 \
    proxy

docker network create \
    --driver=bridge \
    --gateway=172.19.0.1 \
    --subnet=172.19.0.0/16 \
    monitoring