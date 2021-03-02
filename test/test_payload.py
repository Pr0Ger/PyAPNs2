import pytest

from apns2.payload import Payload, PayloadAlert


@pytest.fixture
def payload_alert():
    return PayloadAlert(
        title='title',
        title_localized_key='title_loc_k',
        title_localized_args=['title_loc_a'],
        subtitle='subtitle',
        subtitle_localized_key='subtitle_loc_k',
        subtitle_localized_args=['subtitle_loc_a'],
        body='body',
        body_localized_key='body_loc_k',
        body_localized_args=['body_loc_a'],
        action_localized_key='ac_loc_k',
        action='send',
        launch_image='img'
    )


def test_payload_alert(payload_alert):
    assert payload_alert.dict() == {
        'title': 'title',
        'title-loc-key': 'title_loc_k',
        'title-loc-args': ['title_loc_a'],
        'subtitle': 'subtitle',
        'subtitle-loc-key': 'subtitle_loc_k',
        'subtitle-loc-args': ['subtitle_loc_a'],
        'body': 'body',
        'loc-key': 'body_loc_k',
        'loc-args': ['body_loc_a'],
        'action-loc-key': 'ac_loc_k',
        'action': 'send',
        'launch-image': 'img'
    }


def test_payload():
    payload = Payload(
        alert='my_alert', badge=2, sound='chime',
        content_available=True, mutable_content=True,
        category='my_category', url_args='args', custom={'extra': 'something'}, thread_id='42')
    assert payload.dict() == {
        'aps': {
            'alert': 'my_alert',
            'badge': 2,
            'sound': 'chime',
            'content-available': 1,
            'mutable-content': 1,
            'thread-id': '42',
            'category': 'my_category',
            'url-args': 'args'
        },
        'extra': 'something'
    }


def test_payload_with_payload_alert(payload_alert):
    payload = Payload(
        alert=payload_alert, badge=2, sound='chime',
        content_available=True, mutable_content=True,
        category='my_category', url_args='args', custom={'extra': 'something'}, thread_id='42')
    assert payload.dict() == {
        'aps': {
            'alert': {
                'title': 'title',
                'title-loc-key': 'title_loc_k',
                'title-loc-args': ['title_loc_a'],
                'subtitle': 'subtitle',
                'subtitle-loc-key': 'subtitle_loc_k',
                'subtitle-loc-args': ['subtitle_loc_a'],
                'body': 'body',
                'loc-key': 'body_loc_k',
                'loc-args': ['body_loc_a'],
                'action-loc-key': 'ac_loc_k',
                'action': 'send',
                'launch-image': 'img'
            },
            'badge': 2,
            'sound': 'chime',
            'content-available': 1,
            'mutable-content': 1,
            'thread-id': '42',
            'category': 'my_category',
            'url-args': 'args',
        },
        'extra': 'something'
    }
