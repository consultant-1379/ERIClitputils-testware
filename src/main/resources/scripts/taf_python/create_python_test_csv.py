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
import subprocess


class getPythonTestTags():
    """
    Class to find and organise litp python test cases
    """

    def __init__(self, find_args):
        """ Initialise variables for class """

        self.find_args = find_args

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

        return stdout, stderr, exit_code

    def get_testcase_tags(self, testfile, testcase):
        """ Get Test tags for test case """

        cmd = 'grep -B6 "def {0}" {1}'.format(testcase, testfile)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0:
            return None

        start = False
        tags = ""
        for line1 in stdout:
            line = line1.replace("\"", "'")
            if '@attr' in line:
                start = True
            if 'def test' in line:
                break
            if start:
                tags += line.strip('/n')

        tags = tags.replace("@attr", "").replace("'", "").replace("(", "").replace(")", "").replace(" ", "")

        return tags.strip()

    def get_testcase_tms_id(self, testfile, testcase):
        """ Get TMS ID for test case """

        cmd = 'grep -B6 "def {0}" {1}'.format(testcase, testfile)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0:
            return None
        start = False
        tags = ""
        for line1 in stdout:
            line = line1.replace("\"", "'")
            if '@tmsid' in line:
                start = True
            if start and '@attr' in line or 'def test' in line:
                break
            if start:
                tags += line.strip('/n')

        tags = tags.replace("@tmsid", "").replace("'", "").replace("(", "").replace(")", "").replace(" ", "")

        return tags.strip()

    def get_testcase_parallel_id(self, testfile, testcase):
        """ Get Parallel Param for test case """

        return "False"

    def check_test_tag(self, test_case_tags):
        """ Check test tags against job actions """

        run_test = False
        ignore_test = False
        test_case_tags_list = test_case_tags.split(",")
        #for tc_tag in test_case_tags_list:
        given_tags = self.find_args["TEST_TAGS"].split(",")
        for giv_tag in given_tags:
            if giv_tag in test_case_tags_list:
                run_test = True
                break
        if not self.find_args["RUN_PRE_REG_ONLY"] and "pre-reg" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "PRE REG ONLY IS FALSE AND PRE REG IS PRESENT"
        if self.find_args["RUN_PRE_REG_ONLY"] and "pre-reg" not in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "PRE REG ONLY IS TRUE AND PRE REG IS NOT PRESENT"
        if self.find_args["RUN_REG_AND_PRE_REG"]:
            run_test = True
            ignore_test = False
            #print "PRE REG IS TRUE OR FALSE, BUT ALL ARE BEING INCLUDED ANYWAY"
        if self.find_args["INSTALL_TYPE"] != "physical" and "physical" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING PHYSICAL TEST"
        if self.find_args["INSTALL_TYPE"] != "cloud" and "cloud-only" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING CLOUD ONLY TEST"
        if not self.find_args["EXPANSION"] and "expansion" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING EXPANSION ONLY TEST"
        if not self.find_args["CDB_TESTS"] and "cdb-only" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING CDB ONLY TEST CASE"
        if not self.find_args["KGB_PHYSICAL"] and "kgb-physical" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING KGB PHYSICAL TEST CASE"
        if not self.find_args["KGB_OTHER"] and "kgb-other" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING KGB OTHER TEST CASE"
        if "manual-test" in test_case_tags_list:
            run_test = False
            ignore_test = True
            #print "REMOVING MANUAL TEST CASE"
        if run_test and ignore_test:
            print "THIS IS NOT POSSIBLE, ERROR ON TEST FINDER"
            sys.exit(1)
        if run_test and not ignore_test:
            return "RUN_TEST"
        if not run_test and ignore_test:
            return "IGNORE_TEST"
        if not run_test and not ignore_test:
            if self.find_args["REPORT_ONLY_RUN"]:
                return "IGNORE_TEST"
            else:
                return "SKIP_TEST"

        return "SKIP_TEST"

    def get_ordered_tc_list(self, unordered_test_case_list):
        
        ordered_test_case_list = []
        new_ordered_test_case_list = []
        ordered_list = []
        if self.find_args["RUN_MULTIPLE_MODULES"]:
            cmd = "find {0} | grep ordered_tcs.txt".format(self.find_args["TEST_LOCATION"])
            order_files, stderr, exit_code = self.run_command_local(cmd, logs=True)
            if ordered_files != []:
                for ord_file in ordered_files:
                    cmd = "cat {0}/ordered_tcs.txt".format(ord_file)
                    stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                    if stdout != []:
                        ordered_list.extend(stdout)
                    else:
                        print "No ordered tests found in ordered file: {0}".format(ord_file)
            else:
                print "No ordered task files found"
                return unordered_test_case_list
        else:
            if os.path.isfile("{0}/ordered_tcs.txt".format(self.find_args["TEST_LOCATION"])):
                print "{0}/ordered_tcs.txt has been found".format(self.find_args["TEST_LOCATION"])
                cmd = "cat {0}/ordered_tcs.txt".format(self.find_args["TEST_LOCATION"])
                stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                if stdout != []:
                    ordered_list.extend(stdout)
                else:
                    print "No ordered tests found in ordered file: {0}".format(self.find_args["TEST_LOCATION"])
                    return unordered_test_case_list
            else:
                print "No ordered task file found at: {0}/ordered_tcs.txt".format(self.find_args["TEST_LOCATION"])
                return unordered_test_case_list

        #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        #print ordered_list
        #print unordered_test_case_list
        #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"

        for order_test in ordered_list:
            order_test =  order_test.replace(":", ",")
            #print "====================="
            #print order_test
            #print "====================="
            found_in_list = False
            for unordered_test in unordered_test_case_list:
                #print unordered_test
                if order_test in unordered_test:
                    #print "------> ",unordered_test
                    ordered_test_case_list.append(unordered_test)
        for tcdec in unordered_test_case_list:
            if tcdec not in ordered_test_case_list:
                new_ordered_test_case_list.append(tcdec)
        new_ordered_test_case_list.extend(ordered_test_case_list)
        #print "--------------------------------"
        #for line in new_ordered_test_case_list:
        #    print line
        #print "--------------------------------"
        return new_ordered_test_case_list           

    def find_python_tests(self):
        """ find python tests in a given directory and organise tags """
    
        # FIND ALL TEST CASE FILE, NAMES, TAGS, PARALLEL AND TMS ID
        # FIND TEST CASES IN FILES
        cmd = 'grep -R "def test_" {0} | grep "testset" | grep ".py"'.format(self.find_args["TEST_LOCATION"])
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if stderr != [] or exit_code != 0:
            print "ERROR: stderr is {0} and exit code is {1}".format(stderr, exit_code)
            exit(1)
        unordered_test_case_list = []
        ordered_test_case_list = []
        for ret_list in stdout:
            item1 = ret_list.replace(":    def ", ":")
            full_details = item1.split("(")[0]
            testfile = full_details.split(":")[0]
            testcase = full_details.split(":")[1]
            full_details = full_details.replace(":", ",")
            test_case_tags = self.get_testcase_tags(testfile, testcase)
            test_case_action = self.check_test_tag(test_case_tags)
            full_details += ",{0}".format(test_case_action)
            test_tms_id = self.get_testcase_tms_id(testfile, testcase)
            full_details += ",{0}".format(test_tms_id)
            run_in_parallel = self.get_testcase_parallel_id(testfile, testcase)
            full_details += ",{0}".format(run_in_parallel)
            if test_case_action == "SKIP_TEST" or test_case_action == "RUN_TEST":
                #print full_details
                unordered_test_case_list.append(full_details)
        # PRESERVE ORDERING MECHANISM IF ANY
        ordered_test_case_list = self.get_ordered_tc_list(unordered_test_case_list)
        # PARALLEL v ORDERED

        for line in ordered_test_case_list:
            print line

        sys.exit(0)

