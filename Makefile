run_pipeline:
	DOCKER_BUILDKIT=0 docker-compose build pipeline
	DOCKER_BUILDKIT=0 docker-compose run -d pipeline