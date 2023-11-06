docker network create \
    --driver=bridge \
    --gateway=172.18.0.1 \
    --subnet=172.18.0.0/16 \
    chilflix_backend

docker network create \
    --driver=bridge \
    --gateway=172.19.0.1 \
    --subnet=172.19.0.0/16 \
    chilflix_frontend

docker network create \
    --driver=bridge \
    --gateway=172.20.0.1 \
    --subnet=172.20.0.0/16 \
    dashboard

docker network create \
    --driver=bridge \
    --gateway=172.21.0.1 \
    --subnet=172.21.0.0/16 \
    dns