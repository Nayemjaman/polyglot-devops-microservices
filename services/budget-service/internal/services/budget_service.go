package services

import (
	"context"
	"errors"
	"math"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/api"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/clients/transaction"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/models"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/repositories"
	"github.com/shopspring/decimal"
)

const (
	UsageStatusOnTrack  = "ON_TRACK"
	UsageStatusWarning  = "WARNING"
	UsageStatusExceeded = "EXCEEDED"
	UsageStatusNoBudget = "NO_BUDGET"
)

type BudgetService struct {
	repo         *repositories.BudgetRepository
	transactions transaction.SummaryClient
}

func NewBudgetService(repo *repositories.BudgetRepository, transactions transaction.SummaryClient) *BudgetService {
	return &BudgetService{repo: repo, transactions: transactions}
}

type CreateBudgetInput struct {
	Name              string          `json:"name"`
	Year              int             `json:"year"`
	Month             int             `json:"month"`
	TotalBudgetAmount decimal.Decimal `json:"total_budget_amount"`
	CurrencyCode      string          `json:"currency_code"`
}

type UpdateBudgetInput struct {
	Name              *string          `json:"name"`
	TotalBudgetAmount *decimal.Decimal `json:"total_budget_amount"`
	Status            *string          `json:"status"`
}

type BudgetListFilters struct {
	Page     int
	PageSize int
	Year     *int
	Month    *int
	Status   *string
}

type CreateCategoryInput struct {
	CategoryID               uuid.UUID       `json:"category_id"`
	CategoryNameSnapshot     string          `json:"category_name_snapshot"`
	BudgetAmount             decimal.Decimal `json:"budget_amount"`
	AlertThresholdPercentage decimal.Decimal `json:"alert_threshold_percentage"`
}

type UpdateCategoryInput struct {
	CategoryNameSnapshot     *string          `json:"category_name_snapshot"`
	BudgetAmount             *decimal.Decimal `json:"budget_amount"`
	AlertThresholdPercentage *decimal.Decimal `json:"alert_threshold_percentage"`
}

type CreateAlertRuleInput struct {
	RuleType            string          `json:"rule_type"`
	ThresholdPercentage decimal.Decimal `json:"threshold_percentage"`
	IsEnabled           bool            `json:"is_enabled"`
}

type UpdateAlertRuleInput struct {
	ThresholdPercentage *decimal.Decimal `json:"threshold_percentage"`
	IsEnabled           *bool            `json:"is_enabled"`
}

type BudgetOut struct {
	ID                uuid.UUID   `json:"id"`
	UserID            uuid.UUID   `json:"user_id,omitempty"`
	Name              string      `json:"name"`
	Year              int         `json:"year"`
	Month             int         `json:"month"`
	TotalBudgetAmount api.Decimal `json:"total_budget_amount"`
	CurrencyCode      string      `json:"currency_code"`
	Status            string      `json:"status"`
	CreatedAt         time.Time   `json:"created_at"`
	UpdatedAt         time.Time   `json:"updated_at"`
}

type BudgetDetailOut struct {
	BudgetOut
	Categories []BudgetCategoryOut  `json:"categories"`
	AlertRules []BudgetAlertRuleOut `json:"alert_rules"`
}

type BudgetCategoryOut struct {
	ID                       uuid.UUID   `json:"id"`
	BudgetID                 uuid.UUID   `json:"budget_id"`
	CategoryID               uuid.UUID   `json:"category_id"`
	CategoryNameSnapshot     string      `json:"category_name_snapshot"`
	BudgetAmount             api.Decimal `json:"budget_amount"`
	AlertThresholdPercentage api.Decimal `json:"alert_threshold_percentage"`
	CreatedAt                time.Time   `json:"created_at,omitempty"`
	UpdatedAt                time.Time   `json:"updated_at,omitempty"`
}

type BudgetAlertRuleOut struct {
	ID                  uuid.UUID   `json:"id"`
	BudgetID            uuid.UUID   `json:"budget_id"`
	RuleType            string      `json:"rule_type"`
	ThresholdPercentage api.Decimal `json:"threshold_percentage"`
	IsEnabled           bool        `json:"is_enabled"`
	CreatedAt           time.Time   `json:"created_at,omitempty"`
	UpdatedAt           time.Time   `json:"updated_at,omitempty"`
}

