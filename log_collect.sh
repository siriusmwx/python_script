#!/bin/bash
current_dir=$(
    cd $(dirname $0)
    pwd
)
cd ${current_dir}
log_dir=$(date '+%Y-%m-%d_%H%M%S')
mkdir -p log_dir
collect_log=${log_dir}/$(date '+%Y-%m-%d_%H%M%S').log
echo_log() {
    echo -e "[INFO $(date '+%Y%m%d:%H%M%S')] $@" | tee -a $collect_log
}

trap 'echo -e "\nthe collect log is ${collect_log}." && exit 1' SIGINT
while :; do
    echo_log $(df -h | grep /mnt/share)
    ls -l $1 >>${collect_log}
    du -sh $1 >>${collect_log}
    sleep 60
    file_size=$(du ${collect_log} | awk '{print $1}' | grep -oE '^[0-9]+')
    if [ ${file_size} -gt 1024 ]; then
        collect_log=${log_dir}/$(date '+%Y-%m-%d_%H%M%S').log
    fi
done
