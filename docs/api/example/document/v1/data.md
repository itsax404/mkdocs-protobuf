# Protocol Documentation: data.proto

## Package: `example.document.v1`

## Imports

- `user.proto`

## Messages

### Document

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| id | `string` | 1 | Unique identifier for the document |
| title | `string` | 2 | Document title |
| content | `string` | 3 | Document content |
| creator | [User](../../../user.md) | 5 | Creator of the document |

### DocumentChunk

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document_id | `string` | 1 | Parent document ID |
| content | `string` | 2 | Chunk content |
| embedding | `repeated float` | 3 | Chunk embedding |

### Query

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| text | `string` | 1 | Query text |
| user | [User](../../../user.md) | 3 | User making the query |

