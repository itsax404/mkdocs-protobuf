# Protocol Documentation: test.proto

## Package: `test`## Imports 

- `user.proto`

## Messages

### TestMessage

Nested message for test results

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| name | `string` | 1 | Name of the test |
| description | `string` | 2 | Description of the test |
| status_code | `int32` | 3 | Status code |
| user_id | `string` | 4 | Reference to user |
| result | `TestResult` | 4 | The test result |
| test | `string` | 5 |  |

#### TestResult (nested in TestMessage)

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| passed | `bool` | 1 | Whether the test passed |
| score | `int32` | 2 | Test score |
| notes | `string` | 3 | Additional notes |

## Services

### TestService

* Run a test

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| RunTest | `TestMessage` | `TestMessage.TestResult` | * Run a test |
| GetStatus | `TestMessage` | `TestMessage` | Get test status |