type MonthlyStatusOut struct {
	BudgetID          uuid.UUID                  `json:"budget_id"`
	UserID            uuid.UUID                  `json:"user_id"`
	Year              int                        `json:"year"`
	Month             int                        `json:"month"`
	CurrencyCode      string                     `json:"currency_code"`
	TotalBudgetAmount api.Decimal                `json:"total_budget_amount"`
	TotalSpentAmount  api.Decimal                `json:"total_spent_amount"`
	RemainingAmount   api.Decimal                `json:"remaining_amount"`
	UsedPercentage    api.Decimal                `json:"used_percentage"`
	Status            string                     `json:"status"`
	Summary           transaction.MonthlySummary `json:"summary"`
}

type CategoryWiseStatusOut struct {
	BudgetID     uuid.UUID           `json:"budget_id"`
	Year         int                 `json:"year"`
	Month        int                 `json:"month"`
	CurrencyCode string              `json:"currency_code"`
	Categories   []CategoryStatusOut `json:"categories"`
}

type CategoryStatusOut struct {
	BudgetCategoryID         uuid.UUID   `json:"budget_category_id,omitempty"`
	CategoryID               uuid.UUID   `json:"category_id"`
	CategoryName             string      `json:"category_name"`
	BudgetAmount             api.Decimal `json:"budget_amount"`
	SpentAmount              api.Decimal `json:"spent_amount"`
	RemainingAmount          api.Decimal `json:"remaining_amount"`
	UsedPercentage           api.Decimal `json:"used_percentage"`
	AlertThresholdPercentage api.Decimal `json:"alert_threshold_percentage,omitempty"`
	Status                   string      `json:"status"`
	IsAlertTriggered         bool        `json:"is_alert_triggered,omitempty"`
}

type BudgetUsageOut struct {
	BudgetID          uuid.UUID           `json:"budget_id"`
	Name              string              `json:"name"`
	Year              int                 `json:"year"`
	Month             int                 `json:"month"`
	CurrencyCode      string              `json:"currency_code"`
	TotalBudgetAmount api.Decimal         `json:"total_budget_amount"`
	TotalSpentAmount  api.Decimal         `json:"total_spent_amount"`
	RemainingAmount   api.Decimal         `json:"remaining_amount"`
	UsedPercentage    api.Decimal         `json:"used_percentage"`
	Status            string              `json:"status"`
	Categories        []CategoryStatusOut `json:"categories"`
	GeneratedAt       time.Time           `json:"generated_at"`
}

func (s *BudgetService) CreateBudget(ctx context.Context, userID uuid.UUID, input CreateBudgetInput) (BudgetOut, error) {
	if err := validateCreateBudget(input); err != nil {
		return BudgetOut{}, err
	}

	exists, err := s.repo.ExistsActiveForPeriod(ctx, userID, input.Year, input.Month, nil)
	if err != nil {
		return BudgetOut{}, err
	}
	if exists {
		return BudgetOut{}, NewValidationError(map[string][]string{
			"month": {"Only one active budget is allowed for the same year and month"},
		})
	}

	budget := models.Budget{
		UserID:            userID,
		Name:              strings.TrimSpace(input.Name),
		Year:              input.Year,
		Month:             input.Month,
		TotalBudgetAmount: input.TotalBudgetAmount,
		CurrencyCode:      normalizeCurrency(input.CurrencyCode),
		Status:            models.BudgetStatusActive,
	}
	if err := s.repo.Create(ctx, &budget); err != nil {
		return BudgetOut{}, err
	}
	return toBudgetOut(budget, true), nil
}

func (s *BudgetService) ListBudgets(ctx context.Context, userID uuid.UUID, filters BudgetListFilters) ([]BudgetOut, api.Pagination, error) {
	page, pageSize := normalizePagination(filters.Page, filters.PageSize)
	if filters.Status != nil {
		status := strings.ToUpper(strings.TrimSpace(*filters.Status))
		filters.Status = &status
		if !isBudgetStatus(status) {
			return nil, api.Pagination{}, NewValidationError(map[string][]string{"status": {"Invalid budget status"}})
		}
	}

	budgets, total, err := s.repo.List(ctx, userID, repositories.BudgetFilters{Year: filters.Year, Month: filters.Month, Status: filters.Status}, page, pageSize)
	if err != nil {
		return nil, api.Pagination{}, err
	}

	out := make([]BudgetOut, 0, len(budgets))
	for _, budget := range budgets {
		out = append(out, toBudgetOut(budget, false))
	}

	return out, api.Pagination{
		Page:       page,
		PageSize:   pageSize,
		TotalItems: total,
		TotalPages: int(math.Ceil(float64(total) / float64(pageSize))),
	}, nil
}

