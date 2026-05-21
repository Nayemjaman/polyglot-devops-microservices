package transaction

import "errors"

var ErrUnavailable = errors.New("transaction gRPC client unavailable")
