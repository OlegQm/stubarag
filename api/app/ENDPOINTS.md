This mini-documentation explains (with examples) how to use the new endpoints.

All endpoints are divided into 4 sections:

1. **`common`**: General-purpose endpoints:
  - `/common/clear_chroma_collection`
  - `/common/clear_mongo_collection`
  - `/common/delete_one_chroma_record`
  - `/common/delete_one_mongo_record`
  - `/common/get_mongo_records`

2. **`faq`**: Endpoints designed to handle FAQs (frequently asked questions):
  - `/faq/load_records`
  - `/faq/random_questions`
  - `/faq/similar_questions`

3. **`webscraper`**: Endpoints for performing web scraping on a link:
  - `/webscraper/webscraper`
  - `/webscraper/webscraper_batch`
  - `/webscraper/get_chunks`

4. **`tests`**: Endpoints for testing and managing QnA data:
  - `/testing/start_llm_test` (CURRENTLY UNAVAILABLE)
  - `/testing/upload_records`
  - `/testing/get_records`
  - `/testing/delete_records`

The response of each of these endpoints (except `/faq/random_questions` and `/faq/similar_questions`) contains 2 parameters: `status`, denoting success / non-success. If the status is 201 (in case of data loading) or 200 (for all other cases), the operation was successful, in other cases - unsuccessful. If the operation failed, the reason for the failure can be seen in the `message` parameter.

Let's break down the endpoints of each section in more detail:

## 1. `common`:

## 1.1. `/common/clear_chroma_collection`:
Clears any ChromaDB collection. Takes one argument in the body of the request: `collection_name` is the name of the collection to be cleared. Example Usage:

### Query (method - DELETE).
https://prod.agentkovac.sk/api/common/clear_chroma_collection

### Request body (format - JSON):
{'collection_name': 'faq'}

## 1.2. `/common/clear_mongo_collection`:
Clears any MongoDB collection. Takes one argument in the request body: `collection_name` is the name of the collection to be cleared. Example Usage:

### Query (method - DELETE).
https://prod.agentkovac.sk/api/common/clear_mongo_collection

### Request body (format - JSON):
{'collection_name': 'faq'}

## 1.3. `/common/delete_one_chroma_record`:

Deletes a single record in the ChromaDB `collection_name` collection by `filter`.

### Query (method - DELETE).
https://prod.agentkovac.sk/api/common/delete_one_chroma_record

### `filter`:

The filter to use to find the record to delete. This parameter is passed in the body of the request. This is actually the key of the record to be deleted, the keys and example queries for the `faq` and `webscraper` collections are shown below:

### For the `faq` collection:
- key: `question`;
- request body (format - JSON):
    `{"collection_name": "faq", "filter": {"question": "What is ChromaDB?"}}`

### Lifehack:

If you don't remember the exact question, use the `/faq/similar_questions` endpoint by passing the question to it and setting `top=1`. You should then get the exact question, which you can use to remove it from the collection.

### For the `webscraper` collection:
- key: `url`;
- request body (format - JSON):
    `{"collection_name": "webscraper", "filter": {"url": "https://www.example.com"}}`

## 1.4. `/common/delete_one_mongo_record`:

Deletes a record from the `collection_name` MongoDB collection by `filter`.

### Query (method - DELETE).
https://prod.agentkovac.sk/api/common/delete_one_mongo_record

### Request body (format - JSON):
{"collection_name": "faq", "filter": {"_id": "ab1289sna9a9a999"}}

## 1.5. `/common/get_mongo_records`:

This endpoint searches for documents in the specified MongoDB collection using the provided filter. It returns a list of matching records. If no records are found, HTTP 404 is returned.

### Request (method - GET)
```
https://prod.agentkovac.sk/api/common/get_mongo_records?collection_name=<collection name>
```

### Request Details:
- **HTTP Method:** GET
- **URL:** `/common/get_mongo_records`
- **Query Parameter:**
    - `collection_name` (string): Name of the MongoDB collection.
- **Request Body (format - JSON):**
    A JSON object containing the filter criteria. For example:
    ```json
    {
        "filter": {"pattern_or_llm": "pattern"}
    }
    ```

### Example Usage:

#### Query:
```
https://prod.agentkovac.sk/api/common/get_mongo_records?collection_name=qna
```
#### Body:
```json
{
    "filter": {"pattern_or_llm": "pattern"}
}
```

### Response:

The response returns a JSON object with the following fields:
- **message**: A descriptive message of the outcome.
- **status**: The HTTP status code.
- **records**: A list of matching documents, with ObjectId fields converted to strings for JSON serialization.

