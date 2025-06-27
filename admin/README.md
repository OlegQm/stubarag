# Admin console

## GUI for administration

## How to use Admin MongoDB console?

- 'Knowledge base' page displays documents for embeddings
- 'History' page displays conversations of user with option to delete and learn from them
- To use 'Selection actions' buttons, select any number of rows in grid
- To access details of record, select row and click 'Details' under grid

Use Streamlit as basic visual component.

- Side menu with Sub-Pages should be accesible after start of the app and on every Sub-Page
- We'll need to score answers.
- Both Chat App and Admin App need to run simultaneously (different containers)

## Admin APP flow

```mermaid
graph LR
    n5["Chat App"]
	n1["Admin- History/Knowledge Base"]
    n2("MongoDB")
	n3("ChromaDB")
	n4["Details Page"]
    n5 -- Save Conversations --> n2;
    n2 -- Display List of Conversations/Documents --> n1;
    n1 -- Upload Documents --> n2;
    n1 -- Learn --> n3;
    n3 -- Unlearn --> n1;
    n1 -- Single Selected Item --> n4
```

## RAG LLM chain diagram

```mermaid
graph LR
	User -- User Query --> Conversation;
	Conversation -- Summarize Query for Embeddings Retrieval --> AuxLLM;
	AuxLLM -- Retrieve Relevant Data --> VectorDB;
	VectorDB -- Retrieved Contextual Data --> MainLLM;
	MainLLM -- Response --> Conversation;
	Conversation -- Save --> History;
	Conversation -- Context from Current Conversation --> MainLLM;
    AuxLLM -- Generate Title --> Conversation;
	KnowledgeBase -- Ingest Documents --> VectorDB;
	History -- Ingest Conversations --> VectorDB;
```