func (s *BudgetService) GetBudget(ctx context.Context, userID, budgetID uuid.UUID) (BudgetDetailOut, error) {
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return BudgetDetailOut{}, serviceError(err)
	}
	return toBudgetDetailOut(budget), nil
}

func (s *BudgetService) UpdateBudget(ctx context.Context, userID, budgetID uuid.UUID, input UpdateBudgetInput) (BudgetOut, error) {
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return BudgetOut{}, serviceError(err)
	}

	if input.Name != nil {
		name := strings.TrimSpace(*input.Name)
		if name == "" {
			return BudgetOut{}, NewValidationError(map[string][]string{"name": {"Name is required"}})
		}
		budget.Name = name
	}
	if input.TotalBudgetAmount != nil {
		if input.TotalBudgetAmount.LessThanOrEqual(decimal.Zero) {
			return BudgetOut{}, NewValidationError(map[string][]string{"total_budget_amount": {"Total budget amount must be greater than 0"}})
		}
		currentCategoryTotal, err := s.repo.SumCategoryBudget(ctx, budget.ID, nil)
		if err != nil {
			return BudgetOut{}, err
		}
		if decimal.NewFromFloat(currentCategoryTotal).GreaterThan(*input.TotalBudgetAmount) {
			return BudgetOut{}, NewValidationError(map[string][]string{"total_budget_amount": {"Total budget amount cannot be less than category budget total"}})
		}
		budget.TotalBudgetAmount = *input.TotalBudgetAmount
	}
	if input.Status != nil {
		status := strings.ToUpper(strings.TrimSpace(*input.Status))
		if !isBudgetStatus(status) {
			return BudgetOut{}, NewValidationError(map[string][]string{"status": {"Invalid budget status"}})
		}
		if status == models.BudgetStatusActive {
			exists, err := s.repo.ExistsActiveForPeriod(ctx, userID, budget.Year, budget.Month, &budget.ID)
			if err != nil {
				return BudgetOut{}, err
			}
			if exists {
				return BudgetOut{}, NewValidationError(map[string][]string{"status": {"Another active budget already exists for this year and month"}})
			}
		}
		budget.Status = status
	}

	if err := s.repo.Update(ctx, &budget); err != nil {
		return BudgetOut{}, err
	}
	return toBudgetOut(budget, false), nil
}

func (s *BudgetService) ArchiveBudget(ctx context.Context, userID, budgetID uuid.UUID) error {
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return serviceError(err)
	}
	budget.Status = models.BudgetStatusArchived
	return s.repo.Update(ctx, &budget)
}

func (s *BudgetService) CreateCategory(ctx context.Context, userID, budgetID uuid.UUID, input CreateCategoryInput) (BudgetCategoryOut, error) {
	if err := validateCreateCategory(input); err != nil {
		return BudgetCategoryOut{}, err
	}
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return BudgetCategoryOut{}, serviceError(err)
	}
	if err := s.ensureCategoryTotal(ctx, budget, input.BudgetAmount, nil); err != nil {
		return BudgetCategoryOut{}, err
	}

	category := models.BudgetCategory{
		BudgetID:                 budgetID,
		CategoryID:               input.CategoryID,
		CategoryNameSnapshot:     strings.TrimSpace(input.CategoryNameSnapshot),
		BudgetAmount:             input.BudgetAmount,
		AlertThresholdPercentage: input.AlertThresholdPercentage,
	}
	if err := s.repo.CreateCategory(ctx, &category); err != nil {
		return BudgetCategoryOut{}, err
	}
	return toCategoryOut(category, true), nil
}

func (s *BudgetService) ListCategories(ctx context.Context, userID, budgetID uuid.UUID) ([]BudgetCategoryOut, error) {
	if _, err := s.repo.Get(ctx, userID, budgetID); err != nil {
		return nil, serviceError(err)
	}
	categories, err := s.repo.ListCategories(ctx, userID, budgetID)
	if err != nil {
		return nil, err
	}
	out := make([]BudgetCategoryOut, 0, len(categories))
	for _, category := range categories {
		out = append(out, toCategoryOut(category, true))
	}
	return out, nil
}

