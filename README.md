

## Create external volume to store our data
```
docker volume create db-volume
```
## How to populate data to a DB table
```
DOCKER_BUILDKIT=0 docker-compose run pipeline
```