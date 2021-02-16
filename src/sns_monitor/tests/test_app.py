# -*- coding: utf-8 -*-
import json
import os
from typing import Optional
from unittest import TestCase, mock

import pkg_resources
from starlette.testclient import TestClient

from sns_monitor.api import init_sns_monitor_api

__author__ = 'lundberg'


class MockResponse:
    def __init__(self, content: bytes = b'', json_data: Optional[dict] = None, status_code: int = 200):
        self._content = content
        self._json_data = json_data
        self._status_code = status_code

    @property
    def content(self):
        return self._content

    @property
    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass


class TestApp(TestCase):
    def setUp(self) -> None:
        self.config = {'app_name': 'test'}
        # Load test cert
        self.datadir = pkg_resources.resource_filename(__name__, 'data')
        with open(f'{self.datadir}{os.sep}test.crt', mode='rb') as f:
            self.cert_bytes = f.read()

        # Headers and body from AWS documentation
        self.headers = {
            'x-amz-sns-message-type': 'Notification',
            'x-amz-sns-message-id': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
            'x-amz-sns-topic-arn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
            'x-amz-sns-subscription-arn': 'arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
            'Content-Type': 'text/plain; charset=UTF-8',
        }
        self.body = {
            'Type': 'Notification',
            'MessageId': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
            'TopicArn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
            'Subject': 'test',
            'Message': 'test message',
            'Timestamp': '2012-04-25T21:49:25.719Z',
            'SignatureVersion': '1',
            'Signature': 'KsQfz4uV9wgpzkHWTzcG6RG1FbyZKk0pFm1hmJ76HCleXhARkLJkUyq4gD8vF19m9zVRz2K2zxlQlSVqyzsSUUYOY4NdvfTo66fJumHM7QxQ9nfWizVwno2qEnAYFnVIffHX4B3pPUp6ySogahNFMWnbayLL251tHaoCZC3sqGeF2vZk3VpGf0f/OuDOKtdPO94o7dlqrDE5kQtq7JEFPRogX0B4nRIBSzJm/0bY6VYElo8mu2pKRd2OnwSU9ZUEdFkWKjnN7mi4fmpZcEoJhHCyN9EFRG3qyh6yyP+X+3ZP9HJVJaJbdQxCbK19IwVjfsJ1mLtvsxoOu7dztdGWKw==',
            'SigningCertURL': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem',
            'UnsubscribeURL': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
        }
        # Initialize app
        self.app = init_sns_monitor_api(test_config=self.config)
        # Setup test client
        self.client = TestClient(self.app)

    @mock.patch('requests.get')
    def test_post_notification(self, mock_get: mock.Mock) -> None:
        mock_get.return_value = MockResponse(content=self.cert_bytes)

        response = self.client.post('/messages/', data=json.dumps(self.body), headers=self.headers)
        assert response.status_code == 200
        assert response.ok is True

    @mock.patch('requests.get')
    def test_accept_notification(self, mock_get: mock.Mock) -> None:
        mock_get.return_value = MockResponse(content=self.cert_bytes)
        self.app.state.config.topic_allow_list = ['arn:aws:sns:us-west-2:123456789012:MyTopic']
        response = self.client.post('/messages/', data=json.dumps(self.body), headers=self.headers)
        assert response.status_code == 200
        assert response.ok is True

    @mock.patch('requests.get')
    def test_reject_notification(self, mock_get: mock.Mock) -> None:
        mock_get.return_value = MockResponse(content=self.cert_bytes)
        self.app.state.config.topic_allow_list = ['some_other_topic']
        response = self.client.post('/messages/', data=json.dumps(self.body), headers=self.headers)
        assert response.status_code == 400

    def test_status_healthy(self) -> None:
        response = self.client.get('/status/healthy')
        assert response.status_code == 200
        assert response.json() == {'message': 'STATUS_OK'}
