#!/bin/bash

source venv/bin/activate
gunicorn -b 0.0.0.0:4888 -w 4 app:app