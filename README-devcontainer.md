# How-to use devcontainer

How to Use Docker Containers in VSCode.

Install Required Extensions:

- Docker
- Dev Containers  
  
Setup Docker:

Ensure Docker is installed and running on your machine. You can download Docker from here.  

`devcontainer.json` is located in `.devcontainer` folder  

Open the Project in a Dev Container:  

Open your project in VSCode.  
Press F1 and select `Dev Containers: Reopen in Container`.

You can run your docker-compose setup in devcontainer:
```
cd /workspaces/stubarag  
docker compose up -d
```

Console setup is closed to docker dev environment. 
You are running our dev `docker-compose.yaml` inside `devcontainer` too.  

[BACK](README.md)  
