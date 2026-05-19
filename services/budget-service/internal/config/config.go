package config

import "os"

type Config struct {
	AppEnv         string
	HTTPAddr       string
	AuthServiceURL string
}

func Load() Config {
	return Config{
		AppEnv:         getEnv("APP_ENV", "development"),
		HTTPAddr:       getEnv("HTTP_ADDR", ":8081"),
		AuthServiceURL: getEnv("AUTH_SERVICE_URL", "http://127.0.0.1:8000"),
	}
}

func getEnv(key string, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
