.PHONY: web worker redis

web:
	uvicorn project.asgi:application --reload --port 8000

worker:
	celery -A project worker -l info

redis:
	@if [ $$(docker ps -aq -f name=pp-redis) ]; then \
		echo "Starting existing Redis container..."; \
		docker start pp-redis; \
	else \
		echo "Creating new Redis container..."; \
		docker run -p 6379:6379 --name pp-redis -d redis:7-alpine; \
	fi
