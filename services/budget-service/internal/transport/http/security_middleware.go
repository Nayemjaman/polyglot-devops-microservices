package http

import (
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/config"
)

type rateBucket struct {
	count     int
	resetTime time.Time
}

func requestIDMiddleware() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		requestID := ctx.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.NewString()
		}
		ctx.Header("X-Request-ID", requestID)
		ctx.Set("request_id", requestID)
		ctx.Next()
	}
}

func corsMiddleware(allowedOrigins []string) gin.HandlerFunc {
	allowed := map[string]struct{}{}
	for _, origin := range allowedOrigins {
		allowed[origin] = struct{}{}
	}

	return func(ctx *gin.Context) {
		origin := ctx.GetHeader("Origin")
		if _, ok := allowed[origin]; ok {
			ctx.Header("Access-Control-Allow-Origin", origin)
			ctx.Header("Vary", "Origin")
			ctx.Header("Access-Control-Allow-Credentials", "true")
			ctx.Header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Request-ID")
			ctx.Header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
		}

		if ctx.Request.Method == http.MethodOptions {
			ctx.AbortWithStatus(http.StatusNoContent)
			return
		}

		ctx.Next()
	}
}

func rateLimitMiddleware(cfg config.Config) gin.HandlerFunc {
	var mutex sync.Mutex
	buckets := map[string]*rateBucket{}

	return func(ctx *gin.Context) {
		if ctx.Request.URL.Path == "/health" || ctx.Request.URL.Path == "/metrics" {
			ctx.Next()
			return
		}

		now := time.Now()
		key := ctx.ClientIP()

		mutex.Lock()
		bucket := buckets[key]
		if bucket == nil || now.After(bucket.resetTime) {
			bucket = &rateBucket{count: 0, resetTime: now.Add(cfg.RateLimitWindow)}
			buckets[key] = bucket
		}
		bucket.count++
		remaining := cfg.RateLimitRequests - bucket.count
		resetSeconds := int(time.Until(bucket.resetTime).Seconds())
		mutex.Unlock()

		ctx.Header("X-RateLimit-Limit", strconv.Itoa(cfg.RateLimitRequests))
		ctx.Header("X-RateLimit-Remaining", strconv.Itoa(max(remaining, 0)))
		ctx.Header("X-RateLimit-Reset", strconv.Itoa(max(resetSeconds, 0)))

		if remaining < 0 {
			ctx.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"success": false,
				"message": "Rate limit exceeded",
			})
			return
		}

		ctx.Next()
	}
}
