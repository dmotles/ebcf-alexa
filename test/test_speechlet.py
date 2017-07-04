from _ebcf_alexa import speechlet
import pytest


@pytest.mark.parametrize('_input', [
    'test', '<speak>test', 'test</speak>', '<speak>test</speak>'
])
def test_ssml(_input: str):
    """
    Tests handling of <speak> tags and dict schema.
    :param _input:
    :return:
    """
    ssml = speechlet.SSML(_input)
    assert ssml.ssml == '<speak>test</speak>'
    assert ssml.dict() == {'type': 'SSML', 'ssml': ssml.ssml}


def test_plaintext():
    """
    Tests PlainText dict schema.
    :return:
    """
    pt = speechlet.PlainText('test')
    assert pt.text == 'test'
    assert pt.dict() == {'type': 'PlainText', 'text': 'test'}


def test_plaintext_tossml():
    """
    Tests conversion method from PlainText -> SSML.
    :return:
    """
    assert speechlet.PlainText('test').to_ssml().ssml == '<speak>test</speak>'


def test_simple_card_schema():
    card = speechlet.SimpleCard(title='title', content='content')
    assert card.dict() == {
        'type': 'Simple',
        'title': 'title',
        'content': 'content'
    }


def test_convert_https():
    assert speechlet._convert_https('http://google.com') == 'https://google.com'
    assert speechlet._convert_https('https://google.com') == 'https://google.com'
    assert speechlet._convert_https('ftp://google.com') == 'ftp://google.com'
    assert speechlet._convert_https('google.com') == 'google.com'


@pytest.mark.parametrize(
    'kwargs1,expected_dict1', [
        # No args
        ({}, {}),
        # Args for small_image_url, but using http url
        ({'small_image_url': 'http://google.com/image.jpg'},
         {'smallImageUrl': 'https://google.com/image.jpg'}),
        # Args for small_image_url, https url
        ({'small_image_url': 'https://s3.amazonaws.com/bucket/image.png'},
         {'smallImageUrl': 'https://s3.amazonaws.com/bucket/image.png'}),
    ],
    ids=['NoSmallImageUrl', 'smallImageUrl(HTTP)', 'smallImageUrl(HTTPS)']
)
@pytest.mark.parametrize(
    'kwargs2,expected_dict2', [
        # No args
        ({}, {}),
        # Args for large_image_url, but using http url
        ({'large_image_url': 'http://google.com/image_l.jpg'},
         {'largeImageUrl': 'https://google.com/image_l.jpg'}),
        # Args for large_image_url, https url
        ({'large_image_url': 'https://s3.amazonaws.com/bucket/image_l.png'},
         {'largeImageUrl': 'https://s3.amazonaws.com/bucket/image_l.png'}),
    ],
    ids=['NoLargeImageUrl', 'largeImageUrl(HTTP)', 'largeImageUrl(HTTPS)']
)
def test_standard_card(kwargs1: dict,
                       expected_dict1: dict,
                       kwargs2: dict,
                       expected_dict2: str):

    input_kwargs = {}
    input_kwargs.update(kwargs1)
    input_kwargs.update(kwargs2)
    card = speechlet.StandardCard(title='title', content='content', **input_kwargs)
    expected = {
        'type': 'Standard',
        'title': 'title',
        'text': 'content'
    }
    if expected_dict1 or expected_dict2:
        expected['image'] = {}
        expected['image'].update(expected_dict1)
        expected['image'].update(expected_dict2)
    assert card.dict() == expected


def test_speechlet_response_default():
    assert speechlet.SpeechletResponse().dict() == {
        'version': '1.0',
        'response': {'shouldEndSession': True},
        'sessionAttributes': {}
    }


@pytest.mark.parametrize('_input', [True, False])
def test_speechlet_response_should_end(_input: bool):
    s = speechlet.SpeechletResponse(should_end=_input)
    assert s.dict()['response']['shouldEndSession'] == _input