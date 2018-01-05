import logging
import os
import sys
from typing import Optional

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


def create_or_update_stack(name: str,
                           config_env: str,
                           template: cfn.Template,
                           client: Optional[cfn.Client]=None) -> None:
    config = get_stack_config(config_env)
    if client is None:
        client = cfn.Client()
    stack = client.get_stack(name)
    try:
        if stack is None:
            LOG.debug('Creating stack: %s', name)
            template.create_stack(name, config)
        else:
            LOG.debug('%s already exists', name)
            template.update_stack(stack, config)
    except cfn.StackFailure as fail:
        LOG.error(str(fail))
        for stack_event in fail.stack.iter_failed_stack_events():
            LOG.error(str(stack_event))


def load_template(template_name: str) -> cfn.Template:
    with open(template_name, 'rb') as f:
        return cfn.Template(f.read())


def setup_logging():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-32s %(levelname)-8s: %(message)s')
    handler.setFormatter(formatter)

    #root = logging.getLogger()
    #root.setLevel(logging.DEBUG)
    #root.addHandler(handler)

    for logger in (LOG, logging.getLogger('aws')):
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