func (s *BudgetService) UpdateCategory(ctx context.Context, userID, budgetID, categoryID uuid.UUID, input UpdateCategoryInput) (BudgetCategoryOut, error) {
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return BudgetCategoryOut{}, serviceError(err)
	}
	category, err := s.repo.GetCategory(ctx, userID, budgetID, categoryID)
	if err != nil {
		return BudgetCategoryOut{}, serviceError(err)
	}

	if input.CategoryNameSnapshot != nil {
		name := strings.TrimSpace(*input.CategoryNameSnapshot)
		if name == "" {
			return BudgetCategoryOut{}, NewValidationError(map[string][]string{"category_name_snapshot": {"Category name snapshot is required"}})
		}
		category.CategoryNameSnapshot = name
	}
	if input.BudgetAmount != nil {
		if input.BudgetAmount.LessThanOrEqual(decimal.Zero) {
			return BudgetCategoryOut{}, NewValidationError(map[string][]string{"budget_amount": {"Budget amount must be greater than 0"}})
		}
		if err := s.ensureCategoryTotal(ctx, budget, *input.BudgetAmount, &category.ID); err != nil {
			return BudgetCategoryOut{}, err
		}
		category.BudgetAmount = *input.BudgetAmount
	}
	if input.AlertThresholdPercentage != nil {
		if !isPercentage(*input.AlertThresholdPercentage) {
			return BudgetCategoryOut{}, NewValidationError(map[string][]string{"alert_threshold_percentage": {"Alert threshold percentage must be between 1 and 100"}})
		}
		category.AlertThresholdPercentage = *input.AlertThresholdPercentage
	}

	if err := s.repo.UpdateCategory(ctx, &category); err != nil {
		return BudgetCategoryOut{}, err
	}
	return toCategoryOut(category, true), nil
}

func (s *BudgetService) DeleteCategory(ctx context.Context, userID, budgetID, categoryID uuid.UUID) error {
	category, err := s.repo.GetCategory(ctx, userID, budgetID, categoryID)
	if err != nil {
		return serviceError(err)
	}
	return s.repo.DeleteCategory(ctx, &category)
}

func (s *BudgetService) CreateAlertRule(ctx context.Context, userID, budgetID uuid.UUID, input CreateAlertRuleInput) (BudgetAlertRuleOut, error) {
	if err := validateCreateAlertRule(input); err != nil {
		return BudgetAlertRuleOut{}, err
	}
	if _, err := s.repo.Get(ctx, userID, budgetID); err != nil {
		return BudgetAlertRuleOut{}, serviceError(err)
	}

	rule := models.BudgetAlertRule{
		BudgetID:            budgetID,
		RuleType:            strings.ToUpper(strings.TrimSpace(input.RuleType)),
		ThresholdPercentage: input.ThresholdPercentage,
		IsEnabled:           input.IsEnabled,
	}
	if err := s.repo.CreateAlertRule(ctx, &rule); err != nil {
		return BudgetAlertRuleOut{}, err
	}
	return toAlertRuleOut(rule, true), nil
}

func (s *BudgetService) ListAlertRules(ctx context.Context, userID, budgetID uuid.UUID) ([]BudgetAlertRuleOut, error) {
	if _, err := s.repo.Get(ctx, userID, budgetID); err != nil {
		return nil, serviceError(err)
	}
	rules, err := s.repo.ListAlertRules(ctx, userID, budgetID)
	if err != nil {
		return nil, err
	}
	out := make([]BudgetAlertRuleOut, 0, len(rules))
	for _, rule := range rules {
		out = append(out, toAlertRuleOut(rule, true))
	}
	return out, nil
}

