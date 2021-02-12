# -*- coding: utf-8 -*-
from eduid_common.config.base import EduidEnvironment

from sns_monitor.api import init_sns_monitor_api

app = init_sns_monitor_api()

if __name__ == '__main__':
    import uvicorn

    if app.state.config.environment is EduidEnvironment.dev:
        uvicorn.run('run:app', reload=True)
    else:
        uvicorn.run('run:app')
