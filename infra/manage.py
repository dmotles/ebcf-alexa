import logging
import os
import sys
from typing import Optional

import botocore.exceptions as boto_exc

from aws import ddb, cfn

ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_PATH = os.path.join(ROOT, 'cloudformation', 'ebcf-alexa-infra.template.yml')

GITHUB_CONFIG_TABLE = 'ebcf.alexa.config.github'
TEST_STACK = 'test-ebcf-alexa'
PROD_STACK = 'ebcf-alexa'


LOG = logging.getLogger(__name__)


def get_stack_config(env_name: str) -> dict:
    dynamodb = ddb.DynamoDB()
    table = dynamodb.get_table(GITHUB_CONFIG_TABLE)
    return table.get_row(env_name=env_name)


def create_stack(name: str, config_env: str, template: cfn.Template) -> cfn.Stack:
    return template.create_stack(name, get_stack_config(config_env))


def create_or_update_stack(name: str,
                           config_env: str,
                           template: cfn.Template,
                           client: Optional[cfn.Client]=None) -> None:
    if client is None:
        client = cfn.Client()
    stack = client.get_stack(name)
    if stack is None:
        LOG.debug('Creating stack: %s', name)
        create_stack(name, config_env, template)
    else:
        LOG.debug('%s already exists', name)


def load_template(template_name: str) -> cfn.Template:
    with open(template_name, 'rb') as f:
        return cfn.Template(f.read())


def setup_logging():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-32s %(levelname)-8s: %(message)s')
    handler.setFormatter(formatter)
    for logger in (LOG, logging.getLogger('boto3')):
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)


def main() -> int:
    setup_logging()
    template = load_template(TEMPLATE_PATH)
    create_or_update_stack(TEST_STACK, 'default', template)
    # 3. merge old stack params with new stack params.
    # 3a. ask for missing values?
    # 4. do a stack update
    # 5. wait for it to complete or fail
    # 6. report back
    return 0


if __name__ == '__main__':
    sys.exit(main())
