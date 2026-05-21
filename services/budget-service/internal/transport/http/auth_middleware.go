package http

import (
	"errors"
	"log/slog"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/api"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/auth"
)

func authMiddleware(client *auth.Client, logger *slog.Logger) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		authHeader := strings.TrimSpace(ctx.GetHeader("Authorization"))
		if authHeader == "" {
			unauthenticatedResponse(ctx)
			ctx.Abort()
			return
		}

		user, err := client.Verify(ctx.Request.Context(), authHeader)
		if err != nil {
			if !errors.Is(err, auth.ErrInvalidToken) {
				logger.Error("failed to verify auth token", "error", err)
				api.Error(ctx, http.StatusBadGateway, "Failed to verify authentication", nil)
				ctx.Abort()
				return
			}
			unauthenticatedResponse(ctx)
			ctx.Abort()
			return
		}

		ctx.Set(userIDContextKey, user.ID)
		ctx.Next()
	}
}
