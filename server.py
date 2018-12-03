"""
    Web app and server.
    We only support jpg images.
"""
import argparse
import glob
import logging
import os
import time
from pathlib import Path
import cherrypy
import io

import cv2
import numpy as np
import tensorflow as tf

from yeskyoko.align_dlib import AlignDlib
from base64 import b64decode

MODEL_FILENAME = "/yeskyoko/train/retrained_graph.pb"
LABEL_FILENAME = "/yeskyoko/train/retrained_labels.txt"
INPUT_HEIGHT = 224
INPUT_WIDTH = 224
INPUT_MEAN = 128
INPUT_STD = 128
INPUT_LAYER_NAME = "input"
OUTPUT_LAYER_NAME = "final_result"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

align_dlib = AlignDlib(os.path.join(os.path.dirname(
    __file__), 'etc/shape_predictor_68_face_landmarks.dat'))


def preprocess(image, crop_dim=224):
    bbs = align_dlib.getAllFaceBoundingBoxes(image)
    faces = []
    for bb in bbs:
        aligned = align_dlib.align(
            crop_dim, image, bb,
            landmarkIndices=AlignDlib.INNER_EYES_AND_BOTTOM_LIP)
        aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)
        faces.append(aligned)

    return faces


def load_graph(modelfn):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

    with open(modelfn, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph


def read_tensor_from_image(image, filetype="image/jpeg",
                           input_height=299, input_width=299,
                           input_mean=0, input_std=255):
    if filetype == "image/jpeg":
        image_reader = tf.image.decode_jpeg(
            image, channels=3, name='jpeg_reader')
    elif filetype == "image/png":
        image_reader = tf.image.decode_png(
            image, channels=3, name='png_reader')

    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    resized = tf.image.resize_bilinear(
        dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)

    return result


def load_labels(labelfn):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(labelfn).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label


def img_from_uri(uri):
    data = uri.split(b',')[1]
    arr = np.fromstring(b64decode(data), dtype=np.uint8)
    return cv2.imdecode(arr, -1)


class App(object):
    def __init__(self):
        self.graph = load_graph(MODEL_FILENAME)
        self.labels = load_labels(LABEL_FILENAME)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def label(self):
        # note: error is displayed to user
        size = 0
        sizeLimit = 12  # in MB
        img = b''
        while True:
            data = cherrypy.request.body.read(8192)
            img += data
            if not data:
                break
            size += len(data)
            if size > sizeLimit * 1024 * 1024:
                return {
                    'error': "Image must be smaller than {} MB".format(sizeLimit)
                }

        # decode and convert image
        try:
            img = img_from_uri(img)
        except Exception:
            return{
                'error': "We failed to decode the image."
            }

        if img is None:
            print('label: img_from_uri failed')
            return {
                'error': "We failed to decode the image."
            }

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # preprocess to find faces
        faces = preprocess(img)

        # label each face
        labels = []
        for _, face in enumerate(faces):
            face = cv2.imencode('.jpg', face)[1].tostring()
            t = read_tensor_from_image(face,
                                       input_height=INPUT_HEIGHT, input_width=INPUT_WIDTH,
                                       input_mean=INPUT_MEAN, input_std=INPUT_STD)
            input_name = "import/{}".format(INPUT_LAYER_NAME)
            output_name = "import/{}".format(OUTPUT_LAYER_NAME)
            input_op = self.graph.get_operation_by_name(input_name)
            output_op = self.graph.get_operation_by_name(output_name)

            with tf.Session(graph=self.graph) as sess:
                results = sess.run(output_op.outputs[0],
                                   {input_op.outputs[0]: t})

            results = np.squeeze(results)
            top_k = results.argsort()[-5:][:: - 1]
            label = {}
            for i in top_k:
                label.update({self.labels[i]: float(results[i])})

            labels.append(label)

        result = {
            'faces': len(faces),
            'labels': labels,
            'size': size,
        }

        return result


if __name__ == '__main__':
    cherrypy.quickstart(App(), config="/yeskyoko/server.conf")
