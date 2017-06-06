class _Dictable(object):
    def dict(self) -> dict:
        return {}

class SSML(_Dictable):
    def __init__(self, ssml: str):
        starttag = '<speak>' if not ssml.startswith('<speak>') else ''
        endtag = '</speak>' if not ssml.endswith('</speak>') else ''
        self.ssml = ''.join((starttag, ssml, endtag))

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


class SpeechletResponse(_Dictable):
    def __init__(self,
                 output_speech: _Dictable=None,
                 card: _Dictable=None,
                 reprompt: _Dictable=None,
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

