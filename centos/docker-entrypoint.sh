#!/usr/bin/env bash
set -e

netstat -a | grep '^tcp.*8384.*LISTEN' || /usr/sbin/sshd -D &

cd ~

exec "$@"
