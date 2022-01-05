#!/bin/bash -e

echo ''
printf "    __  ____    ____          ___      __ \n\
   /  |/  / |  / / /___ _____/ (_)____/ /___ __   __ \n\
  / /|_/ /| | / / / __ \`/ __  / / ___/ / __ \`/ | / / \n\
 / /  / / | |/ / / /_/ / /_/ / (__  ) / /_/ /| |/ / \n\
/_/  /_/  |___/_/\__,_/\__,_/_/____/_/\__,_/ |___/\n"
echo '**************** 4D 56 6C 61 64 69 73 6C 61 76 *****************'
echo '****************************************************************'
echo '* Copyright of MVladislav, 2021                                *'
echo '* https://mvladislav.online                                    *'
echo '* https://github.com/MVladislav                                *'
echo '****************************************************************'
echo '* KONS                                                         *'
echo '****************************************************************'
echo ''

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo ''
echo 'setup:: path:: to install without root'
echo '--> setup:: path:: npm'
# SETUP:: npm
# Install NPM Gems to ~/.npm-packages
NPM_PACKAGES="${HOME}/.npm-packages"
export PATH="$PATH:$NPM_PACKAGES/bin"
# Preserve MANPATH if you already defined it somewhere in your config.
# Otherwise, fall back to `manpath` so we can inherit from `/etc/manpath`.
export MANPATH="${MANPATH-$(manpath)}:$NPM_PACKAGES/share/man"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# FUNCTIONS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cd into folder and clone + cd into cloned
clone_or_pull_and_cd() {
  local git_link=$1
  repo_name=$(basename "$git_link" .git)
  echo ''
  echo "inst:: git:: $repo_name"
  cd "$vm_path_git"

  git clone "$git_link" 2>/dev/null || (
    cd "$repo_name"
    git pull
  )
  cd "$repo_name"
}

# cd into folder, create folder for curl name and curl
curl_and_cd() {
  local curl_link=$1
  local repo_name=42
  echo ''
  echo "inst:: curl:: $repo_name"
  cd "$vm_path_git"
  mkdir -p "$repo_name"
  cd "$repo_name"
  curl "$curl_link" >"$repo_name"
}

# check if command always installed like 'which'
check_if_command_installed() {
  if ! command -v "$1" &>/dev/null; then
    echo 1
  else
    echo "--> inst:: ...:: $1 is always installed"
  fi
}
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo ''
echo 'init:: create base folder struct'
vm_path=$HOME/.vm_api
vm_path_git=$vm_path/git
vm_path_source=$vm_path/deb
vm_prefix=$HOME/.local
vm_run=$HOME/.local/bin
mkdir -p "$vm_path"
mkdir -p "$vm_path_git"
mkdir -p "$vm_path_source"
mkdir -p "$vm_prefix"
mkdir -p "$vm_run"

echo ''
echo "init:: venv"
export PYTHONPATH=
python3 -m venv "$vm_path/venv"
source "$vm_path/venv/bin/activate"
# curl https://bootstrap.pypa.io/get-pip.py -o "$vm_path_git/get-pip.py"
# python3 "$vm_path_git/get-pip.py"
python3 -m pip install --upgrade pip

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo ''
echo 'inst:: dependencies...'

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo ''
echo 'inst:: pip3:: services'
pips_to_install=(
  pip
)
for pip_to_install in "${pips_to_install[@]}"; do
  echo "--> inst:: pip3:: ${pip_to_install}"
  python3 -m pip install "$pip_to_install"
done

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo ''
echo 'inst:: npm:: services'
npms_to_install=(
  # ...
)
for npm_to_install in "${npms_to_install[@]}"; do
  echo "--> inst:: npm:: ${npm_to_install}"
  npm install -g "$npm_to_install"
done

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ...

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# set user own rules
chmod 750 "$vm_path" -R 2>/dev/null
chmod 750 "$vm_prefix" -R 2>/dev/null

echo ''
echo '#########################################################################'
echo ''

exit 0
