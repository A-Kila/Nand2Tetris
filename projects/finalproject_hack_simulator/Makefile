install: ## Install requirements
	pip install -r requirements.txt

format: ## Run code formatters
	isort n2t
	black n2t

lint: ## Run code linters
	isort --check n2t 
	black --check n2t
	flake8 n2t
	mypy n2t

test:  ## Run tests with coverage
	pytest --cov
