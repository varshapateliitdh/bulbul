#!/bin/bash

# fix git permissions on some machines
git config --global --add safe.directory $1
git config --global credential.https://dev.azure.com.useHttpPath true

###############################################
###       INSTALL & SETUP NODE & NPM       ###
#############################################
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# Load nvm and use Node.js version 18
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # Loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # Loads nvm bash_completion

nvm install 18
nvm use 18
echo "Node -> $(node -v)" # Should print  Node -> v18.x.x
echo "NPM -> $(npm -v)" # Should print  NPM -> v10.8.x
npm install -g @angular/cli@18
echo "Angular -> $(ng --version)" # Should print  Angular -> v18.x.x

#################################
###       SETUP PYTHON       ###
################################
python -m pip install --upgrade pip

#######################################
# Setup Dotnet 8 (for azure-keyring) #
######################################
wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update && sudo apt-get install -y dotnet-sdk-8.0

#############################
## Install & setup poetry ##
###########################
sudo apt install pipx -y
pipx ensurepath
pipx install poetry==1.8.5
poetry self add artifacts-keyring

# Package for application development
poetry install --no-root --sync --all-extras --with lint --with dev

###########################################
### Install Microsoft ODBC Driver 17   ###
###########################################
if ! [[ "8 9 10 11 12" == *"$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1)"* ]]; then
    echo "Debian $(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1) is not currently supported."
    exit 1
fi

# Download and install Microsoft's package repo
curl -sSL -O https://packages.microsoft.com/config/debian/$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1)/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb  # Cleanup

# Update package list and install ODBC Driver 17
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17


# pre-commit installation abd run
poetry run pre-commit install
poetry run pre-commit run --all-files


##################################
### CONFIGURE GIT CREDENTIALS ###
#################################
echo "Please configure git with your name and email:"
read -p "Enter your name: " user_name
git config --global user.name "$user_name"
read -p "Enter your email: " user_email
git config --global user.email "$user_email"
