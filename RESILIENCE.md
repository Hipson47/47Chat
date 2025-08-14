# Resilience Layer Configuration

The 47Chat backend includes a production-grade resilience layer for model clients (OpenAI and Ollama) with retries, circuit breakers, and comprehensive metrics.

## Environment Variables

Configure the resilience behavior using these environment variables:

### Retry Policy Settings

- `R_POLICY_MAX_RETRIES` (default: `3`) - Maximum number of retry attempts
- `R_POLICY_TIMEOUT_S` (default: `30.0`) - Per-attempt timeout in seconds
- `R_POLICY_BASE_BACKOFF_MS` (default: `200`) - Base backoff delay in milliseconds
- `R_POLICY_MAX_BACKOFF_MS` (default: `5000`) - Maximum backoff delay in milliseconds
- `R_POLICY_JITTER_MS` (default: `100`) - Random jitter range in milliseconds

### Circuit Breaker Settings

- `CB_THRESHOLD` (default: `5`) - Number of failures before opening circuit
- `CB_COOLDOWN_S` (default: `30`) - Recovery time before testing service again
- `CB_HALF_OPEN_SUCCESS` (default: `2`) - Successful requests needed to close circuit

## Example Configuration

```bash
# Conservative settings for production
export R_POLICY_MAX_RETRIES=5
export R_POLICY_TIMEOUT_S=45.0
export CB_THRESHOLD=3
export CB_COOLDOWN_S=60

# Aggressive settings for development
export R_POLICY_MAX_RETRIES=1
export R_POLICY_TIMEOUT_S=10.0
export CB_THRESHOLD=10
export CB_COOLDOWN_S=10
```

## Metrics

The following Prometheus metrics are exported at `/metrics`:

- `model_requests_total{client}` - Total requests made to each client
- `model_errors_total{client,kind}` - Errors by client and error type
- `model_timeouts_total{client}` - Timeout occurrences by client
- `model_request_duration_seconds{client}` - Request latency histogram
- `circuit_state{client}` - Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)

## Error Classification

Exceptions are automatically classified for metrics:

- `timeout` - Request timeout or asyncio.TimeoutError
- `rate_limit` - Rate limiting (429 errors)
- `network` - Connection, DNS, or network errors
- `server` - Server errors (5xx status codes)
- `other` - All other exceptions

## Circuit Breaker States

- **CLOSED** (0) - Normal operation, all requests allowed
- **HALF_OPEN** (1) - Testing recovery, limited requests allowed
- **OPEN** (2) - Fast-fail mode, requests blocked

The circuit breaker automatically transitions between states based on success/failure patterns and configured thresholds.
