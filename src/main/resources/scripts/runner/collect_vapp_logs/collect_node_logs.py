"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes
"""

import os.path
import subprocess
from run_ssh_cmd_su import RunSUCommands


# Location on MS where scripts are stored
SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
LOGS_TO_COPY = "{0}/node_logs_to_copy.txt".format(SCRIPTS_DIR)
CMD_LOGS = "{0}/node_cmds_to_run.txt".format(SCRIPTS_DIR)
# Directory on MS to store all collected logs in
MS_LITP_LOGS = "/root/litp_logs"
# LITP path to identify all clusters in the system
CLUSTER_PATH = "/deployments/d1/clusters/"
# Peer node username and passwords
PEER_USER = "litp-admin"
PEER_PASSWORD = "p3erS3rv3r"
PEER_SU_PASSWORD = "@dm1nS3rv3r"

# Collect the logs specified in the peer node log file
with open(LOGS_TO_COPY) as f:
    COPY_LOGS = f.readlines()

# Run commands on each node specified in the commands
#   file, piping the output to a specified file
with open(CMD_LOGS) as f:
    RUN_CMDS = f.readlines()

# Find all nodes in cluster
print "IDENTIFYING ALL PEER NODES IN CLUSTER..."
CMD = 'litp show -rp {0} | grep -B1 "type: node" ' \
      '| grep -v type | grep "/"'.format(CLUSTER_PATH)
PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
PEER_NODES = PROCESS.communicate()[0]

for node in PEER_NODES.splitlines():
    # Get node hostname
    CMD = 'litp show -p {0} | grep "hostname:"'.format(node)
    PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
    hostname = PROCESS.communicate()[0].split()[1]

    # IS THIS FOR-LOOP NEEDED??? JUST DO IT FOR HOSTNAME???
    for host in hostname.splitlines():
        # Add node name to nodes.txt for MS to SCP logs over
        with open("{0}/nodes.txt".format(MS_LITP_LOGS), "a") as node_file:
            node_file.write("{0}\n".format(host))

        # Create directory on node to copy its logs to
        peer_dir = "/home/{0}/{1}".format(PEER_USER, host)
        print "CREATING {0} ON NODE {1} TO " \
              "TEMPORARILY STORE LOGS:".format(peer_dir, hostname)
        cmd = "mkdir {0}".format(peer_dir)

        node_dir = RunSUCommands(hostname, PEER_USER,
                                 PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
        node_dir.run_cmds()

        # Read file of logs to copy and copy them to directory created on node
        print "COPYING FILES TO TEMP DIRECTORY..."
        for line in COPY_LOGS:
            line = line.rstrip()
            cp_from = line.split()[0]
            cp_to = "{0}/{1}".format(peer_dir, line.split()[1])

            cmd = "cp {0} {1}".format(cp_from, cp_to)

            # If directory, copy all of its contents
            if cp_from[-1] == '/':
                cmd += " -r"

            copy_file = RunSUCommands(hostname, PEER_USER,
                                      PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
            copy_file.run_su_cmds()

        # Read file of commands to run, run them on the node and save each
        #   commands output to a file in the directory created on node
        for line in RUN_CMDS:
            line = line.rstrip()
            cmd_to_run = line.split(" ||| ")[0]
            output_file = "{0}/{1}".format(peer_dir, line.split(" ||| ")[1])

            cmd = "{0} > {1}".format(cmd_to_run, output_file)
            exec_cmd = RunSUCommands(hostname, PEER_USER,
                                     PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
            exec_cmd.run_su_cmds()

        # Change user permissions on all files in
        # created log directory so they can be SCPed
        cmd = "chmod -R 745 {0}/*".format(peer_dir)

        run_cmd = RunSUCommands(hostname, PEER_USER,
                                PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
        run_cmd.run_su_cmds()

