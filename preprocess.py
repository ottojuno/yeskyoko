"""
    For each image in a directory we crop/center each face we find.
    We store the faces in the output directory.
    Each image is preprocessed in parallel using multiprocessing.
    based on: https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
"""
import argparse
import glob
import logging
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import cv2

from yeskyoko.align_dlib import AlignDlib

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)

align_dlib = AlignDlib(os.path.join(os.path.dirname(
    __file__), 'etc/shape_predictor_68_face_landmarks.dat'))


def preprocess_images(input_dir, output_dir, crop_dim):
    start_time = time.time()
    pool = mp.Pool(processes=mp.cpu_count())

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for image_dir in os.listdir(input_dir):
        image_output_dir = os.path.join(
            output_dir, os.path.basename(os.path.basename(image_dir)))
        if not os.path.exists(image_output_dir):
            os.makedirs(image_output_dir)

    image_paths = glob.glob(os.path.join(input_dir, '**/*.jpg'))

    for _, image_path in enumerate(image_paths):
        image_output_dir = os.path.join(
            output_dir, os.path.basename(os.path.dirname(image_path)))
        output_path = os.path.join(
            image_output_dir, os.path.basename(image_path))
        pool.apply_async(preprocess_image, (image_path, output_path, crop_dim))

    pool.close()
    pool.join()
    logger.info('Completed in {} seconds.'.format(time.time() - start_time))


def preprocess_image(input_path, output_path, crop_dim):
    images = process_image(input_path, crop_dim)
    for n, img in enumerate(images):
        p = Path(output_path)
        outfn = p.parent / "{}-{:0>4}{}".format(p.stem, n, p.suffix)
        logger.debug('preprocess_image: cv2.imwrite: {}'.format(outfn))
        cv2.imwrite(str(outfn), img)


def process_image(fn, crop_dim):
    images = []
    image = read_image(fn)

    bbs = align_dlib.getAllFaceBoundingBoxes(image)
    for bb in bbs:
        aligned = align_dlib.align(
            crop_dim, image, bb,
            landmarkIndices=AlignDlib.INNER_EYES_AND_BOTTOM_LIP)
        if aligned is not None:
            aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)
            images.append(aligned)

    return images


def read_image(fn):
    logger.debug('read_image: {}'.format(fn))
    image = cv2.imread(fn)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return image


def main(input_path, output_path, crop_dim):
    preprocess_images(input_path, output_path, crop_dim)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--input-dir', type=str,
                        action='store', default='data', dest='input_dir')
    parser.add_argument('--output-dir', type=str,
                        action='store', default='output', dest='output_dir')
    parser.add_argument('--crop-dim', type=int, action='store', default=180,
                        dest='crop_dim',
                        help='Size to crop images to')

    args = parser.parse_args()

    main(args.input_dir, args.output_dir, args.crop_dim)
