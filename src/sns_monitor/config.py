# -*- coding: utf-8 -*-

from typing import List

from eduid_common.config.base import EduidEnvironment, LoggingConfigMixin, RootConfig
from pydantic import Field


class SNSMonitorConfig(RootConfig, LoggingConfigMixin):
    environment: EduidEnvironment = EduidEnvironment.production
    cert_cache_seconds: int = 3600
    log_format: str = '{asctime} | {levelname:7} | {hostname} | {name:35} | {module:10} | {message}'
    log_filters: List[str] = Field(default=['app_filter'])
