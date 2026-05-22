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
	CORSAllowedOrigins  []string
	RateLimitRequests   int
	RateLimitWindow     time.Duration
	RunMigrations       bool
	GRPCSharedSecret    string
	RabbitMQURL         string
	RabbitMQExchange    string
	TransactionQueue    string
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
		CORSAllowedOrigins:  getEnvList("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
		RateLimitRequests:   getEnvInt("RATE_LIMIT_REQUESTS", 120),
		RateLimitWindow:     time.Duration(getEnvInt("RATE_LIMIT_WINDOW_SECONDS", 60)) * time.Second,
		RunMigrations:       getEnvBool("RUN_MIGRATIONS", false),
		GRPCSharedSecret:    getEnv("GRPC_SHARED_SECRET", ""),
		RabbitMQURL:         getEnv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/"),
		RabbitMQExchange:    getEnv("RABBITMQ_EXCHANGE", "finance.events"),
		TransactionQueue:    getEnv("BUDGET_TRANSACTION_EVENTS_QUEUE", "budget.transaction.events"),
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

func getEnvBool(key string, fallback bool) bool {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value == "true" || value == "1" || value == "yes"
}

func getEnvList(key string, fallback string) []string {
	raw := getEnv(key, fallback)
	values := []string{}
	current := ""
	for _, char := range raw {
		if char == ',' {
			if current != "" {
				values = append(values, current)
			}
			current = ""
			continue
		}
		if char != ' ' && char != '\t' && char != '\n' {
			current += string(char)
		}
	}
	if current != "" {
		values = append(values, current)
	}
	return values
}
