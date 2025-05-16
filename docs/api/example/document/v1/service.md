# Protocol Documentation: service.proto

## Package: `example.document.v1`

## Imports

- `example/document/v1/data.proto`

## Messages

### DeleteDocumentRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document_id | `string` | 1 | Document ID to delete |

### DeleteDocumentResponse

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| success | `bool` | 1 | Whether the deletion was successful |

### GetDocumentRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document_id | `string` | 1 | Document ID to retrieve |

### IndexDocumentRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document | `Document` | 1 | Document to index |
| chunk | `bool` | 2 | Whether to chunk the document |

### IndexDocumentResponse

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document | `Document` | 1 | The indexed document |
| chunk_count | `int32` | 2 | Number of chunks created (if chunking was requested) |

### QueryRequest

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| query | `Query` | 1 | The query to perform |
| limit | `int32` | 2 | Maximum number of results to return |

### QueryResponse

* A single query result

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| results | `repeated QueryResult` | 1 | Query results |
| execution_time_ms | `int32` | 2 | Query execution time in milliseconds |

#### QueryResult (nested in QueryResponse)

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| document | `Document` | 1 | The document that matched |
| chunk | `DocumentChunk` | 2 | The document chunk that matched (if applicable) |
| score | `float` | 3 | The relevance score (higher is better) |

## Services

### DocumentService

* Index a document for future retrieval

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| IndexDocument | `IndexDocumentRequest` | `IndexDocumentResponse` | Index a document for future retrieval |
| Query | `QueryRequest` | `QueryResponse` | Query the document index with natural language |
| GetDocument | `GetDocumentRequest` | `Document` | Retrieve a document by ID |
| DeleteDocument | `DeleteDocumentRequest` | `DeleteDocumentResponse` | Delete a document from the index |

