docker compose -f docker/compose_external_services.yaml down
docker compose -f docker/compose_external_services.yaml up -d
pytest --cov=sensor_reader tests
