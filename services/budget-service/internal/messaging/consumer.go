package messaging

import (
	"context"
	"encoding/json"
	"log/slog"

	amqp "github.com/rabbitmq/amqp091-go"
)

type TransactionEvent struct {
	EventType       string `json:"event_type"`
	UserID          string `json:"user_id"`
	TransactionID   string `json:"transaction_id"`
	Type            string `json:"type"`
	Amount          string `json:"amount"`
	CurrencyCode    string `json:"currency_code"`
	TransactionDate string `json:"transaction_date"`
}

type Consumer struct {
	url      string
	exchange string
	queue    string
	logger   *slog.Logger
}

func NewConsumer(url, exchange, queue string, logger *slog.Logger) *Consumer {
	return &Consumer{url: url, exchange: exchange, queue: queue, logger: logger}
}

func (c *Consumer) Start(ctx context.Context) {
	go c.run(ctx)
}

func (c *Consumer) run(ctx context.Context) {
	conn, err := amqp.Dial(c.url)
	if err != nil {
		c.logger.Warn("rabbitmq unavailable; budget transaction consumer disabled", "error", err)
		return
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		c.logger.Warn("failed to open rabbitmq channel", "error", err)
		return
	}
	defer ch.Close()

	if err := ch.ExchangeDeclare(c.exchange, "topic", true, false, false, false, nil); err != nil {
		c.logger.Warn("failed to declare rabbitmq exchange", "error", err)
		return
	}
	q, err := ch.QueueDeclare(c.queue, true, false, false, false, nil)
	if err != nil {
		c.logger.Warn("failed to declare rabbitmq queue", "error", err)
		return
	}
	if err := ch.QueueBind(q.Name, "transaction.*", c.exchange, false, nil); err != nil {
		c.logger.Warn("failed to bind rabbitmq queue", "error", err)
		return
	}
	msgs, err := ch.Consume(q.Name, "", false, false, false, false, nil)
	if err != nil {
		c.logger.Warn("failed to start rabbitmq consumer", "error", err)
		return
	}

	c.logger.Info("budget transaction event consumer started")
	for {
		select {
		case <-ctx.Done():
			return
		case msg, ok := <-msgs:
			if !ok {
				return
			}
			var event TransactionEvent
			if err := json.Unmarshal(msg.Body, &event); err != nil {
				c.logger.Warn("invalid transaction event", "error", err)
				_ = msg.Nack(false, false)
				continue
			}
			c.logger.Info(
				"received transaction event for budget refresh",
				"event_type", event.EventType,
				"user_id", event.UserID,
				"transaction_id", event.TransactionID,
			)
			_ = msg.Ack(false)
		}
	}
}
