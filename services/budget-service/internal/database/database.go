package database

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

func Open(ctx context.Context, cfg config.DatabaseConfig, logger *slog.Logger) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(cfg.URL), &gorm.Config{
		Logger: gormlogger.Default.LogMode(gormlogger.Warn),
	})
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("unwrap database: %w", err)
	}

	sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
	sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
	sqlDB.SetConnMaxLifetime(cfg.ConnMaxLifetime)

	pingCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	if err := sqlDB.PingContext(pingCtx); err != nil {
		return nil, fmt.Errorf("ping database: %w", err)
	}

	logger.Info("connected to budget database")
	return db, nil
}

func AutoMigrate(db *gorm.DB) error {
	if err := db.AutoMigrate(
		&models.Budget{},
		&models.BudgetCategory{},
		&models.BudgetAlertRule{},
		&models.BudgetHistory{},
	); err != nil {
		return fmt.Errorf("auto migrate budget schema: %w", err)
	}

	return nil
}
