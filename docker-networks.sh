docker network create \
    --driver=bridge \
    --gateway=172.18.0.1 \
    --subnet=172.18.0.0/16 \
    chilflix_backend

docker network create \
    --driver=bridge \
    chilflix_frontend

docker network create \
    --driver=bridge \
    dashboard

docker network create \
    --driver=bridge \
    dns

docker network create \
    --driver=bridge \
    proxy