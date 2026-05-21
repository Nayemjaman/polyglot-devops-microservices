package transaction

import (
	"context"

	"github.com/google/uuid"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/api"
	"github.com/shopspring/decimal"
)

type MonthlySummaryRequest struct {
	UserID uuid.UUID
	Year   int
	Month  int
}

type MonthlySummary struct {
	TotalIncome  decimal.Decimal `json:"-"`
	TotalExpense decimal.Decimal `json:"-"`
	Balance      decimal.Decimal `json:"-"`
	CurrencyCode string          `json:"currency_code"`
}

func (s MonthlySummary) MarshalJSON() ([]byte, error) {
	type payload struct {
		TotalIncome  api.Decimal `json:"total_income"`
		TotalExpense api.Decimal `json:"total_expense"`
		Balance      api.Decimal `json:"balance"`
		CurrencyCode string      `json:"currency_code"`
	}
	return jsonMarshal(payload{
		TotalIncome:  api.NewDecimal(s.TotalIncome),
		TotalExpense: api.NewDecimal(s.TotalExpense),
		Balance:      api.NewDecimal(s.Balance),
		CurrencyCode: s.CurrencyCode,
	})
}

type CategorySpendingRequest struct {
	UserID     uuid.UUID
	CategoryID uuid.UUID
	Year       int
	Month      int
}

type CategorySpending struct {
	CategoryID   uuid.UUID
	CategoryName string
	TotalSpent   decimal.Decimal
	CurrencyCode string
}

type SummaryClient interface {
	GetUserMonthlySummary(ctx context.Context, request MonthlySummaryRequest) (MonthlySummary, error)
	GetUserCategorySpending(ctx context.Context, request CategorySpendingRequest) (CategorySpending, error)
}

type UnavailableClient struct{}

func NewUnavailableClient() UnavailableClient {
	return UnavailableClient{}
}

func (UnavailableClient) GetUserMonthlySummary(context.Context, MonthlySummaryRequest) (MonthlySummary, error) {
	return MonthlySummary{}, ErrUnavailable
}

func (UnavailableClient) GetUserCategorySpending(context.Context, CategorySpendingRequest) (CategorySpending, error) {
	return CategorySpending{}, ErrUnavailable
}
