MAX_PAYLOAD_SIZE = 4096


class PayloadAlert(object):
    def __init__(self, title=None, title_localized_key=None,
                 title_localized_args=None, body=None,
                 body_localized_key=None, body_localized_args=None,
                 action_localized_key=None, launch_image=None
                 ):

        self.__result = {
            'title': title,
            'title-loc-key': title_localized_key,
            'title-loc-args': title_localized_args,

            'body': body,
            'loc-key': body_localized_key,
            'loc-args': body_localized_args,

            'action-loc-key': action_localized_key,
            'launch-image': launch_image
        }

    def dict(self):
        # Remove keys without value
        return {k: self.__result[k] for k in self.__result if self.__result[k]}


class Payload(object):
    def __init__(self, alert=None, badge=None, sound=None,
                 content_available=False, mutable_content=False,
                 category=None, custom=None):

        self.__aps = {
            'alert': alert,
            'badge': badge,
            'sound': sound,
            'content-available': 1 if content_available else None,
            'mutable-content': 1 if mutable_content else None,
            'category': category
        }

        self.custom = custom

    def dict(self):
        # Remove keys without value
        aps = {k: self.__aps[k] for k in self.__aps if self.__aps[k]}
        result = {
            'aps': aps
        }
        
        if self.custom is not None:
            result.update(self.custom)

        return result
