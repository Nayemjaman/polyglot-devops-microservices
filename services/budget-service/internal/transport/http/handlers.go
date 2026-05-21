package http

import (
	"errors"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/api"
	"github.com/nayem/polyglot-devops-microservices/services/budget-service/internal/services"
)

const userIDContextKey = "user_id"

type budgetHandler struct {
	service *services.BudgetService
}

func newBudgetHandler(service *services.BudgetService) *budgetHandler {
	return &budgetHandler{service: service}
}

func (h *budgetHandler) createBudget(ctx *gin.Context) {
	var input services.CreateBudgetInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.CreateBudget(ctx.Request.Context(), currentUserID(ctx), input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.Created(ctx, "Budget created successfully", out)
}

func (h *budgetHandler) listBudgets(ctx *gin.Context) {
	filters := services.BudgetListFilters{
		Page:     queryInt(ctx, "page", 1),
		PageSize: queryInt(ctx, "page_size", 20),
		Year:     optionalQueryInt(ctx, "year"),
		Month:    optionalQueryInt(ctx, "month"),
		Status:   optionalQueryString(ctx, "status"),
	}
	out, pagination, err := h.service.ListBudgets(ctx.Request.Context(), currentUserID(ctx), filters)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.Paginated(ctx, "Budgets fetched successfully", out, pagination)
}

func (h *budgetHandler) getBudget(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	out, err := h.service.GetBudget(ctx.Request.Context(), currentUserID(ctx), budgetID)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget fetched successfully", out)
}

func (h *budgetHandler) updateBudget(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	var input services.UpdateBudgetInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.UpdateBudget(ctx.Request.Context(), currentUserID(ctx), budgetID, input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget updated successfully", out)
}

func (h *budgetHandler) deleteBudget(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	if err := h.service.ArchiveBudget(ctx.Request.Context(), currentUserID(ctx), budgetID); err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget deleted successfully", nil)
}

func (h *budgetHandler) createCategory(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	var input services.CreateCategoryInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.CreateCategory(ctx.Request.Context(), currentUserID(ctx), budgetID, input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.Created(ctx, "Budget category created successfully", out)
}

func (h *budgetHandler) listCategories(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	out, err := h.service.ListCategories(ctx.Request.Context(), currentUserID(ctx), budgetID)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget categories fetched successfully", out)
}

func (h *budgetHandler) updateCategory(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	categoryID, ok := pathUUID(ctx, "category_id")
	if !ok {
		return
	}
	var input services.UpdateCategoryInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.UpdateCategory(ctx.Request.Context(), currentUserID(ctx), budgetID, categoryID, input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget category updated successfully", out)
}

func (h *budgetHandler) deleteCategory(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	categoryID, ok := pathUUID(ctx, "category_id")
	if !ok {
		return
	}
	if err := h.service.DeleteCategory(ctx.Request.Context(), currentUserID(ctx), budgetID, categoryID); err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget category deleted successfully", nil)
}

func (h *budgetHandler) createAlertRule(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	var input services.CreateAlertRuleInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.CreateAlertRule(ctx.Request.Context(), currentUserID(ctx), budgetID, input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.Created(ctx, "Alert rule created successfully", out)
}

func (h *budgetHandler) listAlertRules(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	out, err := h.service.ListAlertRules(ctx.Request.Context(), currentUserID(ctx), budgetID)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Alert rules fetched successfully", out)
}

func (h *budgetHandler) updateAlertRule(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	ruleID, ok := pathUUID(ctx, "rule_id")
	if !ok {
		return
	}
	var input services.UpdateAlertRuleInput
	if !bindJSON(ctx, &input) {
		return
	}
	out, err := h.service.UpdateAlertRule(ctx.Request.Context(), currentUserID(ctx), budgetID, ruleID, input)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Alert rule updated successfully", out)
}

func (h *budgetHandler) deleteAlertRule(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	ruleID, ok := pathUUID(ctx, "rule_id")
	if !ok {
		return
	}
	if err := h.service.DeleteAlertRule(ctx.Request.Context(), currentUserID(ctx), budgetID, ruleID); err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Alert rule deleted successfully", nil)
}

func (h *budgetHandler) monthlyStatus(ctx *gin.Context) {
	year := queryInt(ctx, "year", 0)
	month := queryInt(ctx, "month", 0)
	out, err := h.service.GetMonthlyStatus(ctx.Request.Context(), currentUserID(ctx), year, month)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Monthly budget status fetched successfully", out)
}

func (h *budgetHandler) categoryWiseStatus(ctx *gin.Context) {
	year := queryInt(ctx, "year", 0)
	month := queryInt(ctx, "month", 0)
	out, err := h.service.GetCategoryWiseStatus(ctx.Request.Context(), currentUserID(ctx), year, month)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Category-wise budget status fetched successfully", out)
}

func (h *budgetHandler) budgetUsage(ctx *gin.Context) {
	budgetID, ok := pathUUID(ctx, "id")
	if !ok {
		return
	}
	out, err := h.service.GetBudgetUsage(ctx.Request.Context(), currentUserID(ctx), budgetID)
	if err != nil {
		writeServiceError(ctx, err)
		return
	}
	api.OK(ctx, "Budget usage fetched successfully", out)
}

func bindJSON(ctx *gin.Context, out interface{}) bool {
	if err := ctx.ShouldBindJSON(out); err != nil {
		api.Error(ctx, http.StatusBadRequest, "Validation failed", map[string][]string{"body": {"Invalid request body"}})
		return false
	}
	return true
}

func pathUUID(ctx *gin.Context, name string) (uuid.UUID, bool) {
	id, err := uuid.Parse(ctx.Param(name))
	if err != nil {
		api.Error(ctx, http.StatusBadRequest, "Validation failed", map[string][]string{name: {"Invalid UUID"}})
		return uuid.Nil, false
	}
	return id, true
}

func currentUserID(ctx *gin.Context) uuid.UUID {
	value, _ := ctx.Get(userIDContextKey)
	userID, _ := value.(uuid.UUID)
	return userID
}

func queryInt(ctx *gin.Context, name string, fallback int) int {
	value := ctx.Query(name)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return parsed
}

func optionalQueryInt(ctx *gin.Context, name string) *int {
	value := ctx.Query(name)
	if value == "" {
		return nil
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return nil
	}
	return &parsed
}

func optionalQueryString(ctx *gin.Context, name string) *string {
	value := ctx.Query(name)
	if value == "" {
		return nil
	}
	return &value
}

func writeServiceError(ctx *gin.Context, err error) {
	var validation services.ValidationError
	switch {
	case errors.As(err, &validation):
		api.Error(ctx, http.StatusBadRequest, "Validation failed", validation.Fields)
	case errors.Is(err, services.ErrNotFound):
		api.Error(ctx, http.StatusNotFound, "Resource not found", nil)
	case errors.Is(err, services.ErrDependency):
		api.Error(ctx, http.StatusBadGateway, "Transaction service unavailable", nil)
	default:
		api.Error(ctx, http.StatusInternalServerError, "Internal server error", nil)
	}
}
