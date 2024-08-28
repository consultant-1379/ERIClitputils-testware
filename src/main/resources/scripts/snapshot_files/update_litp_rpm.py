'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     July 2015
@author:    Brian Kelly
@summary:  KGB RPM Update test cases to Update a given RPM in LITP
'''

from litp_generic_test import GenericTest
from redhat_cmd_utils import RHCmdUtils
import os
import time

class litpRPMKGBUpdate(GenericTest):

    """
    The following test cases are aimed at creating and restoring
    snapshots (VxVM and LVM) using non LITP commands. This is to allow for
    P-KGB testing. Using LITP commands to create and remove snapshots would
    be overwritten/removed by LITP test cases in the P-KGB, which leaves
    the need for these test cases to handle the snapshotting outside of LITP
    """

    def setUp(self):
        """Setup variables for every test"""
        super(litpRPMKGBUpdate, self).setUp()
        self.ms_node = self.get_management_node_filename()

    def test_litp_rpm_update(self):
        """
        Update a LITP RPM
        """

        # BASED ON LAST IN THE FOLDER BEING THE LATEST RPM TO INSTALL/UPGRADE
        stdout, stderr, retc = self.run_command_local("/bin/ls -lrt {0} | grep '.rpm' | grep CXP | tail -1".format(os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(retc, 0)
        self.assertEqual(stderr, [])
        self.assertNotEqual(stdout, [])
        rpm = stdout[0].split()[-1]

        local_path = os.path.dirname(os.path.abspath(__file__)) + "/" + rpm
        remote_path_sh = "/tmp/" + rpm
        print "Copy of {0} to {1} on MS Host".format(local_path, remote_path_sh)
        self.assertTrue(self.copy_file_to(self.ms_node, local_path, remote_path_sh, root_copy=True, add_to_cleanup=True))
        stdout, stderr, _ = self.run_command(self.ms_node, "/usr/bin/yum -y install {0}".format(remote_path_sh), su_root=True, su_timeout_secs=320)
        self.assertEqual(stderr, [])
        self.assertNotEqual(stdout, [])
        linepres = False
        wait_update = False
        if "Error: Nothing to do" in stdout or "Complete!" in stdout:
            linepres = True
        if "Error: Nothing to do" in stdout:
            wait_update = True
        self.assertTrue(linepres)
        _, _, retc = self.run_command(self.ms_node, "/usr/bin/litp update -p /litp/logging -o force_debug=true")
        self.assertEqual(retc, 0)
        
        if not wait_update:
            cmd = "/usr/bin/mco puppet status | grep 'Currently applying a catalog'"
            timeloop = 0
            while timeloop < 18:
                print "Running command: " + cmd + " Attempt {0} of 18".format(timeloop + 1)
                stdout, stderr, retc = self.run_command(self.ms_node, cmd)
                if retc == 0:
                    timeloop += 1
                else:
                    break
                time.sleep(10)

            print "RPM Upgrade a success"
