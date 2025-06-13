# Ansible Setup for RAG Project

This guide explains how to use Ansible to set up the environment for the RAG project. The setup includes creating a user, installing Docker, and configuring SSH keys.

## Prerequisites

- Ansible installed on your local machine.
- SSH access to the target server.
- Sudo privileges on the target server.

## Inventory

## Running the Playbooks
To run the playbooks, use the following commands.  

Run the main playbook (docker+rag setup):

`ansible-playbook -i inventory/prod.ini main.yml`


Run the Docker setup playbook:

`ansible-playbook -i inventory/prod.ini docker.yml`

If you have problem with authentication check playbook and fix `remote_user` or documentation to fix your remote_user or root/sudo password.  