func (s *BudgetService) UpdateAlertRule(ctx context.Context, userID, budgetID, ruleID uuid.UUID, input UpdateAlertRuleInput) (BudgetAlertRuleOut, error) {
	rule, err := s.repo.GetAlertRule(ctx, userID, budgetID, ruleID)
	if err != nil {
		return BudgetAlertRuleOut{}, serviceError(err)
	}
	if input.ThresholdPercentage != nil {
		if !isPercentage(*input.ThresholdPercentage) {
			return BudgetAlertRuleOut{}, NewValidationError(map[string][]string{"threshold_percentage": {"Threshold percentage must be between 1 and 100"}})
		}
		rule.ThresholdPercentage = *input.ThresholdPercentage
	}
	if input.IsEnabled != nil {
		rule.IsEnabled = *input.IsEnabled
	}
	if err := s.repo.UpdateAlertRule(ctx, &rule); err != nil {
		return BudgetAlertRuleOut{}, err
	}
	return toAlertRuleOut(rule, true), nil
}

func (s *BudgetService) DeleteAlertRule(ctx context.Context, userID, budgetID, ruleID uuid.UUID) error {
	rule, err := s.repo.GetAlertRule(ctx, userID, budgetID, ruleID)
	if err != nil {
		return serviceError(err)
	}
	return s.repo.DeleteAlertRule(ctx, &rule)
}

func (s *BudgetService) GetMonthlyStatus(ctx context.Context, userID uuid.UUID, year, month int) (MonthlyStatusOut, error) {
	budget, err := s.repo.GetByPeriod(ctx, userID, year, month)
	if err != nil {
		return MonthlyStatusOut{}, serviceError(err)
	}
	summary, err := s.transactions.GetUserMonthlySummary(ctx, transaction.MonthlySummaryRequest{UserID: userID, Year: year, Month: month})
	if err != nil {
		return MonthlyStatusOut{}, ErrDependency
	}

	totalSpent := summary.TotalExpense
	remaining := budget.TotalBudgetAmount.Sub(totalSpent)
	used := percentage(totalSpent, budget.TotalBudgetAmount)
	return MonthlyStatusOut{
		BudgetID:          budget.ID,
		UserID:            userID,
		Year:              year,
		Month:             month,
		CurrencyCode:      budget.CurrencyCode,
		TotalBudgetAmount: api.NewDecimal(budget.TotalBudgetAmount),
		TotalSpentAmount:  api.NewDecimal(totalSpent),
		RemainingAmount:   api.NewDecimal(remaining),
		UsedPercentage:    api.NewDecimal(used),
		Status:            statusFor(used, decimal.NewFromInt(80)),
		Summary:           summary,
	}, nil
}

func (s *BudgetService) GetCategoryWiseStatus(ctx context.Context, userID uuid.UUID, year, month int) (CategoryWiseStatusOut, error) {
	budget, err := s.repo.GetByPeriod(ctx, userID, year, month)
	if err != nil {
		return CategoryWiseStatusOut{}, serviceError(err)
	}
	categories, err := s.categoryStatuses(ctx, userID, budget)
	if err != nil {
		return CategoryWiseStatusOut{}, err
	}
	return CategoryWiseStatusOut{BudgetID: budget.ID, Year: year, Month: month, CurrencyCode: budget.CurrencyCode, Categories: categories}, nil
}

func (s *BudgetService) GetBudgetUsage(ctx context.Context, userID, budgetID uuid.UUID) (BudgetUsageOut, error) {
	budget, err := s.repo.Get(ctx, userID, budgetID)
	if err != nil {
		return BudgetUsageOut{}, serviceError(err)
	}
	summary, err := s.transactions.GetUserMonthlySummary(ctx, transaction.MonthlySummaryRequest{UserID: userID, Year: budget.Year, Month: budget.Month})
	if err != nil {
		return BudgetUsageOut{}, ErrDependency
	}
	categories, err := s.categoryStatuses(ctx, userID, budget)
	if err != nil {
		return BudgetUsageOut{}, err
	}

	totalSpent := summary.TotalExpense
	remaining := budget.TotalBudgetAmount.Sub(totalSpent)
	used := percentage(totalSpent, budget.TotalBudgetAmount)
	return BudgetUsageOut{
		BudgetID:          budget.ID,
		Name:              budget.Name,
		Year:              budget.Year,
		Month:             budget.Month,
		CurrencyCode:      budget.CurrencyCode,
		TotalBudgetAmount: api.NewDecimal(budget.TotalBudgetAmount),
		TotalSpentAmount:  api.NewDecimal(totalSpent),
		RemainingAmount:   api.NewDecimal(remaining),
		UsedPercentage:    api.NewDecimal(used),
		Status:            statusFor(used, decimal.NewFromInt(80)),
		Categories:        categories,
		GeneratedAt:       time.Now().UTC(),
	}, nil
}

