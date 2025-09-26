.PHONY: web worker redis stop-web stop-worker stop-redis

# --- Start targets ---
web:
	uvicorn project.asgi:application --reload --port 8000 & echo $$! > .web.pid
	@echo "Web server started with PID $$(cat .web.pid)"

worker:
	celery -A project worker -l info & echo $$! > .worker.pid
	@echo "Celery worker started with PID $$(cat .worker.pid)"

redis:
	@if [ $$(docker ps -aq -f name=pp-redis) ]; then \
		if [ $$(docker ps -q -f name=pp-redis) ]; then \
			echo "Redis container already running."; \
		else \
			echo "Starting existing Redis container..."; \
			docker start pp-redis; \
		fi \
	else \
		echo "Creating new Redis container..."; \
		docker run -p 6379:6379 --name pp-redis -d redis:7-alpine; \
	fi

# --- Stop targets ---
stop-web:
	@if [ -f .web.pid ]; then \
		echo "Stopping web server..."; \
		kill $$(cat .web.pid) || true; \
		rm -f .web.pid; \
	else \
		echo "No web server PID file found."; \
	fi

stop-worker:
	@if [ -f .worker.pid ]; then \
		echo "Stopping Celery worker..."; \
		kill $$(cat .worker.pid) || true; \
		rm -f .worker.pid; \
	else \
		echo "No worker PID file found."; \
	fi

stop-redis:
	@if [ $$(docker ps -q -f name=pp-redis) ]; then \
		echo "Stopping Redis container..."; \
		docker stop pp-redis; \
	else \
		echo "No running Redis container named pp-redis."; \
	fi

# --- Utility ---
gen-key:
	@python3 -c "import secrets, string; alphabet = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(alphabet) for _ in range(50)))"
