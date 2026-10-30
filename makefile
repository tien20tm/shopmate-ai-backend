.PHONY: run infra
run:
	uv run fastapi dev

infra:
	docker-compose -f ./deployment/docker-compose.infra.yaml up -d
