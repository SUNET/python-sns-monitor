# -*- coding: utf-8 -*-
import json
from unittest import TestCase

from starlette.testclient import TestClient

from sns_monitor.api import app

__author__ = 'lundberg'


class TestApp(TestCase):
    def setUp(self) -> None:
        # Headers and body from AWS documentation
        self.headers = {
            'x-amz-sns-message-type': 'Notification',
            'x-amz-sns-message-id': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
            'x-amz-sns-topic-arn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
            'x-amz-sns-subscription-arn': 'arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
            'Content-Type': 'text/plain; charset=UTF-8',
        }
        self.body_test = {
            'Type': 'Notification',
            'MessageId': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
            'TopicArn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
            'Subject': 'test',
            'Message': 'test message',
            'Timestamp': '2012-04-25T21:49:25.719Z',
            'SignatureVersion': '1',
            'Signature': 'EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc=',
            'SigningCertURL': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem',
            'UnsubscribeURL': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
        }
        self.body = {
            'Message': 'HEJ 2',
            'MessageId': '811d328f-b633-5fa3-aab4-6a0f4ab56f94',
            'Signature': 'm8o/dG9QF1s86aj6mAdYk++OOe0J6yN+ZWpvRYiiQc8xrIGrOWpelaB/GMbn2XUnW6QfCtEi7RR5+YuNbJm60BILxqnlvnn0Nvjw1iT2VzLZAkIWw3g/dk9zOnlDK8vLksTwXidlQ24/DLc9cG5zfG8100/v4OMAU+1tkIaGcw95G9K3QX2I9zT99RUxvm6U04Xxzz1mUOAZ7JFw9m8xxwsIKbVWTaQsRQb6xj2Rtlb/Mpleke2TkcDCuJW7o3RmED6vpg2Ku3Tu75RunI4Dff+GSzbI+im4Yn9R9HEGJB0hAe3brrisjGVnsMYYsOW+XGIFuB5JOkvgGmtNQZW2wg==',
            'SignatureVersion': '1',
            'SigningCertURL': 'https://sns.eu-north-1.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem',
            'Timestamp': '2021-01-19T15:27:02.064Z',
            'TopicArn': 'arn:aws:sns:eu-north-1:075581119103:ft-test',
            'Type': 'Notification',
            'UnsubscribeURL': 'https://sns.eu-north-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-north-1:075581119103:ft-test:84d734c9-8872-4d86-bf4a-1b721758181d',
        }
        self.client = TestClient(app)

    def test_post_notification(self) -> None:
        response = self.client.post('/message', data=json.dumps(self.body), headers=self.headers)
        assert response.status_code == 200
        assert response.ok is True
