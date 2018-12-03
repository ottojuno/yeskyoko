nvidia-docker run -v $PWD:/yeskyoko \
-e PYTHONPATH=$PYTHONPATH:/yeskyoko \
-p 0.0.0.0:8080:8080 \
-it pibisubukebe/yeskyoko python3 /yeskyoko/server.py