#!/usr/bin/env bash

if [ "$(id -u)" == "0" ]; then
   echo -e "\e[91m\e[1mThis script should NOT be run as root\e[0m" >&2
fi

cd "$(dirname "$0")"

#------------------------------------------------------------------------------

STABLE_VERSION=$(head -n 1 VERSION)

echo -e "\e[91m\e[1mVerison that will be installed : $STABLE_VERSION\e[0m"


#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
#
#  Helpers
#
#------------------------------------------------------------------------------

function echo_step () {
    set +x
    exec 2>&4
    echo -e "\n\e[92m\e[1m$1\e[0m" >&2
    exec 2>&1
    set -x
}


function echo_warn () {
    set +x
    exec 2>&4
    echo -e "\e[93m\e[1m$1\e[0m" >&2
    exec 2>&1
    set -x
}


function echo_error () {
    set +x
    exec 2>&4
    echo -e "\e[91m\e[1m$1\e[0m" >&2
    exec 2>&1
    set -x
}


function echo_progress () {
    set +x
    exec 2>&4
    echo -e ".\c" >&2
    exec 2>&1
    set -x
}

function exit_error () {
    code=$1
    shift
    echo_error "$@"
    echo "(More details in install.log)" >&2
    exit $code
}

function install_compose () {
    if [ $xenial -eq 1 -o $bionic -eq 1 ]; then
        sudo curl -L https://github.com/docker/compose/releases/download/1.21.2/docker-compose-$(uname -s)-$(uname -m) \
        -o /usr/local/bin/docker-compose
    else
        exit_error 5 "Unsupported operating system for Docker. Install Docker manually (ReadMe.md)"
    fi
    sudo chmod +x /usr/local/bin/docker-compose
}

function install_docker () {
    sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo apt-key fingerprint 0EBFCD88
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install docker-ce
}

function geotrek_setup_new () {
    if [[ $(which docker) ]]; then
        echo "Docker is already installed"
    else
        install_docker
    fi
    if [[ $(which docker-compose) ]]; then
        echo "Docker-Compose is already installed"
    else
        install_compose
    fi
    cp .env.dist .env #TODO : Put comments in .env.dist to explain
    editor .env
    source .env
    # TODO : Check utiliy
    #if [$POSTGRES_HOST]; then
    #    sed -e '3,9d;82,83d' < ./docker-compose.yml
    #fi
    echo "Initiate var folder for settings and medias"
    sudo docker-compose run web bash exit
    sudo editor ./var/conf/custom.py
    while ! grep -Eq "^SRID[ ]?=[ ]?[1-9]{4,}" ./var/conf/custom.py || \
    ! grep -Eq "^DEFAULT_STRUCTURE_NAME[ ]?=[ ]?'\w*'" ./var/conf/custom.py || \
    ! grep -Eq "^SPATIAL_EXTENT[ ]?=[ ]?\([0-9]+[.]?[0-9]*[ ]?,[ ]?[0-9]+[.]?[0-9]*[ ]?,[ ]?[0-9]+[.]?[0-9]*[ ]?,[ ]?[0-9]+[.]?[0-9]*\)" ./var/conf/custom.py || \
    ! grep -Eq "^MODELTRANSLATION_LANGUAGES[ ]?=[ ]?\(('[a-z]+'){1}([ ]?,[ ]?'[a-z]+')*[ ]?[,]?[ ]?\)" ./var/conf/custom.py; do
        echo "Custom.py is not well set, the 4 parameters which has to be set are : "
        echo "SRID, DEFAULT_STRUCTURE_NAME, SPATIAL_EXTENT, MODELTRANSLATION_LANGUAGES"
        echo "Check comments to set it well"
        sleep 3
        sudo editor ./var/conf/custom.py
    done
    echo "Initiate Postgres"
    sudo docker-compose up -d postgres
    sleep 15
    echo "LoadData"
    sudo docker-compose run web initial.sh
    echo "Create a super User"
    sudo docker-compose run web ./manage.py createsuperuser
    echo "Transform your instance in a service"
    sed -i "s,WorkingDirectory=,WorkingDirectory=$1,g" geotrek.service;
    sudo cp geotrek.service /etc/systemd/system/geotrek.service
    sudo systemctl enable geotrek
    echo "Run 'sudo systemctl start geotrek' for start your service"
}

xenial=$(grep "Ubuntu 16.04" /etc/issue | wc -l)
bionic=$(grep "Ubuntu 18.04" /etc/issue | wc -l)

sudo chown -R $USER:$USER $(pwd)
sudo service postgresql stop
geotrek_setup_new $(pwd)