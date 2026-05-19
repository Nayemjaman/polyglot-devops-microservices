package http

import (
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service-go/internal/config"
)

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
	router.GET("/hello", helloHandler)

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

func helloHandler(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"message": "hello world",
		"service": "budget-service",
	})
}
