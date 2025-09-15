.PHONY: setup
setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: run-scheduler
run-scheduler:
	. venv/bin/activate && uvicorn services.scheduler.api:app --reload --port 8081

.PHONY: run-bot
run-bot:
	. venv/bin/activate && python services/bot/bot.py
