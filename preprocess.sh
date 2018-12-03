INPUT=/yeskyoko/data
OUTPUT=/yeskyoko/faces

docker run -v $PWD:/yeskyoko \
-e PYTHONPATH=$PYTHONPATH:/yeskyoko \
-it pibisubukebe/yeskyoko python3 /yeskyoko/preprocess.py \
--input-dir ${INPUT} \
--output-dir ${OUTPUT} \
--crop-dim 224