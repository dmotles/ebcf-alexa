from typing import Union
import xml.etree.ElementTree as libxml

class _Dictable(object):
    def dict(self) -> dict:
        return {}


class SSMLParseError(ValueError):
    """Raised if ssml is broken."""


def xml_error(parse_err: libxml.ParseError, txt: str) -> SSMLParseError:
    line_no, offset = parse_err.position
    default_msg = parse_err.args[0]
    for line in txt.splitlines(False):
        line_no -= 1
        if line_no == 0:
            msg = '\n'.join([
                default_msg,
                '',
                '\t' + line,
                '\t' + ' '*offset + '^',
                ])
            return SSMLParseError(msg)
    return SSMLParseError(default_msg)


def validate_ssml(ssml_str: str):
    try:
        doc: libxml.Element = libxml.fromstring(ssml_str)
    except libxml.ParseError as perr:
        raise xml_error(perr, ssml_str) from None

    if doc.tag != 'speak':
        raise SSMLParseError('ssml must start and end with <speak> tags.')


class SSML(_Dictable):
    def __init__(self, ssml: str):
        starttag = '<speak>' if not ssml.startswith('<speak>') else ''
        endtag = '</speak>' if not ssml.endswith('</speak>') else ''
        ssml = ''.join((starttag, ssml, endtag))
        validate_ssml(ssml)
        self.ssml = ssml

    def dict(self) -> dict:
        return {
                'type': 'SSML',
                'ssml': self.ssml
        }


class PlainText(_Dictable):
    def __init__(self, text: str):
        self.text = text

    def dict(self) -> dict:
        return {
            'type': 'PlainText',
            'text': self.text
        }

    def to_ssml(self) -> SSML:
        return SSML('<speak>%s</speak>' % self.text)


SpeechType = Union[SSML, PlainText]


class SimpleCard(_Dictable):
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content

    def dict(self) -> dict:
        return {
            'type': 'Simple',
            'title': self.title,
            'content': self.content
        }


def _convert_https(url: str) -> str:
    if url.startswith('http://'):
        return url.replace('http://', 'https://', 1)
    return url


class StandardCard(SimpleCard):
    def __init__(self, title: str, content: str, small_image_url: str=None, large_image_url: str=None):
        super().__init__(title, content)
        if small_image_url:
            small_image_url = _convert_https(small_image_url)
        if large_image_url:
            large_image_url = _convert_https(large_image_url)
        self.small_image_url = small_image_url
        self.large_image_url = large_image_url

    def dict(self) -> dict:
        x = {
            'type': 'Standard',
            'title': self.title,
            'text': self.content,
        }
        if self.small_image_url:
            x.setdefault('image', {})['smallImageUrl'] = self.small_image_url
        if self.large_image_url:
            x.setdefault('image', {})['largeImageUrl'] = self.large_image_url
        return x


class SpeechletResponse(_Dictable):
    def __init__(self,
                 output_speech: SpeechType=None,
                 card: SimpleCard=None,
                 reprompt: SpeechType=None,
                 attributes: dict=None,
                 should_end: bool=True):
        self.output_speech = output_speech
        self.card = card
        self.reprompt = reprompt
        self.attributes = attributes
        self.should_end = should_end

    def dict(self) -> dict:
        x = {
            'version': '1.0',
            'response': {
                'shouldEndSession': self.should_end
            },
            'sessionAttributes': self.attributes or {}
        }
        if self.output_speech:
            x['response']['outputSpeech'] = self.output_speech.dict()
        if self.reprompt:
            x['response']['reprompt'] = {
                'outputSpeech': self.reprompt.dict()
            }
        if self.card:
            x['response']['card'] = self.card.dict()
        return x

