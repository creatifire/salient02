#!/bin/bash

echo "🧪 Testing Enhanced Session Endpoint"
echo "======================================"

# Clean up any existing cookies
rm -f /tmp/session_cookies

echo -e "\n1️⃣ Testing without session (should return 404):"
curl -X GET http://localhost:8000/api/session \
  -H 'Accept: application/json' \
  --cookie-jar /tmp/session_cookies \
  --cookie /tmp/session_cookies \
  -w '\nHTTP Status: %{http_code}\n' \
  -s | jq '.' 2>/dev/null || cat

echo -e "\n2️⃣ Creating session by visiting main page:"
curl -X GET http://localhost:8000/ \
  --cookie-jar /tmp/session_cookies \
  -s -o /dev/null
echo "Session cookie created ✅"

echo -e "\n3️⃣ Testing with valid session (should show LLM config):"
curl -X GET http://localhost:8000/api/session \
  -H 'Accept: application/json' \
  --cookie /tmp/session_cookies \
  -w '\nHTTP Status: %{http_code}\n' \
  -s | jq '.' 2>/dev/null || cat

echo -e "\n4️⃣ Extracting just the LLM configuration:"
curl -X GET http://localhost:8000/api/session \
  -H 'Accept: application/json' \
  --cookie /tmp/session_cookies \
  -s | jq '.llm_configuration' 2>/dev/null || echo "jq not available"

echo -e "\n✅ Testing complete!"
echo "Expected new fields in response:"
echo "  - llm_configuration.provider"
echo "  - llm_configuration.model" 
echo "  - llm_configuration.temperature"
echo "  - llm_configuration.max_tokens"
echo "  - llm_configuration.config_sources"
echo "  - llm_configuration.last_usage"
