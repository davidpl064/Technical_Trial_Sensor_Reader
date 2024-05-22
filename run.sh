docker compose -f docker/compose.yaml up -d

# Wait some seconds for containers startup
sleep 2

docker logs --follow  app-sense_reader-1