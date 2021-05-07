# -*- coding: utf-8 -*-
from datetime import datetime, timezone

__author__ = 'lundberg'


def utc_now() -> datetime:
    """ Return current time with tz=UTC """
    return datetime.now(tz=timezone.utc)
