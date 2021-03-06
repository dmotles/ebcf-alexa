from _ebcf_alexa import env
from _ebcf_alexa import wods
from _ebcf_alexa.speechlet import SSML as assert_valid_ssml  # not really an assert, but this does do validation
from datetime import datetime, date
from textwrap import dedent
from unittest.mock import patch, Mock
import io
import pytest
import urllib.parse as parse
from urllib.error import HTTPError
from http.client import HTTPMessage

class TestWOD(object):
    def test_rohan_forgot_to_put_conditioning_or_strength_in(self):
        wods.WOD({'enabled': True, 'title': None, 'date': '2018-01-13T00:00:00.000Z',
                  'publishDate': '2018-01-13T05:00:00.000Z', 'image': None, 'strength': None,
                  'conditioning': None, 'description': None, 'videoId': None})


SAMPLE_WOD_JSON = r"""
{"links": {
    "self": "http://www.elliottbaycrossfit.com/api/v1/wods?filter%5Bsimple%5D%5Bdate%5D=2017-07-03T00%3A00%3A00.000Z&filter%5Bsimple%5D%5Benabled%5D=true"},
 "data": [{"id": "595546898a91720004306145", "type": "wods",
           "attributes": {"enabled": true, "title": null, "date": "2017-07-03T00:00:00.000Z",
                          "publishDate": "2017-07-03T04:00:00.000Z",
                          "image": "http://ebcf.s3.amazonaws.com/20170703.jpg",
                          "strength": "HAPPY BIRTHDAY KELSEY!!!!\n\nTempo Back Squat\n3x10 (3 sec down, 2 sec pause at bottom, 1 sec rise)",
                          "conditioning": "3 Rounds\n400 m Run\n15 Hang Power Cleans 115#/95#\n15 Thrusters 115#/95#\n\n20 Min Cap",
                          "description": null, "videoId": null},
           "links": {"self": "http://localhost:4500/api/v1/wods/595546898a91720004306145"}, "relationships": {"tags": {
         "data": [{"type": "tags", "id": "56e61406e17eab8d035f2a4b"},
                  {"type": "tags", "id": "5955467d8a91720004306144"},
                  {"type": "tags", "id": "58e6be89d795e30004729a33"},
                  {"type": "tags", "id": "594183dfeb66da000430d0d6"},
                  {"type": "tags", "id": "5840a16a7283fd0400cb4eb6"},
                  {"type": "tags", "id": "595b079eb938b80004f26bf5"}],
         "links": {"self": "http://localhost:4500/api/v1/wods/relationships/tags"}}}}]}
""".strip()


BROKEN_WOD_JSON = r"""
{"meta": {}, "links": {
    "self": "http://www.elliottbaycrossfit.com/api/v1/wods?filter%5Bsimple%5D%5Bdate%5D=2018-01-13T00%3A00%3A00.000Z&filter%5Bsimple%5D%5Benabled%5D=true"},
 "data": [{"id": "5a542d6ca8277d0004cc9df7", "type": "wods",
           "attributes": {"enabled": true, "title": null, "date": "2018-01-13T00:00:00.000Z",
                          "publishDate": "2018-01-13T05:00:00.000Z", "image": null, "strength": null,
                          "conditioning": null, "description": null, "videoId": null},
           "links": {"self": "http://localhost:4500/api/v1/wods/5a542d6ca8277d0004cc9df7"}, "relationships": {
         "tags": {"data": [{"type": "tags", "id": "5a542d65a8277d0004cc9df5"}],
                  "links": {"self": "http://localhost:4500/api/v1/wods/relationships/tags"}}}}]}
""".strip()


def mock_urlopen(urlstr: str):
    parsed = parse.urlparse(urlstr)
    query = parse.parse_qs(parsed.query)
    query_date = query['filter[simple][date]'][0]
    # for some reason, parse_qs puts values inside lists.
    if query_date == '2017-07-03T00:00:00.000Z':
        return io.StringIO(SAMPLE_WOD_JSON)
    elif query_date == '2018-01-13T00:00:00.000Z':
        return io.StringIO(BROKEN_WOD_JSON)
    assert False, 'Mock not supported for this date'


@pytest.yield_fixture
def fake_urlopen():
    m = Mock(side_effect=mock_urlopen)
    with patch.object(wods, 'urlopen', m) as urlopen:
        yield urlopen


@pytest.mark.parametrize(
    'input_,expected', [
        # nested dictionary example
        ({'filter': {'simple': {'date': '2017-07-03'}}},
         'filter%5Bsimple%5D%5Bdate%5D=2017-07-03'),

        # nested dictionary with list
        ({'outer': {'inner': ['item0', 'item1']}},
         'outer%5Binner%5D%5B0%5D=item0&outer%5Binner%5D%5B1%5D=item1')
    ],
    ids=[
        'nested-dict',
        'nested-list'
    ]
)
def test_url_encode_multilevel(input_, expected):
    assert wods._urlencode_multilevel(input_) == expected


def test_get_wod_e2e(fake_urlopen):
    """This exercises the whole code path for get_wod, including parsing the json
    into an object."""
    wod = wods.get_wod(date(2017, 7, 3))
    urlstr = fake_urlopen.call_args[0][0]
    parsedurl = parse.urlparse(urlstr)
    query = parse.parse_qs(parsedurl.query)
    # parse_qs puts values inside lists, so its the first item.
    assert query['filter[simple][date]'][0] == '2017-07-03T00:00:00.000Z'
    assert query['filter[simple][enabled]'][0] == 'True'
    assert parsedurl.path == '/api/v1/wods'
    assert parsedurl.hostname == 'www.elliottbaycrossfit.com'
    assert wod.date == date(2017, 7, 3)
    assert wod.datetime == datetime(2017, 7, 3, tzinfo=env.UTC)
    assert wod.publish_datetime == datetime(2017, 7, 3, 4, tzinfo=env.UTC)
    assert wod.image == 'http://ebcf.s3.amazonaws.com/20170703.jpg'
    assert 'HAPPY BIRTHDAY KELSEY!!!!' in wod.announcement_lines


