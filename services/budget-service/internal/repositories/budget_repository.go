package repositories

import (
	"context"
	"errors"

	"github.com/google/uuid"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/models"
	"gorm.io/gorm"
)

type BudgetFilters struct {
	Year   *int
	Month  *int
	Status *string
}

type BudgetRepository struct {
	db *gorm.DB
}

func NewBudgetRepository(db *gorm.DB) *BudgetRepository {
	return &BudgetRepository{db: db}
}

func (r *BudgetRepository) Create(ctx context.Context, budget *models.Budget) error {
	return r.db.WithContext(ctx).Create(budget).Error
}

func (r *BudgetRepository) List(ctx context.Context, userID uuid.UUID, filters BudgetFilters, page, pageSize int) ([]models.Budget, int64, error) {
	query := r.db.WithContext(ctx).Model(&models.Budget{}).Where("user_id = ?", userID)
	query = applyBudgetFilters(query, filters)

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	var budgets []models.Budget
	err := query.Order("year DESC, month DESC, created_at DESC").
		Limit(pageSize).
		Offset((page - 1) * pageSize).
		Find(&budgets).Error
	return budgets, total, err
}

func (r *BudgetRepository) Get(ctx context.Context, userID, budgetID uuid.UUID) (models.Budget, error) {
	var budget models.Budget
	err := r.db.WithContext(ctx).
		Preload("Categories").
		Preload("AlertRules").
		Where("id = ? AND user_id = ?", budgetID, userID).
		First(&budget).Error
	return budget, normalizeNotFound(err)
}

func (r *BudgetRepository) GetByPeriod(ctx context.Context, userID uuid.UUID, year, month int) (models.Budget, error) {
	var budget models.Budget
	err := r.db.WithContext(ctx).
		Preload("Categories").
		Preload("AlertRules").
		Where("user_id = ? AND year = ? AND month = ? AND status = ?", userID, year, month, models.BudgetStatusActive).
		First(&budget).Error
	return budget, normalizeNotFound(err)
}

func (r *BudgetRepository) ExistsActiveForPeriod(ctx context.Context, userID uuid.UUID, year, month int, excludeBudgetID *uuid.UUID) (bool, error) {
	query := r.db.WithContext(ctx).Model(&models.Budget{}).
		Where("user_id = ? AND year = ? AND month = ? AND status = ?", userID, year, month, models.BudgetStatusActive)
	if excludeBudgetID != nil {
		query = query.Where("id <> ?", *excludeBudgetID)
	}

	var count int64
	if err := query.Count(&count).Error; err != nil {
		return false, err
	}
	return count > 0, nil
}

func (r *BudgetRepository) Update(ctx context.Context, budget *models.Budget) error {
	return r.db.WithContext(ctx).Save(budget).Error
}

func (r *BudgetRepository) CreateCategory(ctx context.Context, category *models.BudgetCategory) error {
	return r.db.WithContext(ctx).Create(category).Error
}

func (r *BudgetRepository) ListCategories(ctx context.Context, userID, budgetID uuid.UUID) ([]models.BudgetCategory, error) {
	var categories []models.BudgetCategory
	err := r.db.WithContext(ctx).
		Joins("JOIN budgets ON budgets.id = budget_categories.budget_id").
		Where("budget_categories.budget_id = ? AND budgets.user_id = ?", budgetID, userID).
		Order("budget_categories.created_at ASC").
		Find(&categories).Error
	return categories, err
}

func (r *BudgetRepository) GetCategory(ctx context.Context, userID, budgetID, categoryID uuid.UUID) (models.BudgetCategory, error) {
	var category models.BudgetCategory
	err := r.db.WithContext(ctx).
		Joins("JOIN budgets ON budgets.id = budget_categories.budget_id").
		Where("budget_categories.id = ? AND budget_categories.budget_id = ? AND budgets.user_id = ?", categoryID, budgetID, userID).
		First(&category).Error
	return category, normalizeNotFound(err)
}

func (r *BudgetRepository) UpdateCategory(ctx context.Context, category *models.BudgetCategory) error {
	return r.db.WithContext(ctx).Save(category).Error
}

func (r *BudgetRepository) DeleteCategory(ctx context.Context, category *models.BudgetCategory) error {
	return r.db.WithContext(ctx).Delete(category).Error
}

func (r *BudgetRepository) SumCategoryBudget(ctx context.Context, budgetID uuid.UUID, excludeCategoryID *uuid.UUID) (float64, error) {
	query := r.db.WithContext(ctx).Model(&models.BudgetCategory{}).Where("budget_id = ?", budgetID)
	if excludeCategoryID != nil {
		query = query.Where("id <> ?", *excludeCategoryID)
	}

	var total float64
	err := query.Select("COALESCE(SUM(budget_amount), 0)").Scan(&total).Error
	return total, err
}

func (r *BudgetRepository) CreateAlertRule(ctx context.Context, rule *models.BudgetAlertRule) error {
	return r.db.WithContext(ctx).Create(rule).Error
}

func (r *BudgetRepository) ListAlertRules(ctx context.Context, userID, budgetID uuid.UUID) ([]models.BudgetAlertRule, error) {
	var rules []models.BudgetAlertRule
	err := r.db.WithContext(ctx).
		Joins("JOIN budgets ON budgets.id = budget_alert_rules.budget_id").
		Where("budget_alert_rules.budget_id = ? AND budgets.user_id = ?", budgetID, userID).
		Order("budget_alert_rules.created_at ASC").
		Find(&rules).Error
	return rules, err
}

func (r *BudgetRepository) GetAlertRule(ctx context.Context, userID, budgetID, ruleID uuid.UUID) (models.BudgetAlertRule, error) {
	var rule models.BudgetAlertRule
	err := r.db.WithContext(ctx).
		Joins("JOIN budgets ON budgets.id = budget_alert_rules.budget_id").
		Where("budget_alert_rules.id = ? AND budget_alert_rules.budget_id = ? AND budgets.user_id = ?", ruleID, budgetID, userID).
		First(&rule).Error
	return rule, normalizeNotFound(err)
}

func (r *BudgetRepository) UpdateAlertRule(ctx context.Context, rule *models.BudgetAlertRule) error {
	return r.db.WithContext(ctx).Save(rule).Error
}

func (r *BudgetRepository) DeleteAlertRule(ctx context.Context, rule *models.BudgetAlertRule) error {
	return r.db.WithContext(ctx).Delete(rule).Error
}

func applyBudgetFilters(query *gorm.DB, filters BudgetFilters) *gorm.DB {
	if filters.Year != nil {
		query = query.Where("year = ?", *filters.Year)
	}
	if filters.Month != nil {
		query = query.Where("month = ?", *filters.Month)
	}
	if filters.Status != nil {
		query = query.Where("status = ?", *filters.Status)
	}
	return query
}

func normalizeNotFound(err error) error {
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return ErrRecordNotFound
	}
	return err
}
