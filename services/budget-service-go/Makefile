APP_NAME := budget-service
GO ?= $(shell if [ -x .tools/go/bin/go ]; then printf "%s" ".tools/go/bin/go"; else printf "%s" "go"; fi)
GO_ENV := GOCACHE="$(CURDIR)/.cache/go-build" GOMODCACHE="$(CURDIR)/.cache/gomod"

.PHONY: run build test tidy

run:
	$(GO_ENV) "$(GO)" run ./cmd/api

build:
	$(GO_ENV) "$(GO)" build -o ./bin/$(APP_NAME) ./cmd/api

test:
	$(GO_ENV) "$(GO)" test ./...

tidy:
	$(GO_ENV) "$(GO)" mod tidy
