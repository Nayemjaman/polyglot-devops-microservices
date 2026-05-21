package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/shopspring/decimal"
	"gorm.io/gorm"
)

const (
	BudgetStatusActive   = "active"
	BudgetStatusArchived = "archived"
	BudgetStatusDraft    = "draft"

	AlertRuleTypeBudget   = "budget"
	AlertRuleTypeCategory = "category"
)

type Budget struct {
	ID                uuid.UUID       `gorm:"type:uuid;primaryKey"`
	UserID            uuid.UUID       `gorm:"type:uuid;not null;index:idx_budgets_user_period"`
	Name              string          `gorm:"type:varchar(120);not null"`
	Year              int             `gorm:"not null;index:idx_budgets_user_period;check:year >= 1900 AND year <= 9999"`
	Month             int             `gorm:"not null;index:idx_budgets_user_period;check:month >= 1 AND month <= 12"`
	TotalBudgetAmount decimal.Decimal `gorm:"type:numeric(14,2);not null;check:total_budget_amount >= 0"`
	CurrencyCode      string          `gorm:"type:char(3);not null"`
	Status            string          `gorm:"type:varchar(20);not null;default:'active';check:status IN ('active','archived','draft')"`
	CreatedAt         time.Time       `gorm:"not null"`
	UpdatedAt         time.Time       `gorm:"not null"`

	Categories []BudgetCategory  `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
	AlertRules []BudgetAlertRule `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
	History    []BudgetHistory   `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
}

func (Budget) TableName() string {
	return "budgets"
}

func (b *Budget) BeforeCreate(_ *gorm.DB) error {
	if b.ID == uuid.Nil {
		b.ID = uuid.New()
	}
	return nil
}

type BudgetCategory struct {
	ID                       uuid.UUID       `gorm:"type:uuid;primaryKey"`
	BudgetID                 uuid.UUID       `gorm:"type:uuid;not null;uniqueIndex:idx_budget_categories_budget_category"`
	CategoryID               uuid.UUID       `gorm:"type:uuid;not null;uniqueIndex:idx_budget_categories_budget_category"`
	CategoryNameSnapshot     string          `gorm:"type:varchar(120);not null"`
	BudgetAmount             decimal.Decimal `gorm:"type:numeric(14,2);not null;check:budget_amount >= 0"`
	AlertThresholdPercentage decimal.Decimal `gorm:"type:numeric(5,2);not null;default:80;check:alert_threshold_percentage >= 0 AND alert_threshold_percentage <= 100"`
	CreatedAt                time.Time       `gorm:"not null"`
	UpdatedAt                time.Time       `gorm:"not null"`

	Budget Budget `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
}

func (BudgetCategory) TableName() string {
	return "budget_categories"
}

func (c *BudgetCategory) BeforeCreate(_ *gorm.DB) error {
	if c.ID == uuid.Nil {
		c.ID = uuid.New()
	}
	return nil
}

type BudgetAlertRule struct {
	ID                  uuid.UUID       `gorm:"type:uuid;primaryKey"`
	BudgetID            uuid.UUID       `gorm:"type:uuid;not null;uniqueIndex:idx_budget_alert_rules_budget_type"`
	RuleType            string          `gorm:"type:varchar(40);not null;uniqueIndex:idx_budget_alert_rules_budget_type;check:rule_type IN ('budget','category')"`
	ThresholdPercentage decimal.Decimal `gorm:"type:numeric(5,2);not null;check:threshold_percentage >= 0 AND threshold_percentage <= 100"`
	IsEnabled           bool            `gorm:"not null;default:true"`
	CreatedAt           time.Time       `gorm:"not null"`
	UpdatedAt           time.Time       `gorm:"not null"`

	Budget Budget `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
}

func (BudgetAlertRule) TableName() string {
	return "budget_alert_rules"
}

func (r *BudgetAlertRule) BeforeCreate(_ *gorm.DB) error {
	if r.ID == uuid.Nil {
		r.ID = uuid.New()
	}
	return nil
}

type BudgetHistory struct {
	ID                uuid.UUID       `gorm:"type:uuid;primaryKey"`
	BudgetID          uuid.UUID       `gorm:"type:uuid;not null;uniqueIndex:idx_budget_history_budget_snapshot"`
	TotalBudgetAmount decimal.Decimal `gorm:"type:numeric(14,2);not null;check:total_budget_amount >= 0"`
	TotalSpentAmount  decimal.Decimal `gorm:"type:numeric(14,2);not null;check:total_spent_amount >= 0"`
	RemainingAmount   decimal.Decimal `gorm:"type:numeric(14,2);not null"`
	UsedPercentage    decimal.Decimal `gorm:"type:numeric(5,2);not null;check:used_percentage >= 0 AND used_percentage <= 100"`
	SnapshotDate      time.Time       `gorm:"type:date;not null;uniqueIndex:idx_budget_history_budget_snapshot"`
	CreatedAt         time.Time       `gorm:"not null"`

	Budget Budget `gorm:"foreignKey:BudgetID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
}

func (BudgetHistory) TableName() string {
	return "budget_history"
}

func (h *BudgetHistory) BeforeCreate(_ *gorm.DB) error {
	if h.ID == uuid.Nil {
		h.ID = uuid.New()
	}
	return nil
}
