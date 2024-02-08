#!/bin/sh
cd `dirname $0`
pwd
cd js
npm install

cd ..
cd python
pwd
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt