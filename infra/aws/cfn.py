import logging
import boto3
from typing import Optional, List, Callable, Dict, Set, Any
import time
from .constants import REGION


LOG = logging.getLogger(__name__)


def create_cfn_resource():
    return boto3.resource('cloudformation', region_name=REGION)


class Stack(object):
    def __init__(self, stack_resource):
        self._resource = stack_resource
        self._client = self._resource.meta.client

    def get_template(self) -> str:
        return self._client.get_template(StackName=self.name)['TemplateBody']

    @property
    def status(self) -> str:
        return self._resource.stack_status

    @property
    def status_reason(self) -> str:
        return self._resource.stack_status_reason

    @property
    def name(self) -> str:
        return self._resource.name

    @property
    def parameter_keys(self) -> Set[str]:
        return set(p['ParameterKey'] for p in self._resource.parameters)

    def wait_for(self, done_states: Set[str], fail_states: Set[str]):
        exit_loop_states = done_states | fail_states
        while self.status not in exit_loop_states:
            LOG.debug('Stack %s in status %s because %s',
                      self.name, self.status, self.status_reason)
            time.sleep(10) # 10 seconds seems like a good poll interval
            self._resource.update()
        if self.status in fail_states:
            raise StackFailure(
                '{}: {}'.format(self.status, self.status_reason))

    def update(self,
               template_body: Optional[dict]=None,
               block: bool=True,
               parameters: Optional[List[Dict[str,str]]]=None,
               capabilities: Optional[List[str]]=None) -> None:
        call_args = {}
        if template_body is None:
            call_args['UsePreviousTemplate'] = True
        else:
            call_args['TemplateBody'] = template_body
        if capabilities is not None:
            call_args['Capabilities'] = capabilities
        if parameters is not None:
            call_args['Parameters'] = parameters
        self._resource.update(**call_args)

        if block:
            waiter = self._client.get_waiter('stack_update_complete')
            waiter.wait(
                StackName=self.name,
                WaiterConfig={
                    'Delay': 10,
                    'MaxAttempts': 120
                }
            )


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
        if block:
            stack.wait_for(
                {'CREATE_COMPLETE'},
                fail_states={
                    'CREATE_FAILED',
                    'ROLLBACK_IN_PROGRESS',
                    'ROLLBACK_COMPLETE',
                    'ROLLBACK_FAILED'
                }
            )
        return stack

    def get_stack(self, name: str) -> Optional[Stack]:
        for s in self._resource.stacks.filter(StackName=name):
            return Stack(s)
        return None


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

    def _merge_parameters(self, params: dict) -> list:
        merged_params = []
        for key, template_param in self.parameters.items():
            if key in params:
                merged_params.append({
                    'ParameterKey': key,
                    'ParameterValue': params[key]
                })
            elif 'DefaultValue' not in template_param:
                raise KeyError('{} is not specified and has no default value'.format(key))
        return merged_params

    def create_stack(self, stack_name: str, params: dict) -> Stack:
        return self._client.create_stack(stack_name,
                                         self.template_content,
                                         block=True,
                                         parameters=self._merge_parameters(params),
                                         capabilities=self.capabilities)

    def _merge_update_params(self, params: Dict[str, str], old_param_keys: Set[str]) -> List[Dict[str, str]]:
        update_params = []
        for key, template_param in self.parameters.items():
            if key in params:
                update_params.append({
                    'ParameterKey': key,
                    'ParameterValue': params[key]
                })
            elif key in old_param_keys:
                update_params.append({
                    'ParameterKey': key,
                    'UsePreviousValue': True
                })
            elif 'DefaultValue' not in template_param:
                raise KeyError('{} is not specified and has no default value'.format(key))
        return update_params

    def update_stack(self, stack: Stack, params: dict):
        old_param_keys = stack.parameter_keys
        update_args = dict(
            parameters=self._merge_update_params(params, old_param_keys),
            capabilities=self.capabilities
        )

        # same template, parameter-only update
        if set(self.parameters) != old_param_keys or \
                self.template_content != stack.get_template():
            update_args['template_body'] = self.template_content

        stack.update(**update_args)
