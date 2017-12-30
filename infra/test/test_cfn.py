from aws import cfn
from unittest.mock import NonCallableMagicMock, patch
import pytest
from typing import Callable, List, Tuple

SAMPLE_TEMPLATE_YML = b'''
# this is a sample yaml that might pass validation, but definitely wont
# run
Description: Yah
Parameters:
    InstanceType:
        Type: String
        Default: 't2.micro'
    Password: 
        Type: String
        NoEcho: yes
        Description: an unused password
Resources:
    EC2:
        Type: 'AWS::EC2::Instance'
        Properties:
            ImageId: i-abc123
            InstanceType: !Ref InstanceType
'''


@pytest.fixture
def validate_template_mock_response() -> dict:
    """since dicts are mutable, we will generate this per test"""
    return {
        'Parameters': [
            {
                'ParameterKey': 'InstanceType',
                'DefaultValue': 't2.micro',
            },
            {
                'ParameterKey': 'Password',
                'NoEcho': True,
                'Description': 'an unused password'
            },
        ],
        'Description': 'Yah',
        'Capabilities': ['CAPABILITY_IAM'],
        'CapabilitiesReason': 'something here, idk'
    }


@pytest.fixture(scope='module')
def _cfn_resource():
    """creates a real boto3 cfn resource to use as a spec"""
    return cfn.create_cfn_resource()


@pytest.fixture
def mock_cfn_resource(_cfn_resource,
                      validate_template_mock_response: dict) -> NonCallableMagicMock:
    """mock version of above, with functions spec'd out"""
    mock_resource = NonCallableMagicMock(spec=_cfn_resource)
    mock_client = NonCallableMagicMock(spec=_cfn_resource.meta.client,
                                       parent=mock_resource.meta,
                                       name='client')
    mock_resource.meta.client = mock_client
    mock_client.validate_template.return_value = validate_template_mock_response
    return mock_resource


@pytest.fixture
def mock_cfn_resource_factory(mock_cfn_resource) -> Callable[[], NonCallableMagicMock]:
    """used to init the Client"""
    return lambda: mock_cfn_resource


@pytest.fixture
def client(mock_cfn_resource_factory) -> NonCallableMagicMock:
    """a cfn.Client for test"""
    return cfn.Client(mock_cfn_resource_factory)


class MockStackResource(object):
    def __init__(self, name: str, mock_stack_states: List[Tuple[str, str]]):
        self._state_iter = iter(mock_stack_states)
        self.stack_status, self.stack_status_reason = next(self._state_iter)
        self.name = name
        self.update_call_count = 0

    def update(self) -> None:
        self.update_call_count += 1
        try:
            self.stack_status, self.stack_status_reason = next(self._state_iter)
        except StopIteration:
            pass


#########################################################################################
# TESTS
#########################################################################################

##
# Stack
##

@patch('time.sleep')
def test_stack_wait_for(mock_sleep):
    stack = cfn.Stack(
        MockStackResource('test_stack', [
            ('CREATE_IN_PROGRESS', ''),
            ('CREATE_IN_PROGRESS', ''),
            ('CREATE_COMPLETE', ''),
        ])
    )
    stack.wait_for(done_states={'CREATE_COMPLETE'},
                   fail_states={'CREATE_FAILED'})
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(10)


@patch('time.sleep')
def test_stack_wait_for_failure(mock_sleep):
    stack = cfn.Stack(
        MockStackResource('test_stack', [
            ('CREATE_IN_PROGRESS', ''),
            ('CREATE_IN_PROGRESS', ''),
            ('ROLLBACK_IN_PROGRESS', 'Something broke'),
            ('ROLLBACK_IN_PROGRESS', 'Something broke'),
            ('CREATE_FAILED', 'shits broken'),
        ])
    )
    with pytest.raises(cfn.StackFailure) as exc_info:
        stack.wait_for(done_states={'CREATE_COMPLETE'},
                       fail_states={'CREATE_FAILED'})
    assert str(exc_info.value) == 'CREATE_FAILED: shits broken'
    assert mock_sleep.call_count == 4
    mock_sleep.assert_called_with(10)


##
# Client
##

def test_client_init(mock_cfn_resource, mock_cfn_resource_factory):
    client = cfn.Client(mock_cfn_resource_factory)
    assert client._resource is mock_cfn_resource
    assert client._client is mock_cfn_resource.meta.client


def test_client_validate_template(client):
    assert client.validate_template('yo') is \
           client._client.validate_template.return_value
    client._client.validate_template.assert_called_once_with(
        TemplateBody='yo'
    )


@pytest.mark.parametrize('parameters', [
    None,
    [{'ParameterKey': 'key', 'ParameterValue': 'value'}]
])
@pytest.mark.parametrize('capabilities', [
    None,
    ['CAPABILITY_IAM']
])
def test_client_create_stack(client, parameters, capabilities):
    ret = client.create_stack('stack_name', 'stack_body',
                              parameters=parameters,
                              capabilities=capabilities,
                              block=False)
    assert ret._resource == client._resource.create_stack.return_value
    client._resource.create_stack.assert_called_once_with(
        StackName='stack_name',
        TemplateBody='stack_body',
        Parameters=parameters,
        Capabilities=capabilities
    )


@patch('time.sleep')
def test_client_create_stack_blocking(mock_sleep, client):
    # Make it so the service resource create_stack returns the above
    # MockStackResource implementation that automatically finishes
    client._resource.create_stack.side_effect = (
        lambda StackName, TemplateBody, Parameters, Capabilities:
        MockStackResource(StackName, [
            ('CREATE_IN_PROGRESS', ''),
            ('CREATE_COMPLETE', '')
        ])
    )
    ret = client.create_stack('stack_name', 'stack_body', block=True)
    assert ret.name == 'stack_name'
    assert ret._resource.update_call_count == 1
    assert mock_sleep.call_count == 1


@pytest.mark.parametrize('status', [
    'CREATE_FAILED',
    'ROLLBACK_IN_PROGRESS',
    'ROLLBACK_COMPLETE',
    'ROLLBACK_FAILED'
])
@patch('time.sleep')
def test_client_create_stack_error(mock_sleep, client, status):
    # Make it so the service resource create_stack returns the above
    # MockStackResource implementation that automatically finishes
    client._resource.create_stack.side_effect = (
        lambda StackName, TemplateBody, Parameters, Capabilities:
        MockStackResource(StackName, [
            ('CREATE_IN_PROGRESS', ''),
            (status, 'error')
        ])
    )
    with pytest.raises(cfn.StackFailure):
        client.create_stack('stack_name', 'stack_body', block=True)
    assert mock_sleep.called

##
# Template
##

def test_template_init(client: cfn.Client):
    template = cfn.Template(SAMPLE_TEMPLATE_YML, client=client)
    assert isinstance(template.template_content, str) # template should not be raw bytes
    assert template.parameters == {
        'InstanceType': {
            'ParameterKey': 'InstanceType',
            'DefaultValue': 't2.micro',
        },
        'Password': {
            'ParameterKey': 'Password',
            'NoEcho': True,
            'Description': 'an unused password'
        }
    }
    assert template.description == 'Yah'
    assert template.capabilities == ['CAPABILITY_IAM']





