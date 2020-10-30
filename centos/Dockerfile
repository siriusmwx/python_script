FROM centos:centos8

RUN \
    mv /etc/yum.repos.d/CentOS-AppStream.repo /etc/yum.repos.d/CentOS-AppStream.repo.bak \
    && mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak \
    && mv /etc/yum.repos.d/CentOS-centosplus.repo /etc/yum.repos.d/CentOS-centosplus.repo.bak \
    && mv /etc/yum.repos.d/CentOS-Extras.repo /etc/yum.repos.d/CentOS-Extras.repo.bak \
    && mv /etc/yum.repos.d/CentOS-PowerTools.repo /etc/yum.repos.d/CentOS-PowerTools.repo.bak \
    && curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-8.repo \
    && dnf makecache && dnf -y update \
    && dnf install -y openssh-server net-tools passwd \
    && sed -i \
    's|^#Port 22|Port 8384|g; \
     s|^#PubkeyAuthentication yes|PubkeyAuthentication yes|g;' \
    /etc/ssh/sshd_config \
    && ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N '' \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key -N ''
# && echo "password" | passwd --stdin root

WORKDIR /root

COPY docker-entrypoint.sh /usr/local/bin

EXPOSE 8384

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/bin/bash"]
