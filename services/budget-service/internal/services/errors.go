package services

import "errors"

var (
	ErrNotFound     = errors.New("resource not found")
	ErrConflict     = errors.New("resource already exists")
	ErrValidation   = errors.New("validation failed")
	ErrUnauthorized = errors.New("unauthorized")
	ErrDependency   = errors.New("dependency unavailable")
)

type ValidationError struct {
	Fields map[string][]string
}

func (e ValidationError) Error() string {
	return ErrValidation.Error()
}

func NewValidationError(fields map[string][]string) ValidationError {
	return ValidationError{Fields: fields}
}
