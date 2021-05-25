# -*- coding: utf-8 -*-
from sns_monitor.api import init_sns_monitor_api
from sns_monitor.config import Environment

app = init_sns_monitor_api()

if __name__ == '__main__':
    import uvicorn

    if app.state.config.environment is Environment.dev:
        uvicorn.run('run:app', reload=True)
    else:
        uvicorn.run('run:app')
