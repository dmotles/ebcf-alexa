"""
Entry point for lambda
"""
from _ebcf_alexa import lambda_func
from pprint import pformat

def lambda_handler(*args, **kwargs):
    ret = lambda_func.lambda_handler(*args, **kwargs)
    print('RETURNING BACK: %s' % pformat(ret))
    return ret
