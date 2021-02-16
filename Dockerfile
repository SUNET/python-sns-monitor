FROM docker.sunet.se/eduid/python3env

MAINTAINER eduid-dev <eduid-dev@SEGATE.SUNET.SE>

COPY . /opt/eduid/python-sns-monitor
RUN (cd /opt/eduid/python-sns-monitor; git describe; git log -n 1) > /revision.txt
RUN rm -rf /opt/eduid/python-sns-monitor/.git
RUN /opt/eduid/bin/pip install -U pip wheel
RUN /opt/eduid/bin/pip install --index-url https://pypi.sunet.se -r /opt/eduid/python-sns-monitor/requirements.txt

COPY docker/start.sh /

EXPOSE "8000"
HEALTHCHECK --interval=27s CMD curl http://localhost:8000/status/healthy | grep -q STATUS_OK

CMD [ "/start.sh" ]
