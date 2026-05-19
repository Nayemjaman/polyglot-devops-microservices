package main

import (
	"log/slog"
	"os"

	"github.com/nayem/polyglot-devops-microservices/services/budget-service-go/internal/config"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service-go/internal/transport/http"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg := config.Load()

	router := http.NewRouter(cfg, logger)

	logger.Info("starting budget service", "address", cfg.HTTPAddr)
	if err := router.Run(cfg.HTTPAddr); err != nil {
		logger.Error("budget service stopped", "error", err)
		os.Exit(1)
	}
}
