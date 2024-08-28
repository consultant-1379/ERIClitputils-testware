"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     December 2016
@author:    Laura Forbes

Removes the temporary log directory created on each
node while running the log collection script.
"""

import os
import subprocess
from run_ssh_cmd_su import RunSUCommands


# Directory on MS where all collected logs are stored
MS_LITP_LOGS = "/root/litp_logs"
# LITP path to identify all clusters in the system
CLUSTER_PATH = "/deployments/d1/clusters/"
# Peer node username and passwords
PEER_USER = "litp-admin"
PEER_PASSWORD = "p3erS3rv3r"
PEER_SU_PASSWORD = "@dm1nS3rv3r"

# nodes.txt is created by collect_node_logs.py
# This file contains a list of the peer nodes on the system where
#   directories were created to temporarily store logs
NODES_FILE = "{0}/nodes.txt".format(MS_LITP_LOGS)

# Check if nodes.txt exists
if os.path.isfile(NODES_FILE):
    with open(NODES_FILE) as f:
        PEER_NODES = f.readlines()
else:
    # Find all nodes in cluster
    CMD = 'litp show -rp {0} | grep -B1 "type: node" ' \
      '| grep -v type | grep "/"'.format(CLUSTER_PATH)
    PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
    NODE_URLS = PROCESS.communicate()[0]
    PEER_NODES = []
    for node in NODE_URLS.splitlines():
        hostname = node.rsplit('/', 1)[1]
        PEER_NODES.append(hostname)
    print PEER_NODES

for node in PEER_NODES:
    # Remove created log directory on each node
    cmd = "rm -rf /home/{0}/{1}*".format(PEER_USER, node.rstrip())
    remove_dir = RunSUCommands(node.rstrip(), PEER_USER,
                               PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
    remove_dir.run_su_cmds()