def test_get_wod_e2e_broken_wod(fake_urlopen):
    """see fixture setup. This is a workout without strength or conditioning,
    so its pretty much empty"""
    assert wods.get_wod(date(2018, 1, 13)) is None


def test_get_wod_with_401_error(fake_urlopen):
    """
    The EBCF website returns 401's for workouts that are not yet released.
    """
    def raise_401(url):
        raise HTTPError(url, 401, 'UNAUTHORIZED', HTTPMessage(), fp=None)
    fake_urlopen.side_effect = raise_401
    assert wods.get_wod(date(2018, 1, 13)) is None


@pytest.mark.parametrize(
    ['input_', 'expected'], [
        ('24 Min AMRAP', False),
        ('Tempo Front Squat', False),
        ('EMOM for 14 Min', False),
        ('HAPPY BIRTHDAY KELSEY!!!!', True),
        ('HAPPY BIRTHDAY SARAH!!!!', True),
        ('HAPPY BIRTHDAY MARIE!!!!', True),
        ('THIS IS WORKOUT #1000!!!!', True),
        ('NO EVENING CLASSES TODAY', True),
        ('', False)
    ],
    ids=repr
)
def test_is_announcement_line(input_: str, expected: bool):
    assert wods._is_announcement_line(input_) == expected


DOUBLE_ANNOUNCEMENT = """
ONLY 9 & 10:30 AM CLASSES

HAPPY BIRTHDAY SARAH!!!!
""".strip()


DOUBLE_ANNOUNCEMENT_EXPECTED = (
    ['ONLY 9 & 10:30 AM CLASSES', '', 'HAPPY BIRTHDAY SARAH!!!!'],
    []
)


CONCATENATED_ANNOUNCEMENT = """
HAPPY BIRTHDAY ZLATKO!!!!
15 Min to establish
1 Power Clean + 1 Split Jerk Right + 1 Split Jerk Left
""".strip()


CONCATENATED_ANNOUNCEMENT_EXPECTED = (
    ['HAPPY BIRTHDAY ZLATKO!!!!'],
    ['15 Min to establish', '1 Power Clean + 1 Split Jerk Right + 1 Split Jerk Left']
)


SPLIT_ANNOUNCEMENT = """
HAPPY BIRTHDAY BRIANNE!!!!

Establish:
Max Height Box Jump
& 
Max Distance Broad Jump
""".strip()


SPLIT_ANNOUNCEMENT_EXPECTED = (
    ['HAPPY BIRTHDAY BRIANNE!!!!', ''],
    ['Establish:', 'Max Height Box Jump', '&', 'Max Distance Broad Jump']
)


NO_ANNOUNCEMENT = """
EMOM for 14 Min
3 Squat Snatches 
Focus on mechanics of stringing together the snatches
""".strip()


NO_ANNOUNCEMENT_EXPECTED = (
    [],
    ['EMOM for 14 Min', '3 Squat Snatches',
     'Focus on mechanics of stringing together the snatches']
)


@pytest.mark.parametrize(
    ['input_', 'expected'], [
        (DOUBLE_ANNOUNCEMENT, DOUBLE_ANNOUNCEMENT_EXPECTED),
        (CONCATENATED_ANNOUNCEMENT, CONCATENATED_ANNOUNCEMENT_EXPECTED),
        (SPLIT_ANNOUNCEMENT, SPLIT_ANNOUNCEMENT_EXPECTED),
        (NO_ANNOUNCEMENT, NO_ANNOUNCEMENT_EXPECTED),
        ('', ([], [])),  # EMPTY_STRENGTH
        (None, ([], [])), # NONE STRENGTH
        ('\n \n', ([], []))  # EMPTY_STRENGTH_WITH_NEWLINES
    ],
    ids=['DOUBLE_ANNOUNCEMENT', 'CONCATENATED_ANNOUNCEMENT',
         'SPLIT_ANNOUNCEMENT', 'NO_ANNOUNCEMENT',
         'EMPTY_STRENGTH', 'NONE_STRENGTH',
         'EMPTY_STRENGTH_WITH_NEWLINES']
)
def test_split_announcement_and_strength(input_: str, expected: tuple):
    assert wods._split_announcement_and_strength(input_) == expected


MASSAGE_FOR_TTS_TESTS = [
    ('don\'t', 'don\'t'),
]


@pytest.mark.parametrize('_input,expected', MASSAGE_FOR_TTS_TESTS)
def test__massage_for_TTS(_input, expected):
    assert wods._massage_for_tts(_input) == expected


class TestSSMLTranslation(object):
    def test_11_30_2017_T2B_Times_And_Plus(self):
        """
        This represents a strength section that had a lot of weird alexa-isms on
        11/30/2017
        """
        api_strength_sample = dedent("""
        EMOM for 14 Min:
        Even: 25 Sec Handstand Hold
        Odd: (Strict T2B + Strict T2B Left + Strict T2B Right) x 3 or Skin the Cat + Invert + Front Lever Tuck + 3 Strict Toe to Rings 
        """).splitlines(True)

        output = wods._convert_ssml(api_strength_sample, 'Strength')
        print(output)
        assert output.count('<sub alias="toes to bar">T2B</sub>') == 3
        assert ' times 3' in output
        assert ' x 3 ' not in output
        assert output.count('<break strength="strong"/> + ') == 5
        assert_valid_ssml(output)
