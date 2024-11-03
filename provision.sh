#! /bin/bash -e

SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
cd ${SCRIPT_DIR}

sudo apt-get update
sudo apt-get install ansible -y
sudo apt-get install git -y

ansible-galaxy install -f -r ${SCRIPT_DIR}/requirements.yml

ansible-playbook \
  --connection=local \
  --inventory 127.0.0.1, \
  --limit 127.0.0.1 \
  --extra-vars 'ansible_python_interpreter=/usr/bin/python3' \
  ${SCRIPT_DIR}/playbook.yml
