#!/bin/bash

source venv/bin/activate
gunicorn -b 0.0.0.0:4888 -w 4 --error-logfile error.log --access-logfile >(python app/log_filter.py > access.log) app:app