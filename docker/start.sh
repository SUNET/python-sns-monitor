#!/bin/bash

set -e
set -x

. /opt/eduid/bin/activate

# These could be set from Puppet if multiple instances are deployed
eduid_name=${eduid_name-'python-sns-monitor'}
app_name=${app_name-'sns_monitor'}
base_dir=${base_dir-"/opt/eduid/${eduid_name}"}
project_dir=${project_dir-"${base_dir}/src"}
# These *can* be set from Puppet, but are less expected to...
log_dir=${log_dir-'/var/log/eduid'}
state_dir=${state_dir-"/var/run/${eduid_name}"}
config_ns=/eduid/api/${app_name}
# These *can* be set from Puppet, but are less expected to...
workers=${workers-1}
worker_class=${worker_class-"uvicorn.workers.UvicornWorker"}
worker_threads=${worker_threads-1}
# Need to tell Gunicorn to trust the X-Forwarded-* headers
forwarded_allow_ips=${forwarded_allow_ips-'*'}

mkdir -p "${log_dir}" "${state_dir}"
chown -R eduid: "${log_dir}" "${state_dir}"

# set PYTHONPATH if it is not already set using Docker environment
export PYTHONPATH=${PYTHONPATH-${project_dir}}
echo "PYTHONPATH=${PYTHONPATH}"

# nice to have in docker run output, to check what
# version of something is actually running.
/opt/eduid/bin/pip freeze

if [ -f "/opt/eduid/src/python-sns-monitor/setup.py" ]; then
    # developer mode, restart on code changes
    extra_args="--reload"
fi

echo ""
echo "$0: Starting ${eduid_name}"

export EDUID_CONFIG_NS=${EDUID_CONFIG_NS-${config_ns}}

echo "Reading settings from: ${EDUID_CONFIG_NS-'No namespace set'}"
exec start-stop-daemon --start --quiet -c eduid:eduid --exec \
     /opt/eduid/bin/gunicorn \
     --pidfile "${state_dir}/${eduid_name}.pid" \
     --user=eduid --group=eduid -- \
     --bind 0.0.0.0:8080 \
     --workers ${workers} --worker-class ${worker_class} \
     --forwarded-allow-ips=${forwarded_allow_ips} \
     --access-logfile "${log_dir}/${eduid_name}-access.log" \
     --error-logfile "${log_dir}/${eduid_name}-error.log" \
     --capture-output \
     ${extra_args} sns_monitor.run:app
