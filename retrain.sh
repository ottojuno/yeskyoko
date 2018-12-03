IMAGE_SIZE=224
ARCHITECTURE="mobilenet_0.50_${IMAGE_SIZE}"
IMAGE_DIR=faces-labeled
TRAIN_DIR=train

python -m yeskyoko.retrain \
  --bottleneck_dir=${TRAIN_DIR}/bottlenecks \
  --how_many_training_steps=250000 \
  --model_dir=${TRAIN_DIR}/models/ \
  --summaries_dir=${TRAIN_DIR}/training_summaries/"${ARCHITECTURE}" \
  --output_graph=${TRAIN_DIR}/retrained_graph.pb \
  --output_labels=${TRAIN_DIR}/retrained_labels.txt \
  --architecture="${ARCHITECTURE}" \
  --image_dir=${IMAGE_DIR}