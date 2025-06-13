# Agent Kovac 

Agent Kovac is synonym for matrix fictional character Agent Smith.  

Agent Smith is Matrix agent which are helping people in Matrix to get things in order.  
He doesn't like anarchy and can handle buerocracy to help people maintain good aspect of Matrix.  


## Architecture  

Agent Kovac is LLM based RAG.  
We are using OpenAI API, with embeddings based in chroma to connect Documents into chat. 


## Coding setup

Visual Studio Code is base for our development.


### Recommended VScode extension setup

Here are some recommendations.
- Docker
- Git graph
- Dev containers


### AI usage

We are using AI to help us develop and achieve right testing.  
Good usage:  
- learning new technologies and features
- evaluating code snippets
- analysing logs
- testing of code
- cleaning data

Bad usage:
- creating whole logic of functions in app
- generating passwords/secrets
- copy pasting whole blocks of code
- etc

VScode Extensions to use with AI:
- Github Copilot
- Github Copilot Chat
- Continue (with local LLM) -> [How-to](https://github.com/devopsacid/local-llm)

### Setup VScode formatting

On Windows:  
```sh
git config --global core.autocrlf true
```

On Linux/WSL:  
```sh
git config --global core.autocrlf input 
```

In .gitattributes:  
```ini
* text=auto
```

If using first time reset your git cached files:  
```sh
git rm --cached -r .
git reset --hard
``` 

## Howto use dev containers

[README on devcontainer](README-devcontainer.md)

