#!/usr/bin/env python3
"""
    Tool for manually labeling images in a directory.
    Example:
        mkdir -p data/{notkyoko,yeskyoko}
        # preprocess to get faces/{notkyoko,yeskyoko}
        python3 -m yeskyoko.label faces
        # to get faces-labeled/{notkyoko,yeskyoko}
        # now you can train on faces-labeled
"""
from pathlib import Path

import numpy as np
import cv2


def load_image(fn):
    img = cv2.imread(fn, cv2.IMREAD_COLOR)

    return img


def unlabel(fn, output, labels):
    for label in labels:
        try:
            (output / label / fn.name).unlink()
        except FileNotFoundError:
            continue


def label_images(dirn):
    labels = []

    for fn in Path(dirn).glob('*'):
        if fn.is_dir():
            labels.append(fn.name)

    # make directories
    output = Path('./{}-labeled'.format(dirn))
    output.mkdir(exist_ok=True)
    for n, label in enumerate(labels):
        Path('./{}-labeled/{}'.format(Path(dirn).absolute().name, label)
             ).mkdir(exist_ok=True)
        print('[{}] {}'.format(n + 1, label))

    images = [fn for fn in Path(dirn).glob('**/*.jpg')]

    ndx = 0
    while ndx < len(images):
        fn = images[ndx]

        img = load_image(str(fn))
        cv2.imshow('unlabeled', img)
        cv2.moveWindow('unlabeled', 2048, 0)
        k = cv2.waitKey(0)

        # quit
        if k == 27 or k == ord('q'):
            break

        # previous image
        if k == 8:
            ndx = ndx - 1
            continue

        # skip
        if k == ord('s'):
            print('=> skip')
            unlabel(fn, output, labels)
            ndx = ndx + 1
            continue

        # label
        num = -1
        if (k >= 48 and k <= 57):
            num = k - 48
        elif(k >= 96 and k <= 105):
            num = k - 96
        else:
            continue

        unlabel(fn, output, labels)

        label = labels[num - 1]
        out = output / label / fn.name
        print('=> {}'.format(label))
        cv2.imwrite(str(out), img)

        # next image
        ndx = ndx + 1
        if ndx % 100 == 0:
            print("{} of {}".format(ndx, len(images)))

    cv2.destroyAllWindows()


if __name__ == '__main__':
    import sys
    dirn = sys.argv[1]
    label_images(dirn)
