MAX_PAYLOAD_SIZE = 4096


class PayloadAlert(object):
    def __init__(self, title=None, title_localized_key=None, title_localized_args=None,
                 body=None, body_localized_key=None, body_localized_args=None,
                 action_localized_key=None,
                 launch_image=None
                 ):
        self.title = title
        self.title_localized_key = title_localized_key
        self.title_localized_args = title_localized_args
        self.body = body
        self.body_localized_key = body_localized_key
        self.body_localized_args = body_localized_args
        self.action_localized_key = action_localized_key
        self.launch_image = launch_image

    def dict(self):
        result = {}

        if self.title:
            result['title'] = self.title
        if self.title_localized_key:
            result['title-loc-key'] = self.title_localized_key
        if self.title_localized_args:
            result['title-loc-args'] = self.title_localized_args

        if self.body:
            result['body'] = self.body
        if self.body_localized_key:
            result['loc-key'] = self.body_localized_key
        if self.body_localized_args:
            result['loc-args'] = self.body_localized_args

        if self.action_localized_key:
            result['action-loc-key'] = self.action_localized_key

        if self.launch_image:
            result['launch-image'] = self.launch_image

        return result


class Payload(object):
    def __init__(self, alert=None, badge=None, sound=None,
                 content_available=False, mutable_content=False,
                 category=None, custom=None):
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.content_available = content_available
        self.category = category
        self.custom = custom
        self.mutable_content = mutable_content

    def dict(self):
        result = {
            'aps': {}
        }
        if self.alert is not None:
            if isinstance(self.alert, PayloadAlert):
                result['aps']['alert'] = self.alert.dict()
            else:
                result['aps']['alert'] = self.alert
        if self.badge is not None:
            result['aps']['badge'] = self.badge
        if self.sound is not None:
            result['aps']['sound'] = self.sound
        if self.content_available:
            result['aps']['content-available'] = 1
        if self.mutable_content:
            result['aps']['mutable-content'] = 1
        if self.category is not None:
            result['aps']['category'] = self.category
        if self.custom is not None:
            result.update(self.custom)

        return result
