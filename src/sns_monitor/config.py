# -*- coding: utf-8 -*-
import json
import logging
import os
from enum import Enum
from functools import wraps
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, TypeVar

import yaml
from nacl import encoding, exceptions, secret
from pydantic import BaseSettings, Field

TRootConfigSubclass = TypeVar('TRootConfigSubclass', bound='RootConfig')


class Environment(str, Enum):
    dev = 'dev'
    staging = 'staging'
    production = 'production'


class RootConfig(BaseSettings):
    app_name: str
    debug: bool = False
    testing: bool = False


class LoggingFilters(str, Enum):
    """ Identifiers to coherently map elements in LocalContext.filters to filter classes in logging dictConfig. """

    DEBUG_TRUE: str = 'require_debug_true'
    DEBUG_FALSE: str = 'require_debug_false'
    NAMES: str = 'app_filter'
    SESSION_USER: str = 'user_filter'


class LoggingConfigMixin(BaseSettings):
    app_name: str
    testing: bool = False
    debug: bool = False
    # If this list contains anything, debug logging will only be performed for these users
    debug_eppns: Sequence[str] = Field(default=[])
    log_format: str = '{asctime} | {levelname:7} | {hostname} | {name:35} | {module:10} | {message}'
    log_level: str = 'INFO'
    log_filters: List[str] = Field(default=['app_filter'])
    logging_config: dict = Field(default={})


class SNSMonitorConfig(RootConfig, LoggingConfigMixin):
    environment: Environment = Environment.production
    cert_cache_seconds: int = 3600
    topic_allow_list: List[str] = []


def load_config(
    typ: Type[TRootConfigSubclass], ns: str, app_name: str, test_config: Optional[Mapping[str, Any]] = None,
) -> TRootConfigSubclass:
    """ Figure out where to load configuration from, and do it. """
    app_path = os.environ.get('CONFIG_NS', f'/{ns}/{app_name}/')
    common_path = os.environ.get('CONFIG_COMMON_NS', f'/{ns}/common/')
    yaml_file = os.environ.get('CONFIG_YAML')
    config: Dict[str, Any] = {}

    if test_config:
        res = typ(**test_config)
    elif yaml_file:
        parser = YamlConfigParser(path=Path(yaml_file))

        if common_path:
            common_config = parser.read_configuration(common_path)
            config.update(common_config)

        app_config = parser.read_configuration(app_path)
        config.update(app_config)

        if 'app_name' not in config:
            config['app_name'] = app_name

        res = typ(**config)
    else:
        # Try to load the config with env vars
        res = typ()

    # Save config to a file in /dev/shm for introspection
    fd_int = os.open(f'/dev/shm/{app_name}_config.yaml', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd_int, 'w') as fd:
        fd.write('---\n')
        # have to take the detour over json to get things like enums serialised to strings
        yaml.safe_dump(json.loads(res.json()), fd)

    return res


def decrypt(f):
    @wraps(f)
    def decrypt_decorator(*args, **kwargs):
        config_dict = f(*args, **kwargs)
        decrypted_config_dict = decrypt_config(config_dict)
        return decrypted_config_dict

    return decrypt_decorator


def read_secret_key(key_name: str) -> bytes:
    """
    :param key_name: Key file name
    :return: 32 bytes of secret data
    """
    sanitized_key_name = "".join([c for c in key_name if c.isalpha() or c.isdigit() or c == '_'])
    fp = '/run/secrets/{}'.format(sanitized_key_name)
    with open(fp) as f:
        return encoding.URLSafeBase64Encoder.decode(f.readline())


def init_secret_box(key_name: Optional[str] = None, secret_key: Optional[bytes] = None) -> secret.SecretBox:
    """
    :param key_name: Key file name
    :param secret_key: 32 bytes of secret data
    :return: SecretBox
    """
    if not secret_key:
        if not key_name:
            raise Exception('Can not initialize a SecretBox without either key_name or secret_key')
        secret_key = read_secret_key(key_name)
    return secret.SecretBox(secret_key)


