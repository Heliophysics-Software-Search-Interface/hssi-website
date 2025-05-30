# See: https://sebest.github.io/post/protips-using-gunicorn-inside-a-docker-image/

import os

for k,v in os.environ.items():
	if k.startswith("GUNICORN_"):
		key = k.split('_', 1)[1].lower()
		locals()[key] = v
