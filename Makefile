lab-up:
	docker-compose -f docker-compose.nifi.yaml  -f docker-compose.airflow.yaml up -d

lab-down:
	docker-compose down