def decrypt_config(config_dict: Mapping) -> Mapping:
    """
    :param config_dict: Configuration dictionary
    :return: Configuration dictionary
    """
    boxes: dict = {}
    new_config_dict: dict = {}
    for key, value in config_dict.items():
        if key.lower().endswith('_encrypted'):
            decrypted = False
            for item in value:
                key_name = item['key_name']
                encrypted_value = item['value']

                if not boxes.get(key_name):
                    try:
                        boxes[key_name] = init_secret_box(key_name=key_name)
                    except IOError as e:
                        logging.error(e)
                        continue  # Try next key
                try:
                    encrypted_value = bytes(encrypted_value, 'ascii')
                    decrypted_value = (
                        boxes[key_name].decrypt(encrypted_value, encoder=encoding.URLSafeBase64Encoder).decode('utf-8')
                    )
                    new_config_dict[key[:-10]] = decrypted_value
                    decrypted = True
                    break  # Decryption successful, do not try any more keys
                except exceptions.CryptoError as e:
                    logging.error(e)
                    continue  # Try next key
            if not decrypted:
                logging.error('Failed to decrypt {}:{}'.format(key, value))
        else:
            new_config_dict[key] = value
    return new_config_dict


def interpolate(f):
    @wraps(f)
    def interpolation_decorator(*args, **kwargs):
        config_dict = f(*args, **kwargs)
        interpolated_config_dict = interpolate_config(config_dict)
        for key in list(interpolated_config_dict.keys()):
            if key.lower().startswith('var_'):
                del interpolated_config_dict[key]
        return interpolated_config_dict

    return interpolation_decorator


def interpolate_list(config_dict: dict, sub_list: list) -> list:
    """
    :param config_dict: Configuration dictionary
    :param sub_list: Sub configuration list

    :return: Configuration list
    """
    for i in range(0, len(sub_list)):
        item = sub_list[i]
        # Substitute string items
        if isinstance(item, str) and '$' in item:
            template = Template(item)
            sub_list[i] = template.safe_substitute(config_dict)
        # Call interpolate_config with dict items
        if isinstance(item, dict):
            sub_list[i] = interpolate_config(config_dict, item)
        # Recursively call interpolate_list for list items
        if isinstance(item, list):
            sub_list[i] = interpolate_list(config_dict, item)
    return sub_list


def interpolate_config(config_dict: dict, sub_dict: Optional[dict] = None) -> dict:
    """
    :param config_dict: Configuration dictionary
    :param sub_dict: Sub configuration dictionary

    :return: Configuration dictionary
    """
    if not sub_dict:
        sub_dict = config_dict
    # XXX case insensitive substitution - transitioning to lc config
    ci_config_dict = {}
    for k, v in config_dict.items():
        ci_config_dict[k] = v
        ci_config_dict[k.upper()] = v
    for key, value in sub_dict.items():
        # Substitute string values
        if isinstance(value, str) and '$' in value:
            template = Template(value)
            sub_dict[key] = template.safe_substitute(ci_config_dict)

        # Check if lists contain string values, dicts or more lists
        # Offloaded to interpolate_list
        if isinstance(value, list):
            sub_dict[key] = interpolate_list(ci_config_dict, value)

        # Recursively call interpolate_config for sub dicts
        if isinstance(value, dict):
            sub_dict[key] = interpolate_config(ci_config_dict, value)
    return sub_dict


class YamlConfigParser:
    def __init__(self, path: Path):
        self.path = path

    @interpolate
    @decrypt
    def read_configuration(self, path: str) -> Mapping[str, Any]:
        with self.path.open() as fd:
            import yaml

            data = yaml.safe_load(fd)

        # traverse the loaded data to the right namespace, discarding everything else
        for this in path.split('/'):
            if not this:
                continue
            data = data[this]

        # lowercase all keys
        lc_data = {k.lower(): v for k, v in data.items()}

        return lc_data
