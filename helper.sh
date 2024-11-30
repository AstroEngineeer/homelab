docker network create \
    --driver=bridge \
    --gateway=172.18.0.1 \
    --subnet=172.18.0.0/16 \
    tk-proxy

docker network create \
    --driver=bridge \
    --gateway=172.19.0.1 \
    --subnet=172.19.0.0/16 \
    ts-proxy