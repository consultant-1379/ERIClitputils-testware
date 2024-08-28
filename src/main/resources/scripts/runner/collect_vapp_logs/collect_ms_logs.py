"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes

Collects logs from the MS creating relevant directories to store logs in.
Calls script to collect peer node logs. This script then copies node logs here.

Read the README file to find out how to run this script!
"""

import sys
import subprocess
import pexpect
import os.path
import glob
import time
import collect_logs_funcs


SYSTEM = sys.argv[1]  # Env number for tarball name
# Location on MS where scripts are stored
SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
LOGS_TO_COPY = "{0}ms_logs_to_copy.txt".format(SCRIPTS_DIR)
CMDS_TO_RUN = "{0}ms_cmds_to_run.txt".format(SCRIPTS_DIR)
# Create directory on MS to store all collected logs in
MS_LITP_LOGS = "/root/litp_logs"
# Create directory for MS specific Logs
MS_LOG_DIR = "{0}/ms_logs".format(MS_LITP_LOGS)
# Peer node username and passwords
PEER_USER = "litp-admin"
PEER_PASSWORD = "p3erS3rv3r"
PEER_SU_PASSWORD = "@dm1nS3rv3r"

print "Creating directory to store MS logs: {0}".format(MS_LOG_DIR)
collect_logs_funcs.mkdir_parent(MS_LOG_DIR)

# In case /var/log/messages has been rotated, grab all MS messages files
MESSAGES_DIR = "{0}/messages".format(MS_LOG_DIR)
collect_logs_funcs.mkdir_parent(MESSAGES_DIR)
for message_file in glob.glob(r'{0}'.format("/var/log/messages*")):
    collect_logs_funcs.copy_file(message_file, MESSAGES_DIR)

# Run commands on the MS specified in the commands
#   file, piping the output to a specified file
print "Collecting output of running MS commands " \
      "specified in {0}...".format(CMDS_TO_RUN)
with open(CMDS_TO_RUN) as f:
    RUN_CMDS = f.readlines()

for line in RUN_CMDS:
    line = line.rstrip()
    # '|||' is to be used in files to separate commands
    #   and the files their output is to go into
    # Ex. "litp show_plan ||| litp_plan.txt" runs
    #   "litp show_plan" and pipes the output to litp_plan.txt
    cmd_to_run = line.split(" ||| ")[0]
    output_file = "{0}/{1}".format(MS_LOG_DIR, line.split(" ||| ")[1])

    cmd = "{0} > {1}".format(cmd_to_run, output_file)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).wait()

# Collect the logs specified in the MS log file
print "Collecting MS logs defined in {0}...".format(LOGS_TO_COPY)
with open(LOGS_TO_COPY) as f:
    COPY_LOGS = f.readlines()

for line in COPY_LOGS:
    line = line.rstrip()
    cp_from = line.split()[0]
    cp_to = "{0}/{1}".format(MS_LOG_DIR, line.split()[1])

    # If directory, copy all of its contents
    if cp_from[-1] == '/':
        collect_logs_funcs.copy_dir(cp_from, cp_to)
    elif cp_from[-1] == '*':
        # If file is defined using a wildcard
        for wild_file in glob.glob(r'{0}'.format(cp_from)):
            collect_logs_funcs.copy_file(wild_file, cp_to)
    else:
        # Otherwise, just copy the file
        collect_logs_funcs.copy_file(cp_from, cp_to)

''''# UPDATE PEER NODE PASSWORDS, IF REQUESTED
if len(sys.argv) == 3:
    # Run script to update passwords on all peer nodes if a third argument
    #   is passed to this script and the argument is "set_pass"
    if sys.argv[2] == "set_pass":
        print "UPDATING PEER NODE PASSWORDS..."
        collect_logs_funcs.copy_file("{0}/update_peer_password.py".format(
            SCRIPTS_DIR), "/opt/ericsson/enminst/lib/")
        CMD = "python /opt/ericsson/enminst/lib/update_peer_password.py"
        PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)

        # Poll process for new output until finished
        while True:
            NEXTLINE = PROCESS.stdout.readline()
            if NEXTLINE == '' and PROCESS.poll() is not None:
                break
            sys.stdout.write(NEXTLINE)
            sys.stdout.flush()
        OUTPUT = PROCESS.communicate()[0]
        EXITCODE = PROCESS.returncode

        if EXITCODE == 0:
            print OUTPUT
        else:
            print "ERROR UPDATING PEER NODE PASSWORDS."
            print OUTPUT
            sys.exit(0)
    else:
        print "ERROR UPDATING PEER NODE PASSWORDS.\n-- Please ensure that " \
              "the third argument passed to this script is 'set_pass'." \
              "\n   If you do not want to update the peer node passwords " \
              "then do not pass in a third argument."
        sys.exit(0)
else:
    print "NOT UPDATING PEER NODE PASSWORDS."'''

# Run script to collect logs from nodes
print "Collecting peer node logs..."
CMD = "python {0}collect_node_logs.py".format(SCRIPTS_DIR)
print CMD
PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)

# Save the output of running the node collection script
NODE_LOGS = "node_collection_logs.txt"
print "Logging node collection script output to {0}...".format(NODE_LOGS)
for line in iter(PROCESS.stdout.readline, ''):
    with open("{0}/{1}".format(MS_LITP_LOGS, NODE_LOGS), "a") as out_file:
        out_file.write(line)

# nodes.txt is created by collect_node_logs.py
# This file contains a list of the peer nodes on the system which is used
#   to identify all of the node logs that need to be SCPed to the MS
NODES_FILE = "{0}/nodes.txt".format(MS_LITP_LOGS)

# Check if nodes.txt exists
if os.path.isfile(NODES_FILE):
    # SCP logs from each peer node to MS
    with open(NODES_FILE) as f:
        NODES_LIST = f.readlines()

    for node in NODES_LIST:
        cmd = "scp -o StrictHostKeyChecking=no -r " \
              "{0}@{1}:/home/{0}/{1} {2}".format(
            PEER_USER, node.rstrip(), MS_LITP_LOGS)
        child = pexpect.spawn(cmd)
        child.expect(["password:", pexpect.EOF])
        child.sendline(PEER_PASSWORD)
        child.expect(pexpect.EOF)
else:
    print "{0} NOT FOUND. COULD NOT SCP PEER NODE LOGS TO MS.\n" \
          "-- Only the MS logs will be tarred...".format(NODES_FILE)

# Tar the created log directory
PARENT_DIR = MS_LITP_LOGS.split("/", 2)[0]
LITP_DIR = MS_LITP_LOGS.split("/")[2]
TAR_BALL = "/root/litp_logs_{0}.tar.gz".format(
    time.strftime("%d_%m_%Y_%H-%M"))
#    SCRIPTS_DIR, time.strftime("%d_%m_%Y_%H-%M"))
#CMD = "tar -C /root/ -czf {0} {1}".format(TAR_BALL, LITP_DIR)
CMD = "tar -czvf {0} {1}".format(TAR_BALL, LITP_DIR)
print "Tarring the logs to {0}".format(TAR_BALL)
print CMD
PROCESS = subprocess.Popen(
    CMD, stdout=subprocess.PIPE, shell=True).communicate()

print "Removing temporary directories created on each peer node..."
# Remove the created log directory on each node
CMD = "python {0}rm_peer_dirs.py".format(SCRIPTS_DIR)
subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True).communicate()

print "Log collection successfully completed."

