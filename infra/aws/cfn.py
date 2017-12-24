import logging
import boto3
from typing import Optional, List, Callable, Dict, Set, Any
import time


REGION = 'us-east-1'
TEST_STACK = 'test-ebcf-alexa'
PROD_STACK = 'ebcf-alexa'

LOG = logging.getLogger(__name__)


def create_cfn_resource():
    return boto3.resource('cloudformation', region_name=REGION)


class Stack(object):
    def __init__(self, stack_resource):
        self._resource = stack_resource

    @property
    def status(self) -> str:
        return self._resource.stack_status

    @property
    def status_reason(self) -> str:
        return self._resource.stack_status_reason

    @property
    def name(self) -> str:
        return self._resource.name

    def wait_for(self,
                 done_states: Set[str],
                 fail_states: Set[str],
                 poll_interval: int=10):
        exit_loop_states = done_states | fail_states
        while self.status not in exit_loop_states:
            LOG.debug('Stack %s in status %s because %s',
                      self.name, self.status, self.status_reason)
            time.sleep(poll_interval)
            self._resource.update()
        if self.status in fail_states:
            raise StackFailure(
                '{}: {}'.format(self.status, self.status_reason))


class Client(object):
    def __init__(self, factory: Callable=create_cfn_resource):
        # Because the cfn resource is not thread safe, we will create one per client,
        # and thus require a factory function
        self._resource = factory()
        self._client = self._resource.meta.client

    def validate_template(self, body: str) -> dict:
        return self._client.validate_template(TemplateBody=body)

    def create_stack(self,
                     name: str,
                     body: str,
                     block: bool=True,
                     parameters: Optional[List[Dict[str,str]]]=None,
                     capabilities: Optional[List[str]]=None) -> Stack:
        stack = Stack(self._resource.create_stack(
            StackName=name,
            TemplateBody=body,
            Parameters=parameters,
            Capabilities=capabilities
        ))
        return stack


class StackFailure(Exception):
    pass


class Template(object):
    def __init__(self, template_content: bytes, client: Optional[Client]=None):
        if client is None:
            client = Client()
        self._client = client
        self.template_content = template_content.decode('utf-8')
        res = self._client.validate_template(self.template_content)
        LOG.debug('validate_template: %r', res)
        self.parameters = {
            p['ParameterKey']: p
            for p in res['Parameters']
        }
        self.description = res.get('Description')
        self.capabilities = res['Capabilities']

    def __repr__(self):
        return 'Template({!r})'.format(self.template_content)

    def __str__(self):
        return 'Template(parameters={0.parameters!r}, ' \
               'description={0.description!r}, ' \
               'capabilities={0.capabilities!r})'.format(self)