def main():
    """
    main function
    """

    # Disable output buffering to receive the output instantly
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

    helper = "Not enough arguments supplied, format should be:" \
    + " python create_python_test_csv.py --test_case_dir=<path> --test_case_tags=<test tags to run> --install_type=<cloud|physical> OPTIONAL: " \
    + "--report_only_run --cdb_tests --kgb_only --kgb_other --run_pre_reg --run_reg_and_pre_reg --expansion --kgb_physical"
    if len(sys.argv) < 2:
        print helper
        sys.exit(1)

    find_args = {}
    find_args["INSTALL_TYPE"] = None
    find_args["TEST_TAGS"] = None
    find_args["TEST_LOCATION"] = None
    find_args["REPORT_ONLY_RUN"] = False
    find_args["RUN_PRE_REG_ONLY"] = False
    find_args["RUN_REG_AND_PRE_REG"] = False
    find_args["CDB_TESTS"] = False
    find_args["KGB_ONLY"] = False
    find_args["KGB_OTHER"] = False
    find_args["KGB_PHYSICAL"] = False
    find_args["EXPANSION"] = False
    find_args["RUN_MULTIPLE_MODULES"] = False

    for line in sys.argv:
        if "--install_type=" in line:
            find_args["INSTALL_TYPE"] = line.split("=")[-1]
        if "--test_case_tags=" in line:
            find_args["TEST_TAGS"] = line.split("=")[-1]
        if "--test_case_dir=" in line:
            find_args["TEST_LOCATION"] = line.split("=")[-1]
        if "--report_only_run" in line:
            find_args["REPORT_ONLY_RUN"] = True
        if "--run_pre_reg" in line:
            find_args["RUN_PRE_REG_ONLY"] = True
        if "--run_reg_and_pre_reg" in line:
            find_args["RUN_REG_AND_PRE_REG"] = True
        if "--cdb_tests" in line:
            find_args["CDB_TESTS"] = True
        if "--kgb_only" in line:
            find_args["KGB_ONLY"] = True
        if "--kgb_other" in line:
            find_args["KGB_OTHER"] = True
        if "--kgb_physical" in line:
            find_args["KGB_PHYSICAL"] = True
        if "--run_multiple_modules" in line:
            find_args["RUN_MULTIPLE_MODULES"] = True
        if "--expansion" in line:
            find_args["EXPANSION"] = True
    if find_args["INSTALL_TYPE"] is None or find_args["TEST_TAGS"] is None or find_args["TEST_LOCATION"] is None:
        print "ERROR Mandatory properties not given:"
        print helper
        sys.exit(1)

    getPythonTestTags(find_args).find_python_tests()

if  __name__ == '__main__': main()