**Example:**
```json
{
    "status": 200,
    "message": "1 record(s) retrieved successfully from collection 'users'.",
    "records": [
        {
            "_id": "607f1f77bcf86cd799439011",
            "name": "John Doe",
            "age": 30,
            "status": "active"
        }
    ]
}
```

### Errors:

If an error occurs, the response includes an appropriate message:
- **400**: Bad Request (if the collection name is empty or the filter is not a non-empty dictionary).
- **404**: Not Found (if no records match the filter criteria).
- **500**: Internal Server Error (if a database or unexpected error occurs).

### Notes:
- The filter must be provided in the request body as a non-empty JSON object.
- The `collection_name` is provided as a query parameter.
- Retrieved documents have ObjectId fields automatically converted to strings for proper JSON serialization.

## 1.6. DELETE /common/drop_chroma_collection
```
URL: https://prod.agentkovac.sk/api/common/drop_chroma_collection?collection_name=your_collection_name
```
Description: Permanently deletes the named ChromaDB collection (no recreation).
Response:
  - status 200 on success; 400/404/500 on error
  - message explains the result

## 1.7. DELETE /common/drop_mongo_collection
```
URL: https://prod.agentkovac.sk/api/common/drop_mongo_collection?collection_name=your_collection_name
```
Description: Permanently drops the named MongoDB collection.
Response:
  - status 200 on success; 400/404/500 on error
  - message explains the result


## 2. `faq`:

## 2.1. `/faq/load_records`:

Allows you to load data into the `faq` collection (question (`question`), answer (`answer`), short description (`doc`, may be omitted) and url (`url` - where the answer is taken from, may be omitted)). Example usage:

### Request (method - POST)
https://prod.agentkovac.sk/api/faq/load_records

### Request body (format - JSON):
```json
[
    {
        'query': 'What is FastAPI?',
        'answer': 'FastAPI is a modern web framework for Python.',
        'doc': 'FastAPI Introduction',
        'url': 'http://fastapi.tiangolo.com/'
    },
    {
        'question': 'What is Chroma DB?',
        'answer': 'Chroma DB is a vector database for AI and embeddings.',
        'doc': 'Chroma Documentation',
        'url': 'http://chroma.com/docs/'
    }
]
```

## 2.2. `/faq/random_questions`:

