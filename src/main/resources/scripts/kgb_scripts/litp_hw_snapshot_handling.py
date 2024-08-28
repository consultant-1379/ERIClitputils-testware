'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     March 2016
@author:    Brian Kelly
@summary:   Create/Restore a snapshot manually in KGB environment
'''

from common_methods import NodeConnect
import os
import sys
import time

class litpSnapshotKGBHandling():

    """
    Class to log onto an MS and replace an RPM
    """

    def __init__(self, properties_file):
        """
        initialise variables for the job
        """
        self.properties_file = properties_file
        self.node = NodeConnect()

    def get_connection_info_ms(self):
        """
        get connection data details from given file
        """

        cmd = "/bin/cat {0}".format(self.properties_file)
        outp, _, rc = self.node.run_command_local(cmd, logs=False)
        if rc != 0:
            print "Error reading connection file, exiting..."
            sys.exit(1)
        ms_host = None
        for line in outp:
            if "type=MS" in line:
                ms_host = line.split(".")[1]
                break
        ms_ip = None
        ms_pass = None
        ms_user = "root"
        for line in outp:
            if "host.{0}.ip".format(ms_host) in line:
                ms_ip = line.split("=")[-1]
            if "host.{0}.user.root.pass".format(ms_host) in line:
                ms_pass = line.split("=")[-1]
        return ms_host, ms_ip, ms_pass, ms_user

    def get_connection_info_nodes(self):
        """
        get connection data details from given file
        """

        cmd = "/bin/cat {0}".format(self.properties_file)
        outp, _, rc = self.node.run_command_local(cmd, logs=False)
        if rc != 0:
            print "Error reading connection file, exiting..."
            sys.exit(1)
        node_hosts = []
        for line in outp:
            if "type=unknown" in line:
                node_hosts.append(line.split(".")[1])

        nodes_conn_dict = {}
        for hostn in node_hosts:
            nodes_conn_dict[hostn] = {}
            node_ip = None
            node_root_pass = None
            node_pass = None
            for line in outp:
                if "host.{0}.ip".format(hostn) in line:
                    node_ip = line.split("=")[-1]
                if "host.{0}.user.root.pass".format(hostn) in line:
                    node_root_pass = line.split("=")[-1]
                if "host.{0}.user.litp-admin.pass".format(hostn) in line:
                    node_pass = line.split("=")[-1]
            nodes_conn_dict[hostn]["ip"] = node_ip
            nodes_conn_dict[hostn]["root_user"] = node_root_pass
            nodes_conn_dict[hostn]["litp-admin_user"] = node_pass

        return nodes_conn_dict

    def snapshot_creation(self):
        """
        Create LITP snapshots outside of LITP
        """

        ms_host, ms_ip, ms_pass, ms_user = self.get_connection_info_ms()
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/create_snapshots.sh"
        remote_path_sh = "/tmp/create_snapshots.sh"
        print "Copy of {0} to {1} on MS Host".format(local_path, remote_path_sh)
        self.node.copy_file(local_path, remote_path_sh)
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/create_snapshots.exp"
        remote_path_exp = "/tmp/create_snapshots.exp"
        print "Copy of {0} to {1} on MS Host".format(local_path, remote_path_exp)
        self.node.copy_file(local_path, remote_path_exp)
        stdout, stderr, retc = self.node.run_command("/bin/sh {0}".format(remote_path_sh))
        foundLine = False
        if "All litp_kgb snapshots have been created successfully" in stdout:
            foundLine = True
        if retc != 0 or stderr != [] or not foundLine:
            print "ERROR: Snapshot not created successfully"
            sys.exit(1)
        nodes_conn_dict = self.get_connection_info_nodes()
        for hostnm in nodes_conn_dict:
            foundLine = False
            stdout, stderr, retc = self.node.run_command("/usr/bin/expect {0} {1}".format(remote_path_exp, hostnm))
            if "All litp_kgb snapshots have been created successfully" in stdout:
                foundLine = True
            if retc != 0 or stderr != [] or not foundLine:
                print "ERROR: Snapshot not created successfully"
                sys.exit(1)
            
        print "SNAPSHOTS CREATED SUCCESSFULLY"
        sys.exit(0)

    def snapshot_restore(self):
        """
        Restore LITP snapshots outside of LITP
        """
        ms_host, ms_ip, ms_pass, ms_user = self.get_connection_info_ms()
        nodes_conn_dict = self.get_connection_info_nodes()
        vxvm_disks = []
        for noden in nodes_conn_dict:
            self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
            stdout, stderr, retc = self.node.run_su_root_cmd("/usr/sbin/vxdg list | grep -vE 'NAME|STATE' | awk '{ print $1 }'")
            if retc != 0 or stderr != []:
                print "ERROR: Bad output from vxdg command"
                sys.exit(1)
            if stdout != []:
                for line in stdout:
                    if line not in vxvm_disks:
                        vxvm_disks.append(line)
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)
        stdout, stderr, retc = self.node.run_command("/sbin/service puppet stop")
        for noden in nodes_conn_dict:
            self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
            self.node.run_su_root_cmd("/sbin/service puppet stop")
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)
        stdout, stderr, retc = self.node.run_command("/sbin/service httpd stop")
        for noden in nodes_conn_dict:
            self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
            self.node.run_su_root_cmd("/opt/VRTSvcs/bin/haconf -dump -makero")
            self.node.run_su_root_cmd("/opt/VRTSvcs/bin/hastop -sys {0}".format(noden))
            trycount = 0
            while trycount < 60:
                trycount += 1
                _, _, retc = self.node.run_su_root_cmd("/opt/VRTSvcs/bin/hastatus -sum")
                if retc != 0:
                    time.sleep(2)
                    break
                time.sleep(1)

        # NOW LOG ONTO PEER NODES AND RUN TO SEE WHAT DISKS ARE NOT VISABLE       
        vxvm_disks_live = []
        for noden in nodes_conn_dict:
            self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
            stdout, stderr, retc = self.node.run_su_root_cmd("/usr/sbin/vxdg list | grep -vE 'NAME|STATE' | awk '{ print $1 }'")
            if retc != 0 or stderr != []:
                print "ERROR: Bad output from vxdg command"
                sys.exit(1)
            if stdout != []:
                for line in stdout:
                    if line not in vxvm_disks_live:
                        vxvm_disks_live.append(line)
        vxvm_disk_non_live = []
        vxvm_disk_non_live.extend(list(set(vxvm_disks) - set(vxvm_disks_live)))
        print vxvm_disk_non_live
        # FOR ANY THAT ARE MISSING LOG ONTO THE NODE AND RE-IMPORT THEM ON A NODE
        for disk in vxvm_disk_non_live:
            for noden in nodes_conn_dict:
                self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
                _, _, retc = self.node.run_su_root_cmd("/opt/VRTS/bin/vxdg import {0}".format(disk))
                if retc != 0:
                    print "ERROR: Could not re-import vxvm disk"
                    sys.exit(1)
                break
        # NOW RUN THE EXPECTS SCRIPT AS NORMAL
        ms_host, ms_ip, ms_pass, ms_user = self.get_connection_info_ms()
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/merge_snapshots.sh"
        remote_path_sh = "/tmp/merge_snapshots.sh"
        print "Copy of {0} to {1} on MS Host".format(local_path, remote_path_sh)
        self.node.copy_file(local_path, remote_path_sh)
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/merge_snapshots.exp"
        remote_path_exp = "/tmp/merge_snapshots.exp"
        print "Copy of {0} to {1} on MS Host".format(local_path, remote_path_exp)
        self.node.copy_file(local_path, remote_path_exp)
        for hostnm in nodes_conn_dict:
            foundLine = False
            stdout, stderr, retc = self.node.run_command("/usr/bin/expect {0} {1}".format(remote_path_exp, hostnm))
            if "All litp_kgb snapshots have been merged successfully" in stdout:
                foundLine = True
            if retc != 0 or stderr != [] or not foundLine:
                print "ERROR: Merge snapshot expect script not successful"
                sys.exit(1)
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)
        stdout, stderr, retc = self.node.run_command("/bin/sh {0}".format(remote_path_sh))
        foundLine = False
        if "All litp_kgb snapshots have been merged successfully" in stdout:
            foundLine = True
        if retc != 0 or stderr != [] or not foundLine:
            print "ERROR: Snapshot not created successfully"
            sys.exit(1)
        _, _, retc = self.node.run_command("shutdown -r +1")
        if retc != 0:
            print "ERROR: Reboot command failed"
        time.sleep(900)
        self.node.run_command("/sbin/lvscan")
        for noden in nodes_conn_dict:
            self.node = NodeConnect(nodes_conn_dict[noden]["ip"], "litp-admin", nodes_conn_dict[noden]["litp-admin_user"], rootpw=nodes_conn_dict[noden]["root_user"])
            self.node.run_su_root_cmd("/sbin/lvscan")
        print "SNAPSHOTS RESTORED SUCCESSFULLY"
        sys.exit(0)
        
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

if len(sys.argv) != 3:
    print "Not enough arguments given"
    print len(sys.argv)
    sys.exit(1)

snap_handle = litpSnapshotKGBHandling(sys.argv[1])
if sys.argv[2] == "create_snapshot":
    snap_handle.snapshot_creation()
if sys.argv[2] == "restore_snapshot":
    snap_handle.snapshot_restore()
