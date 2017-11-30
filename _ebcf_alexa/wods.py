from urllib.request import urlopen
from urllib.parse import urlencode
import json
import logging
from datetime import datetime, date as Date
import sys
import re
from typing import List, Iterator, Tuple, Optional
from . import env

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

URL = 'http://www.elliottbaycrossfit.com/api/v1/wods?'


def _is_announcement_line(line: str) -> bool:
    """
    Is a line of text considered an announcement line?

    Examples:

    HAPPY BIRTHDAY <person>!!!!
    NO CLASSES <>

    :param line: line to check
    :return: if the line matches an expected pattern
    """
    return bool(line) and (line.upper() == line or line.endswith('!!'))


def _split_announcement_and_strength(strength_raw: Optional[str]) -> Tuple[List[str], List[str]]:
    """
    Split the strength section into 2 sections: announcements and the actual
    strength training workout.

    Rohan sometimes starts the description of the strength training
    section with an announcement, like wishing someone happy birthday
    or announcing that a class is canceled.

    :param strength_raw: The raw strength text from the API
    :return: 2-tuple with the strength and announcements split by line
    """
    if strength_raw is None:
        return [], []
    strength_raw = strength_raw.strip()
    if not strength_raw:
        return [], []
    announcement = []
    lines = [l.strip() for l in strength_raw.splitlines(False)]
    # while we have lines to parse (whole strength can be an announcement)
    # and the line is an announcement line or empty line (multiple announcements
    # can be split by an empty line)
    while lines and (_is_announcement_line(lines[0]) or not lines[0]):
        announcement.append(lines.pop(0))
    return announcement, lines


class WOD(object):
    """
    Class representing a WOD from the EBCF API.
    """
    def __init__(self, wod_attributes: dict):
        self.announcement_lines, self.strength_lines = _split_announcement_and_strength(
            wod_attributes.get('strength', '')
        )
        self.conditioning_lines = wod_attributes.get('conditioning', '').strip().splitlines(False)
        self.image = wod_attributes.get('image', None)
        self.datetime = _safe_datetime(wod_attributes.get('date'))
        self.date = None
        if self.datetime:
            self.date = self.datetime.date()
        self.publish_datetime = _safe_datetime(wod_attributes.get('publishDate'))

    def announcement_ssml(self) -> str:
        if self.announcement_lines:
            ssml_chunks = ['<p>Announcement:']
            for line in self.announcement_lines:
                line = line.strip()
                if line:
                    ssml_chunks.append('<s>{}</s>'.format(_clean_illegal_ssml_chars(line)))
                else:
                    ssml_chunks.append('<break time="500ms"/>')
            ssml_chunks.append('</p>')
            return ''.join(ssml_chunks)
        return ''

    def announcement_pprint(self) -> str:
        if self.announcement_lines:
            return 'Announcement:\n' + '\n'.join(self.announcement_lines)
        return ''

    def strength_ssml(self) -> str:
        if self.strength_lines:
            return _convert_ssml(self.strength_lines, 'Strength Section:')
        return ''

    def strength_pprint(self) -> str:
        if self.strength_lines:
            return 'Strength:\n' + '\n'.join(self.strength_lines)
        return ''

    def conditioning_ssml(self) -> str:
        if self.conditioning_lines:
            return _convert_ssml(self.conditioning_lines, 'Conditioning:')
        return ''

    def conditioning_pprint(self) -> str:
        if self.conditioning_lines:
            return 'Conditioning:\n' + '\n'.join(self.conditioning_lines)
        return ''

    def full_ssml(self) -> str:
        return self.announcement_ssml() + self.strength_ssml() + self.conditioning_ssml()

    def pprint(self) -> str:
        return '\n'.join([
            self.announcement_pprint(),
            self.strength_pprint(),
            self.conditioning_pprint()
        ])

    def as_wod_attributes(self) -> dict:
        return {
            'strength': self.strength_raw,
            'conditioning': self.conditioning_raw,
            'image': self.image,
            'date': self.datetime.strftime(EBCF_API_TSTAMP_FMT),
            'publishDate': self.publish_datetime.strftime(EBCF_API_TSTAMP_FMT)
        }


class APIParseError(ValueError):
    """Thrown when the underlying expectations of the API stop working."""