Returns one or more random questions from the `faq` collection (in the body of the query, you must specify the arguments `collection` - the name of the collection and `random` - the desired number of queries. Example of use:

### Query (method - POST)
https://prod.agentkovac.sk/api/faq/delete_one_chroma_record

### Request body (format - JSON):
```json
[{'collection': 'faq', 'random': 2}]
```

### !!!CAUTION!!! Method may return fewer questions than `random` if there are not enough questions in the collection.

#### The response contains a list of results with the following parameters:
`result` - list of results containing `question` - question, `answer` - answer, `no` - question number, `doc` - helper string, `url` - link to the document with answers;
`status` - number denoting success (200) / non-success of the operation;
`message` - a string to help identify the cause of the problem if the operation is not successful.

## 2.3. `/faq/similar_questions`:

Returns the `top` of similar `search` questions from the `collection` that are similar by at least `similarity` percent. Example Usage:

### Query (method is POST)
https://prod.agentkovac.sk/api/faq/similar_questions

### Request body (format - JSON):
```json
[{'search': 'What is FastAPI?', 'collection': 'faq', 'top': 1, 'similarity': 0.985}]
```

### !!!CAUTION!!! The method may return fewer questions than `top` if there are not enough questions in the collection or if there are not enough questions that are similar to `similarity` percentages on `search`.

### The format of the answer is similar to the format from `/faq/random_questions`.

## 3. `webscraper`:

## 3.1. `/webscraper/webscraper`:

Takes the `url`, `description` (optional, default="Brief description of the webpage.") and `owner` (optional, default="FEI STU") of a page as input and stores all of its static text in MongoDB and, if changes were detected on the page, updates the entry in ChromaDB as well. Example usage:

### Request (method - POST)
https://prod.agentkovac.sk/api/webscraper/webscraper

### Request body (format - JSON):
```json
{"url": "https://www.stuba.sk/sk/zahranicne-partnerske-institucie.html?page_id=204", "description": "Stranka o zahranicnom studiu", "owner": "Mato"}
```

### !!!CAUTION!!! The response may take a long time

## 3.2. `/webscraper/webscraper_batch`:

Allows scraping (collecting static information) for a list of pages. Works the same as `/webscraper/webscraper` but for multiple pages.

### Request (method - POST)
https://prod.agentkovac.sk/api/webscraper/webscraper_batch

### Request body (format - JSON):
```json
[
    {"url": "https://www.stuba.sk/sk/eulist.html?page_id=14972"},
    {"url": "https://www.stuba.sk/sk/vyskume/sluzby-vyskumu.html?page_id=641"}
]
```

### Returns a JSON object with:

- status (int): Overall HTTP status code (200 = all success, 207 = partial success, 500 = all failed, etc.)
- message (string): Operation result message.
- is_webpage_updated (array): For each input URL, an object mapping the URL to a two-element array:
[HTTP status code, status message] (e.g., [200, "Page content successfully extracted"]).

### Example response:

```json
{
  "status": 207,
  "message": "Partial success: some pages failed to process.",
  "is_webpage_updated": [
    {
      "https://example.com/page1": [200, "Page content successfully extracted"]
    },
    {
      "https://example.com/page2": [408, "Request timed out"]
    }
  ]
}
```

## 3.3. `/webscraper/get_chunks`:

An endpoint designed to retrieve all parts of text (`chunks`) from the `webscrapper` collection in ChromaDB for a particular page (for a particular `url`).

### Request (method - POST)

https://prod.agentkovac.sk/api/webscraper/get_chunks

### Request body (format - JSON):

```json
{"url": "https://www.stuba.sk/sk/eulist.html?page_id=14972"}
```

# `/retrieve_data`

### When you use it in the context of `webscrapper`, pass the `url` of the page to the `filename` argument, and pass the page owner's name to `user`. The rest is unchanged.

## 4. `tests`:

<!-- ## 4.1. `/testing/start_llm_test` (CURRENTLY UNAVAILABLE)

This endpoint asynchronously executes a suite of tests using pytest and captures both the detailed test results and the log output. It leverages asynchronous execution to run the tests in a non-blocking manner. In addition to returning a report containing custom test results, the endpoint archives the results in the MongoDB collection `archive_tests`. The archived data includes the latest release (fetched from the QnA collection), the pytest log, and a test summary indicating the count of valid answers relative to the total number of tests.

### Example Usage (method - GET)
```
https://prod.agentkovac.sk/api/testing/start_llm_test
```

### Request Details:
- **HTTP Method:** GET
- **URL:** `/testing/start_llm_test`
- **Description:**  
    Initiates the execution of a predefined test suite for LLM functionality. No request body or query parameters are required.

### Response:

The response returns a JSON object with the following fields:
- **message:** A string indicating the status of the operation (e.g., "Operation completed successfully").
- **status:** An integer representing the HTTP status code.
- **custom_results:** An array containing the outcomes of the executed tests. Each entry provides details about individual test results.
- **pytest_log:** A string containing the concatenated log output from pytest, detailing the execution of the test suite.
- **test_summary:** A string in the format "valid_count/total_count", representing the number of tests that produced valid answers compared to the total number of tests.

**Example Response:**
```json
{
    "message": "Operation completed successfully",
    "status": 200,
    "custom_results": [
        {"Koľko kreditov musím získať, aby som získal bakalársky titul?": "answer was invalid"},
        {"Kto je dekanom FEI STU?": "answer was invalid"}
    ],
    "pytest_log": "app/llm_tests/llm_test_main.py::test_example: passed\n...",
    "test_summary": "0/2"
}
```

### Errors:
If an error occurs during test execution or database operations, the response includes:
- **500:** Internal Server Error (with an appropriate error message).

### Notes:
- The endpoint uses `asyncio.to_thread` to execute the tests asynchronously in a separate thread.
- A custom log capture plugin (`CaptureLogPlugin`) is employed to gather the pytest log output.
- Test results are cleared prior to execution to ensure fresh output.
- The results, along with the latest release and a test summary, are archived in the `archive_tests` collection in MongoDB.  
- If the QnA collection is empty (and thus no release is found), a partial response (206) is returned, indicating that archiving was not possible.
- The service gracefully handles exceptions by returning a 500 error with an appropriate error message.

--- -->

## 4.2. `/testing/upload_records`

This endpoint enables uploading QnA data to a MongoDB collection with transactional support. All operations are executed atomically to ensure data integrity.

### How the Endpoint Works

#### 1. Input Validation

- **Request Parameters:**
  - **qna:**
    A dictionary where each key is a question (string) and each value is a dictionary with one or two keys:
    - **pattern** (optional): A string answer for the "pattern" type.
    - **llm** (optional): A string answer for the "llm" type.
    Each question must contain at least one non-empty value.

- If the input structure is invalid (e.g., `qna` is not a non-empty dictionary), a **400 Bad Request** status is returned.

#### 3. Processing QnA Entries

After validation and potential archiving:
- **Validation:**
  For each question, the system checks:
  - The question is a non-empty string.
  - The value is a dictionary containing 1 or 2 allowed keys (`"pattern"` and/or `"llm"`).
  - All values are strings.

- **Insertion:**
  - For each valid answer type ("pattern" or "llm") with a non-empty value:
    - If no existing record is found for the question and answer type, a new record is inserted with:
      - `question`: the question text,
      - `answer`: the answer value,
      - `pattern_or_llm`: either `"pattern"` or `"llm"`,
    - If the record already exists, it's counted as a duplicate.

- **Error Handling:**
  Invalid entries (e.g., empty questions, missing keys, or empty answers) are recorded and reported.

#### 4. Response Construction

After processing:
- If all records are inserted successfully, **200 OK** is returned.
- If there are invalid or duplicate records but at least one successful insertion, **206 Partial Content** is returned.
- If no record was inserted, **500 Internal Server Error** is returned.
- The message includes:
  - Number of successfully inserted records,
  - List of duplicates (if any),
  - List of validation errors (if any),

#### 5. Transactional Execution

All operations are executed inside a MongoDB session with transaction support, ensuring either full success or complete rollback in case of an error.

### Example Request (POST)

**URL:**
```
https://prod.agentkovac.sk/api/testing/upload_records
```

**Request Body (JSON):**
```json
{
  "qna": {
    "What is the capital of France?": {
      "pattern": "Paris",
      "llm": "The capital of France is Paris"
    },
    "What is the largest planet?": {
      "pattern": "Jupiter"
    }
  }
}
```

### Parameters

- **qna:**
  - **Type:** dictionary
  - **Description:**
    Keys are questions (strings). Values are dictionaries with one or both of the following keys:
    - **pattern:** (string, optional) Answer for "pattern" type.
    - **llm:** (string, optional) Answer for "llm" type.
    At least one key must have a non-empty value.

- **release:**
  - **Type:** string
  - **Description:**
    A version in the format `vX.Y` (e.g., `"v1.0"`).

### Example Responses

#### Success
```json
{
  "status": 200,
  "message": "2/2 QnA entries inserted successfully.
}
```

#### Partial Success
```json
{
  "status": 206,
  "message": "Some entries contain errors:\n[List of errors]\n\n2/3 QnA entries inserted successfully.\n\nThe following questions already exist:\nWhat is the capital of France? (pattern)"
}
```

#### Bad Request
```json
{
  "status": 400,
  "message": "Invalid input: 'qna' must be a non-empty dictionary."
}
```

#### Internal Server Error
```json
{
  "status": 500,
  "message": "Database error: <error details>"
}
```

---

## 4.3. `/testing/get_records`:

This endpoint searches for documents in the specified MongoDB collection using the provided filter. It returns a list of matching records. If no records are found, HTTP 404 is returned.

### Request (method - GET)
```
https://prod.agentkovac.sk/api/testing/get_records
```

### Request Details:
- **HTTP Method:** GET
- **URL:** `/testing/get_records`
- **Request Body (format - JSON):**
    A JSON object containing the filter criteria. For example:
    ```json
    {
        "filter": {"pattern_or_llm": "pattern"}
    }
    ```

### Example Usage:

#### Query:
```
https://prod.agentkovac.sk/api/testing/get_records
```
#### Body:
```json
{
    "filter": {"pattern_or_llm": "pattern"}
}
```

### Response:

The response returns a JSON object with the following fields:
- **message**: A descriptive message of the outcome.
- **status**: The HTTP status code.
- **records**: A list of matching documents, with ObjectId fields converted to strings for JSON serialization.

**Example:**
```json
{
    "status": 200,
    "message": "1 record(s) retrieved successfully from collection 'users'.",
    "records": [
        {
            "_id": "607f1f77bcf86cd799439011",
            "name": "John Doe",
            "age": 30,
            "status": "active"
        }
    ]
}
```

### Errors:

If an error occurs, the response includes an appropriate message:
- **400**: Bad Request (if the collection name is empty or the filter is not a non-empty dictionary).
- **404**: Not Found (if no records match the filter criteria).
- **500**: Internal Server Error (if a database or unexpected error occurs).

### Notes:
- The filter must be provided in the request body as a non-empty JSON object.
- Retrieved documents have ObjectId fields automatically converted to strings for proper JSON serialization.

## 4.4. `/testing/delete_records`:

Deletes a record from the `qna` MongoDB collection by `filter`.

### Query (method - DELETE).
https://prod.agentkovac.sk/api/testing/delete_records

### Request body (format - JSON):
```json
{"filter": {"_id": "ab1289sna9a9a999"}}
```
