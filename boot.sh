#!/bin/bash

# Initialize and upgrade the database 
flask db init
flask db migrate
flask db upgrade

# Create recipe-photos directory in volume if it doesn't exist, will not result in error
mkdir /app/appdata/recipe-photos || true

# Populate recipe-photos directory, will not result in error
cp /rpdocker/default{01..27}.png /app/appdata/recipe-photos/ || true

# Start the application
exec gunicorn -b 0.0.0.0:4888 -w 4 app:app