def _urlencode_multilevel(obj: dict) -> str:
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
                sub_params[encode_key] = val
        else:
            flattened_params[parent_key] = obj
        for k, v in sub_params.items():
            _flatten_obj(v, k)

    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten_obj(v, k)

    return urlencode(flattened_params)


def _call_api(params: dict) -> dict:
    LOG.debug('EBCF API params: %s', params)
    query_url = URL + _urlencode_multilevel(params)
    LOG.debug('HTTP GET %s', query_url)
    with urlopen(query_url) as f:
        return json.load(f)


def _parse_wod_response(api_response: dict) -> Iterator[WOD]:
    LOG.debug('EBCF API response: %s', api_response)
    wod_list = api_response.get('data', [])
    for wod_data in wod_list:
        try:
            yield WOD(wod_data['attributes'])
        except KeyError:
            continue


EBCF_RANGE_STRF_FMT = '%Y-%m-%dT%H:%M:%S%z'


def get_wods_by_range(start_date: datetime, end_date: datetime) -> List[WOD]:
    """
    Gets the WOD by publishDate range.

    :param start_date: Start day
    :param end_date: End day
    :return: WOD
    :rtype: WOD
    """
    params = {'filter': {'simple': {
        'publishDate': {
            '$gt': start_date.strftime(EBCF_RANGE_STRF_FMT),
            '$lt': end_date.strftime(EBCF_RANGE_STRF_FMT)
        },
        'enabled': True
    }}}
    return list(_parse_wod_response(_call_api(params)))


def get_wod(date: Date) -> WOD:
    """
    gets the WOD for a specific day.

    :param datetime.date date: the date
    :returns: wod data or None if not found
    :rtype: WOD
    """
    params = {'filter': {'simple': {
        'date': date.strftime('%Y-%m-%d') + 'T00:00:00.000Z',
        'enabled': True
    }}}
    for wod in _parse_wod_response(_call_api(params)):
        if wod.date == date:
            return wod


_ALIASES = {
    r'OH': r'<sub alias="overhead">OH</sub>',
    r'DB': r'<sub alias="dumbbell">DB</sub>',
    r'KB': r'<sub alias="kettlebell">KB</sub>',
    r'EMOM': r'every minute on the minute',
    r'E(\d)MOM': r'every \1 minutes on the minute',
    r'HSPU': r'hand stand push ups',
    r'#': r'<sub alias="pounds">#</sub>',
    r'(\d+)"': r'\1<sub alias="inches">"</sub>',
    r'(\d+)\'': r'\1<sub alias="feet">\'</sub>',
    r'&': 'and',
    r'(\d+) [Ss]ec\.? ': r'\1 second ',
    r'\bT2B\b': r'<sub alias="toes to bar">T2B</sub>'
}


def _inject_aliases(text: str) -> str:
    for key, replacement in _ALIASES.items():
        text = re.sub(key, replacement, text)
    return text


def _fix_sets(text: str) -> str:
    return re.sub(r'(\d+)x(\d+)', r'\1 sets of \2', text)


def _fix_rx(text: str) -> str:
    return re.sub(r'(\d+[#"\'])/(\d+[#"\'])', r'<prosody rate="fast">\1 male, \2 female</prosody>', text)


def _clean_illegal_ssml_chars(text: str) -> str:
    return text.replace('&', 'and')


def _massage_for_tts(text: str) -> str:
    text = _fix_sets(text)
    text = _fix_rx(text)
    text = _inject_aliases(text)
    return text


def _convert_ssml(lines: List[str], section: str) -> str:
    section = '<p>%s</p>' % section
    new_lines = [
        '<s>{}</s>'.format(_massage_for_tts(l))
        for l in lines
    ]
    return section + ''.join(new_lines)


EBCF_API_TSTAMP_FMT = '%Y-%m-%dT%H:%M:%S.000Z'


def _safe_datetime(datestr: str) -> datetime:
    """Tries to convert a timestamp into a datetime object, without crashing.

    :param datestr: date string
    :returns: datetime object set to UTC or None
    """
    if not datestr:
        return None
    try:
        return env.UTC.localize(datetime.strptime(datestr, EBCF_API_TSTAMP_FMT))
    except ValueError:
        return None


def _test(argv: List[str]) -> None:
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
        print(wod.full_ssml())
    else:
        print(wod)


if __name__ == '__main__':
    _test(sys.argv)

