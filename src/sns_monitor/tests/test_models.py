# -*- coding: utf-8 -*-
import json
from unittest import TestCase

from sns_monitor.models import SNSMessage

__author__ = 'lundberg'


class TestSNSMessage(TestCase):
    def setUp(self) -> None:
        self.data = {
            'Type': 'Notification',
            'MessageId': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
            'TopicArn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
            'Subject': 'test',
            'Message': 'test message',
            'Timestamp': '2012-04-25T21:49:25.719000+00:00',
            'SignatureVersion': '1',
            'Signature': 'EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc=',
            'SigningCertURL': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem',
            'UnsubscribeURL': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
        }

    def test_serialize_deserialize(self):
        message = SNSMessage.parse_obj(self.data)
        message2 = SNSMessage.parse_obj(message.dict(by_alias=True))
        assert message == message2
        assert json.dumps(self.data, sort_keys=True) == message2.json(by_alias=True, exclude_none=True, sort_keys=True)
