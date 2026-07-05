.PHONY: install run eval playground lint clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Set up virtual environment and install all dependencies using uv"
	@echo "  make run        - Start the Streamlit dashboard in the virtual environment"
	@echo "  make eval       - Run the local multi-agent evaluation suite"
	@echo "  make playground - Launch the local ADK CLI agent playground"
	@echo "  make lint       - Run code quality and linting checks using ruff"
	@echo "  make clean      - Clean virtual environment and cached Python files"

install:
	@echo "Syncing dependencies and setting up virtual environment..."
	uv sync

run:
	@echo "Launching Streamlit dashboard..."
	uv run streamlit run app/streamlit_app.py

eval:
	@echo "Running local multi-agent evaluation suite..."
	uv run python tests/eval_runner.py

playground:
	@echo "Launching local ADK agent playground..."
	uv run agents-cli playground

lint:
	@echo "Running lint checks..."
	uv run ruff check .

clean:
	@echo "Cleaning up virtual environment and python cache..."
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .ruff_cache
