install: ## Install requirements
	pip install -r requirements.txt

format: ## Run code formatters
	isort n2t tests
	black n2t tests

lint: ## Run code linters
	isort --check n2t tests
	black --check n2t tests
	flake8 n2t tests
	mypy n2t tests

test:  ## Run tests with coverage
	pytest --cov
