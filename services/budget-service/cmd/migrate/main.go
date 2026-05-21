package main

import (
	"context"
	"log/slog"
	"os"

	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/database"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg := config.Load()

	db, err := database.Open(context.Background(), cfg.Database, logger)
	if err != nil {
		logger.Error("failed to connect to budget database", "error", err)
		os.Exit(1)
	}
	sqlDB, err := db.DB()
	if err != nil {
		logger.Error("failed to unwrap budget database", "error", err)
		os.Exit(1)
	}
	defer sqlDB.Close()

	if err := database.AutoMigrate(db); err != nil {
		logger.Error("failed to migrate budget database", "error", err)
		os.Exit(1)
	}
}
