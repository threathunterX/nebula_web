#!/bin/bash

# get workspace dir
# resolve links - $0 may be a softlink
PRG="$0"
while [ -h "$PRG" ]; do
    ls=`ls -ld "$PRG"`
    link=`expr "$ls" : '.*-> \(.*\)$'`
    if expr "$link" : '/.*' > /dev/null; then
        PRG="$link"
    else
        PRG=`dirname "$PRG"`/"$link"
    fi
done

# Get standard environment variables
PRG=`readlink -e $PRG`
SCRIPTS_DIR=`dirname "$PRG"`
WS_DIR=`dirname "$SCRIPTS_DIR"`
echo "workspace is $WS_DIR"

# remove stale virtualenv
rm -rf "$WS_DIR/venv"

# download and install nebula web third party packages
if [ -d "$WS_DIR/venv" ]; then
    rm -rf "$WS_DIR/venv"
fi
virtualenv --no-site-packages $WS_DIR/venv
source $WS_DIR/venv/bin/activate
$WS_DIR/venv/bin/pip install -i http://172.16.10.57:8081/simple --trusted-host 172.16.10.57 --upgrade pip==8.1.2-threathunter

. $WS_DIR/venv/bin/activate
$WS_DIR/venv/bin/pip install -i http://172.16.10.57:8081/simple --extra-index-url=http://pypi.douban.com/simple --upgrade -r $WS_DIR/requirements.txt
# add aerospike
$WS_DIR/venv/bin/pip install http://172.16.10.57:8081/packages/aerospike-2.0.5.tar.gz  --install-option="--lua-system-path=venv/lua"

virtualenv --relocatable venv

# fix the relocatable python file ,as the encoding should at the front
ls venv/bin/*.py | xargs -n 1 -I {} sed -i -e '/-*- coding/d' -e '0,/^[~#]/a# -*- coding: utf-8 -*-' {}

# download and install swagger package
wget http://172.16.10.57:8081/packages/swagger-1.0.0.tar.gz
tar xvf swagger-1.0.0.tar.gz
mv swagger-1.0.0 nebula/middleware/swagger
rm -rf swagger-1.0.0*
