#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     October 2015
@author:    Brian Kelly
@summary:   Test runner in KGB
'''

import sys
import os
import pexpect
import subprocess


class CollectLITPLogs():
    """
    Class to run a of test case through nosetests
    """

    def __init__(self, tc_args):
        """ Initialise variables for class """

        self.tc_args = tc_args

    def run_command_local(self, cmd, logs=True):
        """
        Run commands against localhost
        """

        if logs:
            print "[local]# {0}".format(cmd)

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)

        result = child.communicate()
        exit_code = child.returncode
        stdout = result[0].splitlines()
        stderr = result[1].splitlines()

        if logs:
            print '\n'.join(stdout)
            print '\n'.join(stderr)
            print exit_code


    def collect_logs(self):
        """ Log onto LITP systems and collect system logs """

        print self.tc_args
        print "Action not completed yet"
        sys.exit(0)

    def update_allure_report(self):
        """ Update the allure report with link to litp test output logs """

        #if not os.path.isfile(self.tc_args["tc_detail_file"]):
        #    print "File does not exist: {0}".format(self.tc_args["tc_detail_file"])
        #    sys.exit(1)
        #fopen = open(self.find_args["CSV_FILE_LOCATION"], "r")
        #with open(self.tc_args["tc_detail_file"]) as filn:
        #    lines = filn.readlines()
        #full_tc_list = [line.rstrip('\n') for line in open(self.tc_args["tc_detail_file"])]
        full_allure_report = [line.rstrip('\n') for line in open(self.tc_args["allure_report_file"])]
        tc_id = self.tc_args["tc_detail_file"].split(":")[3]
        found = False
        for linen in full_allure_report:
            if "<name>{0}</name>".format(tc_id) in linen:
                found = True
            if found and "attachment title=" in linen:
                breakup = linen.replace("\"", "").split()
                for idn in breakup:
                    if "source=" in idn:
                        allure_file = idn.split("=")[-1]
                        self.run_command_local("sed -i 's/{0}/{2}{1}.txt/g' {2}".format(allure_file, tc_id, self.tc_args["allure_report_file"], "..\/..\/test-reports/"), logs=False)
                        break
                break

        sys.exit(0)

def main():
    """
    main function
    """

    # Disable output buffering to receive the output instantly
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

    helper = "Not enough arguments supplied, format should be:" \
        + " python post_test_actions.py collect-system-logs [--connection-file=<host.properties file> --log-output-dir=<directory to add log tarball>]" \
        + " update-allure-report [--allure-report-file=<location of allure report> --tc-detail-file=<list of litp test cases>]"
    if len(sys.argv) < 3:
        print helper
        sys.exit(1)
    tc_args = dict()
    if sys.argv[1] == "collect-system-logs":
        tc_args["connection_file"] = None
        tc_args["log_output_dir"] = None
        for line in sys.argv:
            if "--connection-file=" in line:
                tc_args["connection_file"] = line.split("=")[-1]
            if "--log-output-dir=" in line:
                tc_args["log_output_dir"] = line.split("=")[-1]
        if tc_args["connection_file"] is None or tc_args["log_output_dir"] is None:
            print helper
            sys.exit(1)
        CollectLITPLogs(tc_args).collect_logs()

    if sys.argv[1] == "update-allure-report":
        tc_args["allure_report_file"] = None
        tc_args["tc_detail_file"] = None
        for line in sys.argv:
            if "--allure-report-file=" in line:
                tc_args["allure_report_file"] = line.split("=")[-1]
            if "--tc-detail-file" in line:
                tc_args["tc_detail_file"] = line.split("=")[-1]
        if tc_args["allure_report_file"] is None or tc_args["tc_detail_file"] is None:
            print helper
            sys.exit(1)
        CollectLITPLogs(tc_args).update_allure_report()
    print helper
    sys.exit(1)

if  __name__ == '__main__': main()
