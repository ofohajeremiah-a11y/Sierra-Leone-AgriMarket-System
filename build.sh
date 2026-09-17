#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r backend/requirements.txt

cd frontend
npm install
VITE_API_URL=/api npm run build
cd ..

python backend/manage.py migrate
python backend/manage.py seed_demo
python backend/manage.py collectstatic --noinput
