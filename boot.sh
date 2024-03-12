#!/bin/bash
flask db upgrade
exec gunicorn -b 0.0.0.0:4888 -w 4 app:app
