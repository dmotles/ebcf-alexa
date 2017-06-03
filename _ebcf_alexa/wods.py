from urllib.request import urlopen
from urllib.parse import urlencode
import json
import logging
from datetime import datetime
import sys
import re

LOG = logging.getLogger(__name__)

URL = 'http://www.elliottbaycrossfit.com/api/v1/wods?'


def _urlencode_multilevel(obj):
    """
    EBCF uses PHP-style query args that support nested dictionaries.

    E.g. we need to typically pass the following args to the API:
        filter[simple][date]:2017-06-01T00:00:00.000Z
        filter[simple][enabled]:True

    and these need to be encoded.
    """
    flattened_params = {}

    def _flatten_obj(obj, parent_key):
        sub_params = {}
        if isinstance(obj, dict):
            for child_key in obj:
                encode_key = '{}[{}]'.format(parent_key, child_key)
                sub_params[encode_key] = obj[child_key]
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                encode_key = '{}[{}]'.format(parent_key, i)
                sub_params[encode_key] = obj[child_key]
        else:
            flattened_params[parent_key] = obj
        for k, v in sub_params.items():
            _flatten_obj(v, k)

    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten_obj(v, k)

    return urlencode(flattened_params)


def get_wod(date):
    """
    gets the WOD for a specific day.

    :param datetime.date date: the date
    :returns: wod data or None if not found
    :rtype: dict
    """
    params = {'filter': {'simple': {
        'date': date.isoformat() + 'T00:00:00.000Z',
        'enabled': True
    }}}
    LOG.debug('Getting WOD with params: %s', params)
    query_url = URL + _urlencode_multilevel(params)
    LOG.debug('HTTP GET %s', query_url)
    with urlopen(query_url) as f:
        response = json.load(f)
    for wod_response in response['data']:
        LOG.debug(wod_response)
        try:
            wod_datetime = datetime.strptime(
                wod_response['attributes']['date'],
                '%Y-%m-%dT%H:%M:%S.000Z'
            )
        except KeyError:
            LOG.error('WOD did not contain date attribute: %s', wod_response)
            continue
        if date == wod_datetime.date():
            return WOD(wod_response['attributes'])


_ALIASES = {
    r'DB': r'<sub alias="dumbbell">DB</sub>',
    r'KB': r'<sub alias="kettlebell">KB</sub>',
    r'#': r'<sub alias="pounds">#</sub>',
    r'(\d+)"': r'\1<sub alias="inches">"</sub>',
    r'\'': '<sub alias="feet">\'</sub>',
    r'&': 'and'
}

def _inject_aliases(text):
    for key, replacement in _ALIASES.items():
        text = re.sub(key, replacement, text)
    return text


def _fix_sets(text):
    return re.sub(r'(\d+)x(\d+)', r'\1 sets of \2', text)


def _fix_rx(text):
    return re.sub(r'(\d+[#"\'])/(\d+[#"\'])', r'\1 male, \2 female', text)


def _massage_for_tts(text):
    text = _fix_sets(text)
    text = _fix_rx(text)
    text = _inject_aliases(text)
    return text


def _convert_ssml(text, section):
    lines = text.splitlines(False)
    section = '<p>%s</p>' % section
    for i in range(len(lines)):
        lines[i] = lines[i].strip()

    if len(lines) < 2:
        return ''.join(lines)

    # make announcements/all caps/birthdays pause.
    if lines[0].upper() == lines[0] and not lines[1]:
        lines[0] = '<p>Announcement: %s</p>' % lines[0]
        lines[1] = section
        for i in range(2, len(lines)):
            lines[i] = '<s>%s</s>' % _massage_for_tts(lines[i])
    else:
        lines.insert(0, section)
        for i in range(1, len(lines)):
            lines[i] = '<s>%s</s>' % _massage_for_tts(lines[i])
    return ''.join(lines)

class WOD(object):
    def __init__(self, wod_attributes):
        self.strength_raw = wod_attributes.get('strength', '')
        self.conditioning_raw = wod_attributes.get('conditioning', '')
        self.image = wod_attributes.get('image', None)

    def speech_ssml(self):
        return '<speak>{}{}</speak>'.format(
            _convert_ssml(self.strength_raw, 'Strength Section:'),
            _convert_ssml(self.conditioning_raw, 'Conditioning:')
        )

    def pprint(self):
        return 'Strength:\n{0.strength_raw}\nConditioning:\n{0.conditioning_raw}\nImage: {0.image}'.format(self)


def _test(argv):
    logging.basicConfig(format='%(levelname)s %(filename)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    try:
        date = datetime.strptime(argv[1], '%Y-%m-%d').date()
    except IndexError:
        print('Must give me a date in format: YYYY-MM-DD')
        sys.exit(1)
    wod = get_wod(date)
    if wod:
        print(wod.pprint())
        print('SSML:')
        print(wod.speech_ssml())
    else:
        print(wod)

if __name__ == '__main__':
    _test(sys.argv)

