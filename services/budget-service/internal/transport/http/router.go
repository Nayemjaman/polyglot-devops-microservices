package http

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
)

type authUserResponse struct {
	User struct {
		FirstName string `json:"first_name"`
		LastName  string `json:"last_name"`
	} `json:"user"`
}

func NewRouter(cfg config.Config, logger *slog.Logger) *gin.Engine {
	if cfg.AppEnv == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	if err := router.SetTrustedProxies(nil); err != nil {
		logger.Error("failed to configure trusted proxies", "error", err)
	}
	router.Use(gin.Recovery())
	router.Use(requestLogger(logger))

	router.GET("/health", healthHandler)
	router.GET("/hello", helloHandler(cfg, logger))

	return router
}

func requestLogger(logger *slog.Logger) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		ctx.Next()

		logger.Info(
			"http request",
			"method", ctx.Request.Method,
			"path", ctx.Request.URL.Path,
			"status", ctx.Writer.Status(),
			"client_ip", ctx.ClientIP(),
		)
	}
}

func healthHandler(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"service": "budget-service",
	})
}

func helloHandler(cfg config.Config, logger *slog.Logger) gin.HandlerFunc {
	client := &http.Client{Timeout: 5 * time.Second}

	return func(ctx *gin.Context) {
		authHeader := strings.TrimSpace(ctx.GetHeader("Authorization"))
		if authHeader == "" {
			unauthenticatedResponse(ctx)
			return
		}

		req, err := http.NewRequestWithContext(ctx.Request.Context(), http.MethodGet, strings.TrimRight(cfg.AuthServiceURL, "/")+"/auth/me", nil)
		if err != nil {
			logger.Error("failed to create auth service request", "error", err)
			ctx.JSON(http.StatusInternalServerError, gin.H{
				"message": "failed to verify authentication",
				"service": "budget-service",
			})
			return
		}
		req.Header.Set("Authorization", authHeader)

		resp, err := client.Do(req)
		if err != nil {
			logger.Error("failed to call auth service", "error", err, "auth_service_url", cfg.AuthServiceURL)
			ctx.JSON(http.StatusBadGateway, gin.H{
				"message": "failed to verify authentication",
				"service": "budget-service",
			})
			return
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			unauthenticatedResponse(ctx)
			return
		}

		var authResp authUserResponse
		if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
			logger.Error("failed to decode auth service response", "error", err)
			ctx.JSON(http.StatusBadGateway, gin.H{
				"message": "failed to verify authentication",
				"service": "budget-service",
			})
			return
		}

		fullName := strings.TrimSpace(authResp.User.FirstName + " " + authResp.User.LastName)
		ctx.JSON(http.StatusOK, gin.H{
			"message": "hello " + fullName,
			"service": "budget-service",
		})
	}
}

func unauthenticatedResponse(ctx *gin.Context) {
	ctx.JSON(http.StatusUnauthorized, gin.H{
		"message": "fuck you you are not authentivated",
		"service": "budget-service",
	})
}
