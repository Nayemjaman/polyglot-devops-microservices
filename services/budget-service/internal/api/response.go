package api

import (
	"encoding/json"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/shopspring/decimal"
)

type Response struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
}

type PaginatedResponse struct {
	Success    bool        `json:"success"`
	Message    string      `json:"message"`
	Data       interface{} `json:"data"`
	Pagination Pagination  `json:"pagination"`
}

type ErrorResponse struct {
	Success bool                `json:"success"`
	Message string              `json:"message"`
	Errors  map[string][]string `json:"errors,omitempty"`
}

type Pagination struct {
	Page       int   `json:"page"`
	PageSize   int   `json:"page_size"`
	TotalItems int64 `json:"total_items"`
	TotalPages int   `json:"total_pages"`
}

type Decimal struct {
	decimal.Decimal
}

func NewDecimal(value decimal.Decimal) Decimal {
	return Decimal{Decimal: value}
}

func (d Decimal) MarshalJSON() ([]byte, error) {
	return []byte(d.Decimal.String()), nil
}

func (d *Decimal) UnmarshalJSON(data []byte) error {
	var value decimal.Decimal
	if err := value.UnmarshalJSON(data); err != nil {
		var raw json.Number
		if jsonErr := json.Unmarshal(data, &raw); jsonErr != nil {
			return err
		}
		parsed, parseErr := decimal.NewFromString(raw.String())
		if parseErr != nil {
			return err
		}
		value = parsed
	}
	d.Decimal = value
	return nil
}

func OK(ctx *gin.Context, message string, data interface{}) {
	ctx.JSON(http.StatusOK, Response{Success: true, Message: message, Data: data})
}

func Created(ctx *gin.Context, message string, data interface{}) {
	ctx.JSON(http.StatusCreated, Response{Success: true, Message: message, Data: data})
}

func Paginated(ctx *gin.Context, message string, data interface{}, pagination Pagination) {
	ctx.JSON(http.StatusOK, PaginatedResponse{Success: true, Message: message, Data: data, Pagination: pagination})
}

func Error(ctx *gin.Context, status int, message string, errors map[string][]string) {
	ctx.JSON(status, ErrorResponse{Success: false, Message: message, Errors: errors})
}
