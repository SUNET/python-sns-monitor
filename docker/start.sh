#!/bin/bash

set -e
set -x

. /opt/eduid/bin/activate

# These could be set from Puppet if multiple instances are deployed
eduid_name=${eduid_name-'python-sns-monitor'}
base_dir=${base_dir-"/opt/eduid/${eduid_name}"}
project_dir=${project_dir-"${base_dir}/src"}
# These *can* be set from Puppet, but are less expected to...
log_dir=${log_dir-'/var/log/eduid'}
run=${run-'/opt/eduid/python-sns-monitor/src/sns_monitor/run.py'}

chown -R eduid: "${log_dir}"

if [ -r /opt/eduid/src/python-sns-monitor/run.py ]; then
    run=/opt/eduid/src/python-sns-monitor/run.py
fi

# set PYTHONPATH if it is not already set using Docker environment
export PYTHONPATH=${PYTHONPATH-${project_dir}}
echo "PYTHONPATH=${PYTHONPATH}"

# nice to have in docker run output, to check what
# version of something is actually running.
/opt/eduid/bin/pip freeze

echo ""
echo "$0: Starting ${run}"
exec start-stop-daemon --start --quiet -c eduid:eduid \
     --pidfile "${state_dir}/${eduid_name}.pid" --make-pidfile \
     --exec /opt/eduid/bin/python3 -- $run
