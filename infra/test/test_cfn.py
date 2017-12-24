from aws import cfn
from unittest.mock import NonCallableMagicMock
import pytest
from typing import Callable

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


#########################################################################################
# TESTS
#########################################################################################

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
    assert client.create_stack('stack_name', 'stack_body',
                               parameters=parameters,
                               capabilities=capabilities)._resource is \
        client._resource.create_stack.return_value
    client._resource.create_stack.assert_called_once_with(
        StackName='stack_name',
        TemplateBody='stack_body',
        Parameters=parameters,
        Capabilities=capabilities
    )


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





