import logging
import argparse
import os

import manage


LOG = logging.getLogger(__name__)


def is_file(arg):
    if not os.path.isfile(arg):
        raise ValueError('{} is not a file'.format(arg))
    return arg


def main():
    manage.setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=is_file)

    opts = parser.parse_args()

    # Will raise exception if the template is not valid
    manage.load_template(opts.path)


if __name__ == '__main__':
    main()
