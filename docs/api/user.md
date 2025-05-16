# Protocol Documentation: user.proto

## Package: `user`

## Messages

### CreateUserRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| user | `User` | 1 | The user to create |

### DeleteUserRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| user_id | `string` | 1 | The ID of the user to delete |

### DeleteUserResponse

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| success | `bool` | 1 | Whether the deletion was successful |

### GetUserRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| user_id | `string` | 1 | The ID of the user to retrieve |

### Role

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| id | `string` | 1 | Unique identifier for the role |
| name | `string` | 2 | Name of the role |
| permissions | `repeated string` | 3 | Permissions associated with this role |

### UpdateUserRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| user_id | `string` | 1 | The user ID to update |
| user | `User` | 2 | The new user data |

### User

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| id | `string` | 1 | Unique identifier for the user |
| name | `string` | 2 | User's full name |
| email | `string` | 3 | User's email address |
| profile | `Profile` | 4 | User's profile information |
| roles | `repeated Role` | 5 | User roles |
| status | `Status` | 6 | Current user status |

#### Profile (nested in User)

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| avatar_url | `string` | 1 | Profile picture URL |
| bio | `string` | 2 | User bio information |

## Enums

### Status

| Name | Number | Description |
|------|--------|-------------|
| UNKNOWN | 0 | Status is unknown |
| ACTIVE | 1 | User is active |
| INACTIVE | 2 | User is inactive |
| SUSPENDED | 3 | User is suspended |

## Services

### UserService

* Creates a new user

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| CreateUser | `CreateUserRequest` | `User` | Creates a new user |
| GetUser | `GetUserRequest` | `User` | Gets a user by ID |
| UpdateUser | `UpdateUserRequest` | `User` | Updates an existing user |
| DeleteUser | `DeleteUserRequest` | `DeleteUserResponse` | Deletes a user |

