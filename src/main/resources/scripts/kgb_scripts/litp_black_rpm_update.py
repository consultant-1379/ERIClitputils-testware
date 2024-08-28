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
import re

class litpBlackRPMKGBUpdate():

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

    def test_litp_black_rpm_update(self):
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
        repo = "litp"
        upgrades = []
        downgrades = []
        dg_remote_path_sh = ""
        ##If ',' is present in RPM argument assume multiply RPMs to be updated at once.
        if "," in self.rpm_location:
            remote_rpms = list()
            #Loop through all rpms passed by splitting on ','
            #and copy each to MS
            for rpm_loc in self.rpm_location.split(','):
                local_path = rpm_loc
                remote_path = "/tmp/" + rpm_loc.split("/")[-1]
                print "Copy of {0} to {1} on MS Host" \
                    .format(local_path, remote_path)
                self.node.copy_file(local_path, remote_path)

                #Append each remote path to a list. This will be used later to
                #update all in a single yum command.
                remote_rpms.append(remote_path)

                stdout, stderr, _ = \
                    self.node.run_command("/usr/bin/litp import {0} {1}".
                                          format(remote_path, repo))

            #Join list of all remote paths by a space ready for passing to
            #yum argument
            package_data = self.separate_upgrades_and_downgrades(remote_rpms)

        #if only 1 RPM is present then just copy one RPM
        else:
            local_path = self.rpm_location
            #set to remote location of the single rpm
            remote_path_sh = "/tmp/" + self.rpm_location.split("/")[-1]
            print "Copy of {0} to {1} on MS Host" \
                .format(local_path, remote_path_sh)
            self.node.copy_file(local_path, remote_path_sh)
            stdout, stderr, _ = \
                self.node.run_command("/usr/bin/litp import {0} {1}".format(
                    remote_path_sh, repo))
            package_data = self.separate_upgrades_and_downgrades(
                [remote_path_sh])
        upgrades = package_data["update_packages"]
        downgrades = package_data["downgrade_names"]
        remote_path_sh = " ".join(upgrades)
        dg_remote_path_sh = " ".join(downgrades)

        #Run the upgrade command

        stdout = [] # Ensure graceful exit
        if dg_remote_path_sh:
            # The downgrade case
            stdout, stderr, _ = \
                self.node.run_command("/usr/bin/yum -y downgrade {0}".
                                      format(dg_remote_path_sh))

        if remote_path_sh:
            # The normal install case for black rpms where the candidate
            # version
            # is either newer than an existing matching package or there is no
            # previously installed version of that rpm
            stdout, stderr, _ = \
                self.node.run_command("/usr/bin/yum -y install {0}" \
                                      .format(remote_path_sh))

        if not (remote_path_sh or dg_remote_path_sh):
            print "No provided black rpm was an upgrade or a downgrade of an " \
                  "installed package. No changes to make, aborting job."
            sys.exit(1)

        linepres = False
        wait_update = False
        for line in stdout:
            if "does not update installed package" in line or "Complete!" in line:
                linepres = True
            if "does not update installed package" in line:
                wait_update = True
        print "linepres {0}".format(str(linepres))
        print "waitupdate {0}".format(str(wait_update))
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

    def separate_upgrades_and_downgrades(self, package_list):
        """
        Description:
            This method will separate a list of packages into two lists:
                One containing only packages with versions newer than those currently found in the yum list
                Another containing only packages which are not newer than items currently found on the yum list.
        """

        # 1. Map rpm file path to package name and version using regex
        pattern = r"^([^-]+?)-([^-]+).*\.rpm"
        regex = re.compile(pattern)
        packages_to_query = []
        version_mappings = {}
        for candidate_package_path in package_list:
            package_name = candidate_package_path.split("/")[-1]
            match = regex.search(package_name)
            packages_to_query.append(match.group(1))
            version_mappings[candidate_package_path] = {"name": match.group(1),
                                         "version": match.group(2)}

        # 2. List installed packages with their current installed versions
        yum_package_list = " ".join(packages_to_query)
        cmd = "yum list installed {0}".format(yum_package_list)
        yum_list, _, _ = self.node.run_command(cmd)
        start_point = 0
        if "Installed Packages" in yum_list:
            start_point = yum_list.index('Installed Packages') + 1

        update_list = []
        update_packages = []
        downgrade_list = []
        downgrade_packages = []
        replace_list = []
        replace_packages = []
        for candidate_package_path, candidate_package_data in version_mappings.iteritems():
            candidate_name = candidate_package_data["name"]
            candidate_version = candidate_package_data["version"]
            found = False
            for package_detail in yum_list[start_point:]:
                # Search for the candidate package in the yum installed package list
                split_package_detail = package_detail.split()
                installed_name = split_package_detail[0]
                installed_version = split_package_detail[1].split("-")[0]
                if candidate_name in installed_name:
                    # If a name match is found, compare versions and add to the
                    # appropriate list depending on the
                    # version comparison (upgrade, downgrade, versions equal)
                    found = True
                    package_install_status = self.is_version_newer(
                        installed_version,
                        candidate_version)
                    is_update = package_install_status > 0
                    is_downgrade = package_install_status < 0
                    versions_equal = package_install_status == 0
                    if is_update:
                        update_list.append(candidate_name)
                        update_packages.append(candidate_package_path)
                    if is_downgrade:
                        downgrade_list.append(candidate_name)
                        downgrade_packages.append(candidate_package_path)
                    if versions_equal:
                        replace_list.append(candidate_name)
                        replace_packages.append(candidate_package_path)
            if not found:
                # The candidate is a new package
                update_list.append(candidate_name)
                update_packages.append(candidate_package_path)
        return {"update_packages" : update_packages,
                "update_names" : update_list,
                "downgrade_packages" : downgrade_packages,
                "downgrade_names" : downgrade_list,
                "replace_packages" : replace_packages,
                "replace_names" : replace_list
                }

    def is_version_newer(self, existing_str, candidate_str):
        """
        Determine whether the candidate package is newer than the currently installed package
        :param existing_str: The version string of the currently installed package
        :param candidate_str: The version string of the candidate install
        :return: Positive if candidate is newer, negative if candidate is older
                0 if the two are equal
        """
        existing = existing_str.split(".")
        candidate = candidate_str.split(".")
        index=0
        comparison=0
        existing_version_section_count = len(existing)-1
        while comparison == 0 and index < len(candidate):
            if index > existing_version_section_count:
                # candidate version is longer and
                # previous matching sections were equal
                # candidate is newer
                return 1
            candidate_section = int(candidate[index])
            existing_section = int(existing[index])
            if candidate_section > existing_section:
                return 1
            if candidate_section < existing_section:
                return -1
            index += 1
        return 0

sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

if len(sys.argv) != 3:
    print "Not enough arguments given"
    print len(sys.argv)
    sys.exit(1)

rpm_update = litpBlackRPMKGBUpdate(sys.argv[1], sys.argv[2])
rpm_update.test_litp_black_rpm_update()