func (s *BudgetService) categoryStatuses(ctx context.Context, userID uuid.UUID, budget models.Budget) ([]CategoryStatusOut, error) {
	out := make([]CategoryStatusOut, 0, len(budget.Categories))
	for _, category := range budget.Categories {
		spending, err := s.transactions.GetUserCategorySpending(ctx, transaction.CategorySpendingRequest{
			UserID: userID, CategoryID: category.CategoryID, Year: budget.Year, Month: budget.Month,
		})
		if err != nil {
			return nil, ErrDependency
		}
		used := percentage(spending.TotalSpent, category.BudgetAmount)
		remaining := category.BudgetAmount.Sub(spending.TotalSpent)
		status := statusFor(used, category.AlertThresholdPercentage)
		out = append(out, CategoryStatusOut{
			BudgetCategoryID:         category.ID,
			CategoryID:               category.CategoryID,
			CategoryName:             firstNonEmpty(spending.CategoryName, category.CategoryNameSnapshot),
			BudgetAmount:             api.NewDecimal(category.BudgetAmount),
			SpentAmount:              api.NewDecimal(spending.TotalSpent),
			RemainingAmount:          api.NewDecimal(remaining),
			UsedPercentage:           api.NewDecimal(used),
			AlertThresholdPercentage: api.NewDecimal(category.AlertThresholdPercentage),
			Status:                   status,
			IsAlertTriggered:         status != UsageStatusOnTrack,
		})
	}
	return out, nil
}

func validateCreateBudget(input CreateBudgetInput) error {
	errors := map[string][]string{}
	if strings.TrimSpace(input.Name) == "" {
		errors["name"] = []string{"Name is required"}
	}
	if input.Year <= 0 {
		errors["year"] = []string{"Year is required"}
	}
	if input.Month < 1 || input.Month > 12 {
		errors["month"] = []string{"Month must be between 1 and 12"}
	}
	if input.TotalBudgetAmount.LessThanOrEqual(decimal.Zero) {
		errors["total_budget_amount"] = []string{"Total budget amount must be greater than 0"}
	}
	if normalizeCurrency(input.CurrencyCode) == "" {
		errors["currency_code"] = []string{"Currency code is required"}
	}
	if len(errors) > 0 {
		return NewValidationError(errors)
	}
	return nil
}

func validateCreateCategory(input CreateCategoryInput) error {
	errors := map[string][]string{}
	if input.CategoryID == uuid.Nil {
		errors["category_id"] = []string{"Category ID is required"}
	}
	if strings.TrimSpace(input.CategoryNameSnapshot) == "" {
		errors["category_name_snapshot"] = []string{"Category name snapshot is required"}
	}
	if input.BudgetAmount.LessThanOrEqual(decimal.Zero) {
		errors["budget_amount"] = []string{"Budget amount must be greater than 0"}
	}
	if !isPercentage(input.AlertThresholdPercentage) {
		errors["alert_threshold_percentage"] = []string{"Alert threshold percentage must be between 1 and 100"}
	}
	if len(errors) > 0 {
		return NewValidationError(errors)
	}
	return nil
}

func validateCreateAlertRule(input CreateAlertRuleInput) error {
	errors := map[string][]string{}
	ruleType := strings.ToUpper(strings.TrimSpace(input.RuleType))
	if !isAlertRuleType(ruleType) {
		errors["rule_type"] = []string{"Invalid alert rule type"}
	}
	if !isPercentage(input.ThresholdPercentage) {
		errors["threshold_percentage"] = []string{"Threshold percentage must be between 1 and 100"}
	}
	if len(errors) > 0 {
		return NewValidationError(errors)
	}
	return nil
}

func (s *BudgetService) ensureCategoryTotal(ctx context.Context, budget models.Budget, newAmount decimal.Decimal, excludeCategoryID *uuid.UUID) error {
	total, err := s.repo.SumCategoryBudget(ctx, budget.ID, excludeCategoryID)
	if err != nil {
		return err
	}
	if decimal.NewFromFloat(total).Add(newAmount).GreaterThan(budget.TotalBudgetAmount) {
		return NewValidationError(map[string][]string{"budget_amount": {"Sum of category budget amounts cannot exceed total budget amount"}})
	}
	return nil
}

