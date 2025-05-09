.PHONY: up down analysis-logs rmq-ui

up:
	docker compose up -d rabbitmq detector-rgb analysis_service

down:
	docker compose down

analysis-logs:
	docker compose logs -f analysis_service

rmq-ui:
	open http://localhost:15672  # RabbitMQ management UI (guest/guest)