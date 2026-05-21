package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	AppEnv              string
	HTTPAddr            string
	AuthServiceURL      string
	TransactionGRPCAddr string
	BudgetGRPCAddr      string
	Database            DatabaseConfig
}

type DatabaseConfig struct {
	URL             string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
}

func Load() Config {
	return Config{
		AppEnv:              getEnv("APP_ENV", "development"),
		HTTPAddr:            getEnv("HTTP_ADDR", ":8081"),
		AuthServiceURL:      getEnv("AUTH_SERVICE_URL", "http://127.0.0.1:8000"),
		TransactionGRPCAddr: getEnv("TRANSACTION_GRPC_ADDR", "127.0.0.1:50052"),
		BudgetGRPCAddr:      getEnv("BUDGET_GRPC_ADDR", ":50051"),
		Database: DatabaseConfig{
			URL:             getEnv("DATABASE_URL", "postgres://budget_service_user:budget_service_password@127.0.0.1:6433/budget_service_db?sslmode=disable"),
			MaxOpenConns:    getEnvInt("DATABASE_MAX_OPEN_CONNS", 10),
			MaxIdleConns:    getEnvInt("DATABASE_MAX_IDLE_CONNS", 5),
			ConnMaxLifetime: time.Duration(getEnvInt("DATABASE_CONN_MAX_LIFETIME_SECONDS", 300)) * time.Second,
		},
	}
}

func getEnv(key string, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}

func getEnvInt(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}

	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return parsed
}
