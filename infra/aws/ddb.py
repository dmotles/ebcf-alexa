"""
DynamoDB Wrapper

since boto3 is mostly code-gen'd, it doesn't provide any type hints. Making some light-weight wrappers
to make testing easier.
"""
import boto3
import logging
from .constants import REGION


LOG = logging.getLogger(__name__)


def dynamodb_resource():
    return boto3.resource('dynamodb', region_name=REGION)


class Table(object):
    def __init__(self, table_resource):
        self._resource = table_resource

    def get_row(self, **key) -> dict:
        response = self._resource.get_item(Key=key)
        return response['Item']


class DynamoDB(object):
    def __init__(self, resource_factory=dynamodb_resource):
        self._resource = resource_factory()

    def get_table(self, name: str) -> Table:
        table_resource = self._resource.Table(name)
        table_resource.reload()
        return Table(table_resource)
