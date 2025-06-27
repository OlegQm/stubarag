# RAG API Mini-Documentation

This mini-documentation explains (with examples) how to use the RAG endpoint.

## 1.1. `/get_rag_answer`:

This endpoint provides an AI-generated response based on provided conversation history. It optionally enhances the user's query for improved clarity and context before processing.

### Request (method - POST)
```
https://prod.agentkovac.sk/llm/get_rag_answer
```

### Request body (format - JSON):
```json
[
    {
        "role": "user",
        "content": "Kto je dekan?"
    }
]
```

### Parameters:
- `conversation_content`: List of dictionaries, each containing:
  - `role`: Must be either `"user"` or `"assistant"`.
  - `content`: The message text.

### Example Usage:

#### Simple request (without enhancement)

##### Query:
```
https://prod.agentkovac.sk/llm/get_rag_answer?needs_enhancement=False
```
##### Body:
```json
[
    {
        "role": "user",
        "content": "Kto je dekan?"
    }
]
```

#### Request with enhancement

##### Query:
```
https://prod.agentkovac.sk/llm/get_rag_answer
```
##### Body:
```json
[
    {
        "role": "user",
        "content": "Ake existuju bonusy pre tehotne ukrajinky na FEI STU?"
    }
]
```

### Response:

The response contains:
- `answer`: The AI-generated response to the query.

Example:
```json
{
    "answer": "Neural networks are a subset of machine learning algorithms inspired by the structure of the human brain. They are used in deep learning to recognize patterns in data."
}
```

### Errors:

If an error occurs, the response includes an appropriate message:
- `400`: Invalid input format.
- `422`: JSON decoding error.
- `500`: Internal server error.

### Notes:
- Ensure the `conversation_content` format is correct.
- Enhanced queries typically provide more accurate and contextually relevant responses.
