FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm
ARG USERNAME=vscode

WORKDIR /

# Configure global settings to bypass SSL certificate verification for corporate network/VPN
ENV GIT_SSL_NO_VERIFY=true
ENV PIP_TRUSTED_HOST="pypi.org pypi.python.org files.pythonhosted.org"
ENV NPM_CONFIG_STRICT_SSL=false

RUN echo "insecure" >> /root/.curlrc && \
    echo "check_certificate = off" >> /etc/wgetrc

# Install common tools
RUN apt update && apt -y install git procps curl libicu-dev build-essential libssl-dev libffi-dev wget libgl1

WORKDIR /home/$USERNAME
USER $USERNAME

# Configure vscode user settings to bypass SSL certificate verification
RUN echo "insecure" >> ~/.curlrc && \
    echo "check_certificate = off" >> ~/.wgetrc && \
    git config --global http.sslVerify false


# Install Azure AI CLI (which installs `az` CLI and `ai` CLI + dependencies)
RUN curl -sL https://aka.ms/InstallAzureAICLIDeb | bash

EXPOSE 11434
