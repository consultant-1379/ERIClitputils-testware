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


class RunPythonTestCase():
    """
    Class to run a of test case through nosetests
    """

    def __init__(self, tc_args):
        """ Initialise variables for class """

        self.tc_args = tc_args

    def run_nosetests(self):
        """ Run nosetests on args supplied """

        if not os.path.isdir(self.tc_args["test_output_dir"]):
            os.mkdir(self.tc_args["test_output_dir"])
        tc_output_file = self.tc_args["test_output_dir"] + "/" \
                + self.tc_args["test_id"] + ".txt"
        if os.path.isdir(tc_output_file):
            print "Test log file already exists: {0}".format(tc_output_file)
            sys.exit(1)

        cmd = 'nosetests -s --testmatch={0} {1}'.format(self.tc_args["test_file"], self.tc_args["test_case"])
        get_logs = True
        final_result = None
        time_taken = None
        try:
            fopen = open(tc_output_file, "a+")
            if self.tc_args["test_action"] == "SKIP_TEST":
                fopen.write("SKIPPED TEST CASE, NO LOGS\n")
            else:
                for line in pexpect.spawn(cmd, timeout=20000):
                    if get_logs and "Ran 1 test in" not in line.strip():
                        fopen.write("{0}\n".format(line.strip("\n")))
                    if "Ran 1 test in" in line.strip():
                        line1 = line.strip().split()
                        time_taken = line1[-1]
                    if line.strip() == "OK":
                        # IF OK, TEST HAS PASSED, LOG RESULT TO LOG AND REPORT FILES
                        fopen.write("\nResult: PASS\n")
                        final_result = "PASS"
                    if "FAILED (errors=" in line.strip():
                        # IF OK, TEST HAS ERRORS, LOG RESULT TO LOG AND REPORT FILES
                        fopen.write("\nResult: ERROR\n")
                        final_result = "ERROR"
                    if "FAILED (failures=" in line.strip():
                        # IF OK, TEST HAS FAILED, LOG RESULT TO LOG AND REPORT FILES
                        fopen.write("\nResult: FAIL\n")
                        final_result = "FAIL"

            fopen.close()

        except Exception:
            print "ERROR: Print timeout value has been reached..."
            self.timeout_failure = True

        if final_result == "PASS":
            sys.exit(0)
        if final_result == "ERROR" or final_result == "FAIL":
            sys.exit(1)

        sys.exit(1)

def main():
    """
    main function
    """

    # Disable output buffering to receive the output instantly
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

    helper = "Not enough arguments supplied, format should be:" \
    + " python nosetests_runner.py --test-file=<test_file> --test-case=<test_case_name>" \
    + " --test-action=<run|skip> --test-id=<tms_id> --test-utils=<test utils dir> --connection-file=<connection data>" \
    + " --test-output-dir=<test result log file directory>"
    if len(sys.argv) != 8:
        print helper
        sys.exit(1)

    tc_args = dict()
    tc_args["test_file"] = None
    tc_args["test_case"] = None
    tc_args["test_action"] = None
    tc_args["test_id"] = None
    tc_args["test_utils"] = None
    tc_args["connection_file"] = None
    tc_args["test_output_dir"] = None
    for line in sys.argv:
        if "--test-file=" in line:
            tc_args["test_file"] = line.split("=")[-1]
        if "--test-case=" in line:
            tc_args["test_case"] = line.split("=")[-1]
        if "--test-action=" in line:
            tc_args["test_action"] = line.split("=")[-1]
        if "--test-id=" in line:
            tc_args["test_id"] = line.split("=")[-1]
        if "--test-utils=" in line:
            tc_args["test_utils"] = line.split("=")[-1]
        if "--connection-file=" in line:
            tc_args["connection_file"] = line.split("=")[-1]
        if "--test-output-dir=" in line:
            tc_args["test_output_dir"] = line.split("=")[-1]
    if tc_args["test_file"] is None or tc_args["test_case"] is None or tc_args["test_action"] is None or tc_args["test_id"] is None or tc_args["test_utils"] is None or tc_args["connection_file"] is None or tc_args["test_output_dir"] is None:
        print helper
        sys.exit(1)

    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + ":" + tc_args["test_utils"]
    else:
        os.environ["PYTHONPATH"] = tc_args["test_utils"]
    os.environ["LITP_CONN_DATA_FILE"] = tc_args["connection_file"]

    # CALL CLASS METHOD
    RunPythonTestCase(tc_args).run_nosetests()


if  __name__ == '__main__': main()
