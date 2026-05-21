package transaction

import "encoding/json"

func jsonMarshal(value interface{}) ([]byte, error) {
	return json.Marshal(value)
}
