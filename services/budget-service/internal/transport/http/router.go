package http

import (
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/auth"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/clients/transaction"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/repositories"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/services"
	"gorm.io/gorm"
)

func NewRouter(cfg config.Config, logger *slog.Logger, db *gorm.DB) *gin.Engine {
	if cfg.AppEnv == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	if err := router.SetTrustedProxies(nil); err != nil {
		logger.Error("failed to configure trusted proxies", "error", err)
	}
	router.Use(gin.Recovery())
	router.Use(requestIDMiddleware())
	router.Use(corsMiddleware(cfg.CORSAllowedOrigins))
	router.Use(rateLimitMiddleware(cfg))
	router.Use(metricsMiddleware())
	router.Use(requestLogger(logger))

	router.GET("/health", healthHandler)
	router.GET("/metrics", metricsHandler)
	authClient := auth.NewClient(cfg.AuthServiceURL)
	protected := router.Group("")
	protected.Use(authMiddleware(authClient, logger))
	protected.GET("/hello", helloHandler)

	budgetRepo := repositories.NewBudgetRepository(db)
	transactionClient := transaction.NewUnavailableClient()
	budgetService := services.NewBudgetService(budgetRepo, transactionClient)
	budgets := newBudgetHandler(budgetService)

	apiRoutes := protected.Group("/api")
	apiRoutes.POST("/budgets", budgets.createBudget)
	apiRoutes.GET("/budgets", budgets.listBudgets)
	apiRoutes.GET("/budgets/status/monthly", budgets.monthlyStatus)
	apiRoutes.GET("/budgets/status/category-wise", budgets.categoryWiseStatus)
	apiRoutes.GET("/budgets/:id", budgets.getBudget)
	apiRoutes.PATCH("/budgets/:id", budgets.updateBudget)
	apiRoutes.DELETE("/budgets/:id", budgets.deleteBudget)
	apiRoutes.GET("/budgets/:id/usage", budgets.budgetUsage)

	apiRoutes.POST("/budgets/:id/categories", budgets.createCategory)
	apiRoutes.GET("/budgets/:id/categories", budgets.listCategories)
	apiRoutes.PATCH("/budgets/:id/categories/:category_id", budgets.updateCategory)
	apiRoutes.DELETE("/budgets/:id/categories/:category_id", budgets.deleteCategory)

	apiRoutes.POST("/budgets/:id/alert-rules", budgets.createAlertRule)
	apiRoutes.GET("/budgets/:id/alert-rules", budgets.listAlertRules)
	apiRoutes.PATCH("/budgets/:id/alert-rules/:rule_id", budgets.updateAlertRule)
	apiRoutes.DELETE("/budgets/:id/alert-rules/:rule_id", budgets.deleteAlertRule)

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
			"request_id", ctx.GetString("request_id"),
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
		"message": "hello",
		"service": "budget-service",
	})
}

func unauthenticatedResponse(ctx *gin.Context) {
	ctx.JSON(http.StatusUnauthorized, gin.H{
		"success": false,
		"message": "Authentication required",
	})
}
