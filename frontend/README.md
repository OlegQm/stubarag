# Chat client for RAG project

## Main component

Use Streamlit as basic visual component.

- Use MongoDB as storage for chat history.
- We'll need to score answers.
- Good/bad answers will be used for fine-tuning of RAG.
- Integration should be done via docker (docker-compose)

## Chat APP flow

```mermaid
graph LR
	n2("MongoDB - History");
	n1[("History Menu")];
	n3["Current Conversation"];
	n4(("MainLLM"));
	n5((" User  "));
	n7{"User Review
	(optional)"};
	n2 -- Display All Conversations of User --> n1;
	n1 -- Select One --> n3;
	n4 -- Response --> n3;
	n5 -- User Query --> n3;
    n3 --- n7;
	n7 -- Save Conversation --> n2;
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
