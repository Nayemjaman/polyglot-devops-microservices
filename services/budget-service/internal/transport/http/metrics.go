package http

import (
	"fmt"
	"net/http"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

type metricStore struct {
	mu       sync.Mutex
	requests map[string]int64
	latency  map[string]durationSummary
}

type durationSummary struct {
	count int64
	sum   float64
}

var appMetrics = metricStore{
	requests: make(map[string]int64),
	latency:  make(map[string]durationSummary),
}

func metricsMiddleware() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if ctx.Request.URL.Path == "/metrics" {
			ctx.Next()
			return
		}

		startedAt := time.Now()
		ctx.Next()

		route := ctx.FullPath()
		if route == "" {
			route = ctx.Request.URL.Path
		}
		method := ctx.Request.Method
		status := ctx.Writer.Status()
		elapsed := time.Since(startedAt).Seconds()

		requestKey := fmt.Sprintf("%s\x00%s\x00%d", method, route, status)
		latencyKey := fmt.Sprintf("%s\x00%s", method, route)

		appMetrics.mu.Lock()
		appMetrics.requests[requestKey]++
		current := appMetrics.latency[latencyKey]
		current.count++
		current.sum += elapsed
		appMetrics.latency[latencyKey] = current
		appMetrics.mu.Unlock()
	}
}

func metricsHandler(ctx *gin.Context) {
	appMetrics.mu.Lock()
	defer appMetrics.mu.Unlock()

	var lines []string
	lines = append(lines,
		"# HELP app_http_requests_total Total HTTP requests handled by the service.",
		"# TYPE app_http_requests_total counter",
	)

	requestKeys := make([]string, 0, len(appMetrics.requests))
	for key := range appMetrics.requests {
		requestKeys = append(requestKeys, key)
	}
	sort.Strings(requestKeys)
	for _, key := range requestKeys {
		parts := strings.Split(key, "\x00")
		lines = append(lines, fmt.Sprintf(
			"app_http_requests_total{service=\"budget-service\",method=\"%s\",route=\"%s\",status=\"%s\"} %d",
			parts[0],
			parts[1],
			parts[2],
			appMetrics.requests[key],
		))
	}

	lines = append(lines,
		"# HELP app_http_request_duration_seconds HTTP request latency summary.",
		"# TYPE app_http_request_duration_seconds summary",
	)

	latencyKeys := make([]string, 0, len(appMetrics.latency))
	for key := range appMetrics.latency {
		latencyKeys = append(latencyKeys, key)
	}
	sort.Strings(latencyKeys)
	for _, key := range latencyKeys {
		parts := strings.Split(key, "\x00")
		labels := fmt.Sprintf("service=\"budget-service\",method=\"%s\",route=\"%s\"", parts[0], parts[1])
		summary := appMetrics.latency[key]
		lines = append(lines, fmt.Sprintf("app_http_request_duration_seconds_count{%s} %d", labels, summary.count))
		lines = append(lines, fmt.Sprintf("app_http_request_duration_seconds_sum{%s} %.6f", labels, summary.sum))
	}

	ctx.Data(http.StatusOK, "text/plain; version=0.0.4", []byte(strings.Join(lines, "\n")+"\n"))
}
