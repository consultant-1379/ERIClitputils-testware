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

from common_methods import NodeConnect
import os
import sys
import time

class litpRPMKGBUpdate():

    """
    Class to log onto an MS and replace an RPM
    """

    def __init__(self, properties_file, rpm_location):
        """
        initialise variables for the job
        """
        self.properties_file = properties_file
        self.rpm_location = rpm_location
        self.node = NodeConnect()

    def get_connection_info(self):
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
                
    def test_litp_rpm_update(self):
        """
        Update a LITP RPM
        """

        ms_host, ms_ip, ms_pass, ms_user = self.get_connection_info()
        #print "DATA:"
        #print ms_host
        #print ms_ip
        #print ms_user
        #print ms_pass
        self.node = NodeConnect(ms_ip, ms_user, ms_pass)

        ##If ',' is present in RPM argument assume multiply RPMs to be updated at once.
        if "," in self.rpm_location:
            remote_rpms = list()
            #Loop through all rpms passed by splitting on ','
            #and copy each to MS
            for rpm_loc in self.rpm_location.split(','):
                local_path = rpm_loc
                remote_path = "/tmp/" + rpm_loc.split("/")[-1]
                print "Copy of {0} to {1} on MS Host"\
                    .format(local_path, remote_path)
                self.node.copy_file(local_path, remote_path)

                #Append each remote path to a list. This will be used later to
                #update all in a single yum command.
                remote_rpms.append(remote_path)

            #Join list of all remote paths by a space ready for passing to
            #yum argument
            remote_path_sh = " ".join(remote_rpms)

        #if only 1 RPM is present then just copy one RPM
        else:
            local_path = self.rpm_location
            #set to remote location of the single rpm
            remote_path_sh = "/tmp/" + self.rpm_location.split("/")[-1]
            print "Copy of {0} to {1} on MS Host"\
                .format(local_path, remote_path_sh)
            self.node.copy_file(local_path, remote_path_sh)

        self.node.run_command("/usr/bin/litp import {0} {1}"\
            .format(remote_path_sh, "/var/www/html/litp"))
        #Run the upgrade command
        stdout, stderr, _ = \
            self.node.run_command("/usr/bin/yum -y install {0}"\
                                      .format(remote_path_sh))
        linepres = False
        wait_update = False
        for line in stdout:
            if "does not update installed package" in line or "Complete!" in line:
                linepres = True
            if "does not update installed package" in line:
                wait_update = True
        if not linepres:
            sys.exit(1)
        _, _, retc = self.node.run_command("/usr/bin/litp update -p /litp/logging -o force_debug=true")
        if retc != 0:
            print "ERROR: LITP DEBUG NOT SUCCESSFUL"
            sys.exit(1)
        self.node.run_command("/bin/rm -rf {0}".format(remote_path_sh))

        if not wait_update:
            cmd = "/usr/bin/mco puppet status | grep 'Currently applying a catalog'"
            timeloop = 0
            while timeloop < 18:
                print "Running command: " + cmd + " Attempt {0} of 18".format(timeloop + 1)
                stdout, stderr, retc = self.node.run_command(cmd)
                if retc == 0:
                    timeloop += 1
                else:
                    break
                time.sleep(10)

            print "RPM Upgrade a success"

        sys.exit(0)

sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

if len(sys.argv) != 3:
    print "Not enough arguments given"
    print len(sys.argv)
    sys.exit(1)

rpm_update = litpRPMKGBUpdate(sys.argv[1], sys.argv[2])
rpm_update.test_litp_rpm_update()
