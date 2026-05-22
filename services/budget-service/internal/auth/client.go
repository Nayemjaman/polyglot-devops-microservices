package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
)

type User struct {
	ID        uuid.UUID
	FirstName string
	LastName  string
}

type Client struct {
	baseURL string
	http    *http.Client
}

type meResponse struct {
	User struct {
		ID        string `json:"id"`
		FirstName string `json:"first_name"`
		LastName  string `json:"last_name"`
	} `json:"user"`
}

func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: strings.TrimRight(baseURL, "/"),
		http:    &http.Client{Timeout: 5 * time.Second},
	}
}

func (c *Client) Verify(ctx context.Context, authHeader string) (User, error) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		user, err := c.verifyOnce(ctx, authHeader)
		if err == nil || err == ErrInvalidToken {
			return user, err
		}
		lastErr = err
		if attempt < 2 {
			timer := time.NewTimer(time.Duration(100*(1<<attempt)) * time.Millisecond)
			select {
			case <-ctx.Done():
				timer.Stop()
				return User{}, ctx.Err()
			case <-timer.C:
			}
		}
	}
	return User{}, lastErr
}

func (c *Client) verifyOnce(ctx context.Context, authHeader string) (User, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/auth/me", nil)
	if err != nil {
		return User{}, fmt.Errorf("create auth request: %w", err)
	}
	req.Header.Set("Authorization", strings.TrimSpace(authHeader))

	resp, err := c.http.Do(req)
	if err != nil {
		return User{}, fmt.Errorf("call auth service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		if resp.StatusCode >= 500 {
			return User{}, fmt.Errorf("auth service returned status %d", resp.StatusCode)
		}
		return User{}, ErrInvalidToken
	}

	var payload meResponse
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return User{}, fmt.Errorf("decode auth response: %w", err)
	}

	userID, err := uuid.Parse(payload.User.ID)
	if err != nil {
		return User{}, fmt.Errorf("parse auth user id: %w", err)
	}

	return User{ID: userID, FirstName: payload.User.FirstName, LastName: payload.User.LastName}, nil
}
