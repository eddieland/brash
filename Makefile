.DEFAULT_GOAL := help

.PHONY: help all check fmt lint test

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  \033[36m%-6s\033[0m %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)

all: fmt check ## Everything to run before committing: fmt, then check

check: lint test ## Verify without modifying files: lint, then test (what CI runs)

# brash goes first, on its own code: ruff then sorts an import a codemod added and formats what it wrote.
fmt: ## Run the formatters: brash, ruff (imports, trailing commas, format), rumdl
	uv run brash .
	uv run ruff check --select I,COM812 --fix .
	uv run ruff format .
	uv run rumdl fmt .

# brash --check prints the diff a codemod would make and fails on one; `make fmt` applies it.
# zizmor runs offline, so the lint needs no GitHub token and gives the same answer on every machine.
lint: ## Lint and type check: ruff, brash, pyrefly, rumdl, actionlint, zizmor
	uv run ruff format --check .
	uv run ruff check .
	uv run brash --check .
	uv run pyrefly check
	uv run rumdl check .
	uv run actionlint
	uv run zizmor --offline --quiet .

test: ## Run the tests
	uv run pytest -q
