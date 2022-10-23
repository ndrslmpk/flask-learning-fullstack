#!/bin/bash
echo "This script starts the local flask development server"

cd starter_code
cd env/Scripts
. activate
cd .. 
cd ..
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
# python app.py