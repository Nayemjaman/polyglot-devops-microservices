package http

import (
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
)

func TestAPIRouteWithoutAuthorizationIsRejected(t *testing.T) {
	cfg := config.Config{
		AppEnv:             "test",
		AuthServiceURL:     "http://auth-service",
		CORSAllowedOrigins: []string{"http://localhost:3000"},
		RateLimitRequests:  100,
		RateLimitWindow:    time.Minute,
	}
	router := NewRouter(cfg, slog.New(slog.NewJSONHandler(os.Stdout, nil)), nil)

	req := httptest.NewRequest(http.MethodGet, "/api/budgets", nil)
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected %d, got %d", http.StatusUnauthorized, resp.Code)
	}
}

func TestHealthRoute(t *testing.T) {
	cfg := config.Config{
		AppEnv:             "test",
		AuthServiceURL:     "http://auth-service",
		CORSAllowedOrigins: []string{"http://localhost:3000"},
		RateLimitRequests:  100,
		RateLimitWindow:    time.Minute,
	}
	router := NewRouter(cfg, slog.New(slog.NewJSONHandler(os.Stdout, nil)), nil)

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, resp.Code)
	}
}