func toBudgetOut(budget models.Budget, includeUser bool) BudgetOut {
	out := BudgetOut{
		ID:                budget.ID,
		Name:              budget.Name,
		Year:              budget.Year,
		Month:             budget.Month,
		TotalBudgetAmount: api.NewDecimal(budget.TotalBudgetAmount),
		CurrencyCode:      budget.CurrencyCode,
		Status:            budget.Status,
		CreatedAt:         budget.CreatedAt,
		UpdatedAt:         budget.UpdatedAt,
	}
	if includeUser {
		out.UserID = budget.UserID
	}
	return out
}

func toBudgetDetailOut(budget models.Budget) BudgetDetailOut {
	categories := make([]BudgetCategoryOut, 0, len(budget.Categories))
	for _, category := range budget.Categories {
		categories = append(categories, toCategoryOut(category, false))
	}
	rules := make([]BudgetAlertRuleOut, 0, len(budget.AlertRules))
	for _, rule := range budget.AlertRules {
		rules = append(rules, toAlertRuleOut(rule, false))
	}
	return BudgetDetailOut{BudgetOut: toBudgetOut(budget, true), Categories: categories, AlertRules: rules}
}

func toCategoryOut(category models.BudgetCategory, includeTimestamps bool) BudgetCategoryOut {
	out := BudgetCategoryOut{
		ID:                       category.ID,
		BudgetID:                 category.BudgetID,
		CategoryID:               category.CategoryID,
		CategoryNameSnapshot:     category.CategoryNameSnapshot,
		BudgetAmount:             api.NewDecimal(category.BudgetAmount),
		AlertThresholdPercentage: api.NewDecimal(category.AlertThresholdPercentage),
	}
	if includeTimestamps {
		out.CreatedAt = category.CreatedAt
		out.UpdatedAt = category.UpdatedAt
	}
	return out
}

func toAlertRuleOut(rule models.BudgetAlertRule, includeTimestamps bool) BudgetAlertRuleOut {
	out := BudgetAlertRuleOut{
		ID:                  rule.ID,
		BudgetID:            rule.BudgetID,
		RuleType:            rule.RuleType,
		ThresholdPercentage: api.NewDecimal(rule.ThresholdPercentage),
		IsEnabled:           rule.IsEnabled,
	}
	if includeTimestamps {
		out.CreatedAt = rule.CreatedAt
		out.UpdatedAt = rule.UpdatedAt
	}
	return out
}

func serviceError(err error) error {
	if errors.Is(err, repositories.ErrRecordNotFound) {
		return ErrNotFound
	}
	return err
}

func normalizePagination(page, pageSize int) (int, int) {
	if page < 1 {
		page = 1
	}
	if pageSize < 1 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}
	return page, pageSize
}

func normalizeCurrency(value string) string {
	value = strings.ToUpper(strings.TrimSpace(value))
	if len(value) != 3 {
		return ""
	}
	return value
}

func isBudgetStatus(value string) bool {
	switch value {
	case models.BudgetStatusActive, models.BudgetStatusArchived, models.BudgetStatusCancelled:
		return true
	default:
		return false
	}
}

func isAlertRuleType(value string) bool {
	switch value {
	case models.AlertRuleTypePercentageUsed, models.AlertRuleTypeBudgetExceeded, models.AlertRuleTypeCategoryLimitWarning, models.AlertRuleTypeCategoryLimitExceeded:
		return true
	default:
		return false
	}
}

func isPercentage(value decimal.Decimal) bool {
	return value.GreaterThan(decimal.Zero) && value.LessThanOrEqual(decimal.NewFromInt(100))
}

func percentage(numerator, denominator decimal.Decimal) decimal.Decimal {
	if denominator.IsZero() {
		return decimal.Zero
	}
	return numerator.Div(denominator).Mul(decimal.NewFromInt(100)).Round(2)
}

func statusFor(usedPercentage, threshold decimal.Decimal) string {
	if usedPercentage.GreaterThanOrEqual(decimal.NewFromInt(100)) {
		return UsageStatusExceeded
	}
	if usedPercentage.GreaterThanOrEqual(threshold) {
		return UsageStatusWarning
	}
	return UsageStatusOnTrack
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
