#! /bin/bash

# MAKE DIRECTORY TO COPY LOGS TO
mkdir /tmp/ci_collect_logs/

# MAKE DIRECTORY FOR MS SPECIFIC LOGS
mkdir /tmp/ci_collect_logs/ms_logs/
mkdir /tmp/ci_collect_logs/ms_logs/metrics-collection
mkdir /tmp/ci_collect_logs/ms_logs/plugins
mkdir /tmp/ci_collect_logs/ms_logs/rabbitmq
mkdir /tmp/ci_collect_logs/ms_logs/cobbler

# dir to export models to (if the script is ran with parameters)
if [ "$1" == "-export" ]
   then
    mkdir /tmp/ci_collect_logs/ms_logs/models
fi
list_message_files=( $(ls /var/log/ | grep messages) )
for line in "${list_message_files[@]}"
do
    cp /var/log/$line /tmp/ci_collect_logs/ms_logs/$line.log
done
#copying model files to the corresponding folder and the deleting of the models from the dir
if [ "$1" == "-export" ]
   then
    cp /tmp/a_*.xml /tmp/ci_collect_logs/ms_logs/models 2>/dev/null || true
    cp /tmp/b_*.xml /tmp/ci_collect_logs/ms_logs/models 2>/dev/null || true
    rm -f /tmp/a_*.xml
    rm -f /tmp/b_*.xml
fi
#copying the litp backup to the logs and then removal from tmp
cp /tmp/litp_backup_*.tar.gz /tmp/ci_collect_logs/ms_logs/ 2>/dev/null || true
rm -rf /tmp/litp_backup_*.tar.gz
cp /var/log/litp/metrics*.log* /tmp/ci_collect_logs/ms_logs/metrics-collection/ 2>/dev/null || true
cp /var/log/mcollective.log /tmp/ci_collect_logs/ms_logs/mcollective.log 2>/dev/null || true
cp /var/log/mcollective-audit.log /tmp/ci_collect_logs/ms_logs/mcollective-audit.log 2>/dev/null || true
cp /var/lib/litp/core/model/LAST_KNOWN_CONFIG /tmp/ci_collect_logs/ms_logs/LAST_KNOWN_CONFIG 2>/dev/null || true
cp -r /opt/ericsson/nms/litp/etc/puppet/manifests/* /tmp/ci_collect_logs/ms_logs/plugins/ 2>/dev/null || true
cp -r /var/log/rabbitmq/* /tmp/ci_collect_logs/ms_logs/rabbitmq/ 2>/dev/null || true
cp -r /var/log/cobbler/* /tmp/ci_collect_logs/ms_logs/cobbler/ 2>/dev/null || true

# MAKE DIRECTORIES FOR EACH OF THE PEER HOSTS
get_peer_nodes=( $(litp show -rp / | grep -v "inherited from" | grep -B1 "type: node" | grep -v type | grep "/") ) || echo "Failed to query litp for peer nodes, only MS logs will be collected"
for line in "${get_peer_nodes[@]}"
do
    hostnamei=( $(litp show -p $line | grep hostname | sed 's/        hostname: //g' ) )
    mkdir /tmp/ci_collect_logs/$hostnamei
    expect /tmp/key_setup.exp $hostnamei
    expect /tmp/scp_file.exp $hostnamei "/var/log/messages*" /tmp/ci_collect_logs/$hostnamei/
    cpy_mess=( $(ls /tmp/ci_collect_logs/$hostnamei/ | grep messages) )
    for line1 in "${cpy_mess[@]}"
    do
        mv /tmp/ci_collect_logs/$hostnamei/$line1 /tmp/ci_collect_logs/$hostnamei/$line1.log
    done
    expect /tmp/scp_file.exp $hostnamei /var/log/litp/litp_libvirt.log /tmp/ci_collect_logs/$hostnamei/
    expect /tmp/scp_file.exp $hostnamei "/var/VRTSvcs/log/*" /tmp/ci_collect_logs/$hostnamei/
    expect /tmp/scp_file.exp $hostnamei "/etc/VRTSvcs/conf/config/main.cf*" /tmp/ci_collect_logs/$hostnamei/
    expect /tmp/scp_file.exp $hostnamei /var/log/mcollective.log /tmp/ci_collect_logs/$hostnamei/mcollective.log
    expect /tmp/scp_file.exp $hostnamei /var/log/mcollective-audit.log /tmp/ci_collect_logs/$hostnamei/mcollective-audit.log
    expect /tmp/scp_file.exp $hostnamei "/var/coredumps/*" /tmp/ci_collect_logs/$hostnamei/
done
echo ""
presdate=( $(date +"%m-%d-%y-%H:%M:%S") )
tar -Pzcvf /tmp/litp_messages_$presdate.tar.gz /tmp/ci_collect_logs/
rm -rf /tmp/ci_collect_logs/
