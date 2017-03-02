# pylint: disable=protected-access

from unittest import TestCase

from apns2.payload import Payload, PayloadAlert


class PayloadTestCase(TestCase):

    def setUp(self):
        self.payload_alert = payload_alert = PayloadAlert(
            title='title', title_localized_key='loc_k', title_localized_args='loc_a',
            body='body', body_localized_key='body_loc_k', body_localized_args='body_loc_a',
            action_localized_key='ac_loc_k', action='send',
            launch_image='img')

    def test_payload(self):
        payload = Payload(
            alert='my_alert', badge=2, sound='chime',
            content_available=1, mutable_content=3,
            category='my_category', url_args='args', custom={'extra': 'something'}, thread_id=42)
        self.assertEqual(payload.dict(), {
            'aps': {
                'alert': 'my_alert',
                'badge': 2,
                'sound': 'chime',
                'content-available': 1,
                'mutable-content': 1,
                'thread-id': 42,
                'category': 'my_category',
                'url-args': 'args'
            },
            'extra': 'something'
        })

    def test_payload_with_payload_alert(self):
        payload = Payload(
            alert=self.payload_alert, badge=2, sound='chime',
            content_available=1, mutable_content=1,
            category='my_category', url_args='args', custom={'extra': 'something'}, thread_id=42)
        self.assertEqual(payload.dict(), {
            'aps': {
                'alert': {
                    'title': 'title',
                    'title-loc-key': 'loc_k',
                    'title-loc-args': 'loc_a',
                    'body': 'body',
                    'loc-key': 'body_loc_k',
                    'loc-args': 'body_loc_a',
                    'action-loc-key': 'ac_loc_k',
                    'action': 'send',
                    'launch-image': 'img'
                },
                'badge': 2,
                'sound': 'chime',
                'content-available': 1,
                'mutable-content': 1,
                'thread-id': 42,
                'category': 'my_category',
                'url-args': 'args',
            },
            'extra': 'something'
        })

    def test_payload_alert(self):
        self.assertEqual(self.payload_alert.dict(), {
            'title': 'title',
            'title-loc-key': 'loc_k',
            'title-loc-args': 'loc_a',
            'body': 'body',
            'loc-key': 'body_loc_k',
            'loc-args': 'body_loc_a',
            'action-loc-key': 'ac_loc_k',
            'action': 'send',
            'launch-image': 'img'
        })
