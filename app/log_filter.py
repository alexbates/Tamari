# This file can be used to help with filtering access logs
# Use the following Gunicorn command:
# gunicorn -b 0.0.0.0:4888 -w 4 --error-logfile error.log --access-logfile >(python app/log_filter.py > access.log) app:app

import sys

excluded_paths = ['/static/', '/recipe-photos/']

for line in sys.stdin:
    if not any(path in line for path in excluded_paths):
        sys.stdout.write(line)