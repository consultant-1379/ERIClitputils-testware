'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     July 2015
@author:    Brian Kelly
@summary:   P-KGB Snapshot test cases to create and restore snapshots manually outside of LITP
'''

from litp_generic_test import GenericTest
from redhat_cmd_utils import RHCmdUtils
import os
import time

class SnapshotPKGB(GenericTest):

    """
    The following test cases are aimed at creating and restoring
    snapshots (VxVM and LVM) using non LITP commands. This is to allow for
    P-KGB testing. Using LITP commands to create and remove snapshots would
    be overwritten/removed by LITP test cases in the P-KGB, which leaves
    the need for these test cases to handle the snapshotting outside of LITP
    """

    def setUp(self):
        """Setup variables for every test"""
        super(SnapshotPKGB, self).setUp()
        self.ms_node = self.get_management_node_filename()
        print self.ms_node
        self.node_hostnames = self.get_model_names_and_urls()["nodes"]

    def test_create_snapshots(self):
        """
        Create VxVM and LVM snapshots
        """

        local_path = os.path.dirname(os.path.abspath(__file__)) + "/create_snapshots.sh"
        remote_path_sh = "/tmp/create_snapshots.sh"
        self.assertTrue(self.copy_file_to(self.ms_node, local_path, remote_path_sh, root_copy=False, add_to_cleanup=True))
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/create_snapshots.exp"
        remote_path_exp = "/tmp/create_snapshots.exp"
        self.assertTrue(self.copy_file_to(self.ms_node, local_path, remote_path_exp, root_copy=False, add_to_cleanup=True))
        stdout, stderr, retc = self.run_command(self.ms_node, "/bin/sh {0}".format(remote_path_sh), su_root=True)
        foundLine = False
        if "All litp_kgb snapshots have been created successfully" in stdout:
            foundLine = True
        self.assertEqual(retc, 0)
        self.assertEqual(stderr, [])
        self.assertTrue(foundLine)

        for hostn in self.node_hostnames:
            stdout, stderr, retc = self.run_command(self.ms_node, "/usr/bin/expect {0} {1}".format(remote_path_exp, hostn["name"]), su_root=True)
            foundLine = False
            if "All litp_kgb snapshots have been created successfully" in stdout:
                foundLine = True
            self.assertEqual(retc, 0)
            self.assertEqual(stderr, [])
            self.assertTrue(foundLine)

    def test_restore_snapshots(self):
        """
        Restore VxVM and LVM snapshots
        """

        nodeslist = self.get_managed_node_filenames()
        vxvm_disks = []
        for noden in nodeslist:
            stdout, stderr, retc = self.run_command(noden, "/usr/sbin/vxdg list | grep -vE 'NAME|STATE' | awk '{ print $1 }'", su_root=True)
            self.assertEqual(retc, 0)
            self.assertEqual(stderr, [])
            if stdout != []:
                for line in stdout:
                    if line not in vxvm_disks:
                        vxvm_disks.append(line)
        # STOP PUPPET ON MS AND NODES
        self.stop_service(self.ms_node, "puppet", assert_success=False, add_to_cleanup=False)
        for noden in nodeslist:
            self.stop_service(noden, "puppet", assert_success=False, add_to_cleanup=False)
        # STOP HTTPD ON MS AND NODES
        self.stop_service(self.ms_node, "httpd", assert_success=False, add_to_cleanup=False)
        # STOP VCS SERVICE ON NODES
        for noden in nodeslist:
            self.run_command(noden, "/opt/VRTSvcs/bin/haconf -dump -makero", su_root=True)
            self.run_command(noden, "/opt/VRTSvcs/bin/hastop -sys {0}".format(noden), su_root=True)
            trycount = 0
            while trycount < 60:
                trycount += 1
                _, _, retc = self.run_command(noden, "/opt/VRTSvcs/bin/hastatus -sum ", su_root=True)
                if retc != 0:
                    time.sleep(2)
                    break
                time.sleep(1)
                
        # NOW LOG ONTO PEER NODES AND RUN TO SEE WHAT DISKS ARE NOT VISABLE
        vxvm_disks_live = []
        for noden in nodeslist:
            stdout, stderr, retc = self.run_command(noden, "/usr/sbin/vxdg list | grep -vE 'NAME|STATE' | awk '{ print $1 }'", su_root=True)
            self.assertEqual(retc, 0)
            self.assertEqual(stderr, [])
            if stdout != []:
                for line in stdout:
                    if line not in vxvm_disks_live:
                        vxvm_disks_live.append(line)
        vxvm_disk_non_live = []
        vxvm_disk_non_live.extend(list(set(vxvm_disks) - set(vxvm_disks_live)))
        print vxvm_disk_non_live
        # FOR ANY THAT ARE MISSING LOG ONTO THE NODE AND RE-IMPORT THEM ON A NODE
        for disk in vxvm_disk_non_live:
            _, _, retc = self.run_command(nodeslist[0], "/opt/VRTS/bin/vxdg import {0}".format(disk), su_root=True)
            self.assertEqual(retc, 0)
        # NOW RUN THE EXPECTS SCRIPT AS NORMAL
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/merge_snapshots.sh"
        remote_path_sh = "/tmp/merge_snapshots.sh"
        self.assertTrue(self.copy_file_to(self.ms_node, local_path, remote_path_sh, root_copy=False, add_to_cleanup=True))
        local_path = os.path.dirname(os.path.abspath(__file__)) + "/merge_snapshots.exp"
        remote_path_exp = "/tmp/merge_snapshots.exp"
        self.assertTrue(self.copy_file_to(self.ms_node, local_path, remote_path_exp, root_copy=False, add_to_cleanup=True))
        for hostn in self.node_hostnames:
            stdout, stderr, retc = self.run_command(self.ms_node, "/usr/bin/expect {0} {1}".format(remote_path_exp, hostn["name"]), su_root=True)
            foundLine = False
            if "All litp_kgb snapshots have been merged successfully" in stdout:
                foundLine = True
            self.assertEqual(retc, 0)
            self.assertEqual(stderr, [])
            self.assertTrue(foundLine)
        stdout, stderr, retc = self.run_command(self.ms_node, "/bin/sh {0}".format(remote_path_sh), su_root=True)
        foundLine = False
        if "All litp_kgb snapshots have been merged successfully" in stdout:
            foundLine = True
        self.assertEqual(retc, 0)
        self.assertEqual(stderr, [])
        self.assertTrue(foundLine)
        _, _, retc = self.run_command(self.ms_node, "shutdown -r +1", su_root=True)
        self.assertEqual(retc, 0)
        self.disconnect_all_nodes()
        time.sleep(900)
        self.run_command(self.ms_node, "/sbin/lvscan", su_root=True)
        for noden in nodeslist:
            self.run_command(noden, "/sbin/lvscan", su_root=True)

