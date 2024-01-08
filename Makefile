test:
	pytest --stepwise --quiet --no-header --color=yes --code-highlight=yes tests

lint:
	ruff check .

fix:
	ruff check . --fix

type:
	mypy

check:
	ruff check --statistics --exit-zero .
	pytest --stepwise-skip --quiet --no-header --no-summary --color=yes --code-highlight=yes tests
	mypy --no-pretty

blac:
	black --check -t py310 -diff .

build:
	poetry build