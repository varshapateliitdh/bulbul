FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm
ARG USERNAME=vscode

WORKDIR /

# Install common tools
RUN apt update && apt -y install git procps curl libicu-dev build-essential libssl-dev libffi-dev wget libgl1

WORKDIR /home/$USERNAME
USER $USERNAME

# Install Azure AI CLI (which installs `az` CLI and `ai` CLI + dependencies)
RUN curl -sL https://aka.ms/InstallAzureAICLIDeb | bash

EXPOSE 11434
