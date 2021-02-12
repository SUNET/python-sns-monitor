# -*- coding: utf-8 -*-

__author__ = 'lundberg'

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from sns_message_validator.sns_message_validator import SNSMessageValidator

message = {
    'Type': 'Notification',
    'MessageId': 'da41e39f-ea4d-435a-b922-c6aae3915ebe',
    'TopicArn': 'arn:aws:sns:us-west-2:123456789012:MyTopic',
    'Subject': 'test',
    'Message': 'test message',
    'Timestamp': '2012-04-25T21:49:25.719Z',
    'SignatureVersion': '1',
    'Signature': None,
    'SigningCertURL': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem',
    'UnsubscribeURL': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789012:MyTopic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55',
}

validator = SNSMessageValidator()

with open('test.key', mode='rb') as f:
    key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

plain_text = validator._get_plaintext_to_sign(message).encode()
signature = key.sign(plain_text, PKCS1v15(), hashes.SHA1())
message['Signature'] = base64.b64encode(signature).decode()
print(message)
