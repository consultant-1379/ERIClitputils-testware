"""
"""
import os
import sys
import collect_logs_funcs
import subprocess

# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

# Install pexpect on gateway
#subprocess.call("sh install_pexpect.sh", shell=True)

MS_IP = "192.168.0.42"
MS_PASSWORD = "@dm1nS3rv3r"
MS_SCRIPTS_DIR = "vapp_collect_logs"
MS_SCRIPT = "collect_ms_logs.py"
MS_LITP_LOGS = "/root/litp_logs"

# COPY COLLECTION SCRIPTS TO MS
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

scp_scripts = "scp -r {0} root@{1}:/root/{2}".format(
        DIR_PATH, MS_IP, MS_SCRIPTS_DIR)
collect_logs_funcs.expect_cmd(scp_scripts, MS_PASSWORD)

MS_COLLECT_SCRIPT = "/root/{0}/{1}".format(MS_SCRIPTS_DIR, MS_SCRIPT)

collect_cmd = 'ssh root@{0} -C "python {1} vapp"'.format(MS_IP, MS_COLLECT_SCRIPT)
# Run script on MS to collect logs
collect_logs_funcs.expect_cmd(collect_cmd, MS_PASSWORD)

#scp_back = "scp -r root@{0}:/root/{1}/litp_logs_*.tar.gz /tmp/".format(MS_IP, MS_SCRIPTS_DIR)
#scp_back = "scp -r root@{0}:/tmp/litp_logs_*.tar.gz .".format(MS_IP, MS_SCRIPTS_DIR)
scp_back = "scp -r root@{0}:/root/litp_logs_*.tar.gz /tmp/".format(MS_IP)
# SCP the logs collected to the current machine
collect_logs_funcs.expect_cmd(scp_back, MS_PASSWORD)

remove_dirs = 'ssh root@{0} -C "rm -rf {1}; rm -rf {2}*"'.format(MS_IP, MS_SCRIPTS_DIR, MS_LITP_LOGS)
# Remove the created directories on the MS
collect_logs_funcs.expect_cmd(remove_dirs, MS_PASSWORD)
