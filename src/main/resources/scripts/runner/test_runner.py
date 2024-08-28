#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     March 2014
@author:    Brian Kelly
@summary:   Test runner in KGB
'''

import sys
import os
import pexpect
import subprocess
import time
import datetime
import pprint
from run_sshcmds import NodeConnect
import urllib, urllib2, json


USAGE = "USAGE:\n\npython test_runner.py -rs --test-dir=xxx --results-dir=xxx --test-type=xxx --connection-file=xxx --utils-dir=xxx [OPTIONAL: --continue-on-fail --run-sanity --run-non-reg]\n\n" \
        + "OPTIONS:\n\n" \
        + "--test-dir=<Path to directory where all test cases exist> -> If test cases are in sub directories within this path they will also be picked up by the test runner\n" \
        + "--results-dir=<Path to a directory where test report can be kept> -> For example '--results-dir=/home/user/teststuff/results-dir/' - /home/user/teststuff/ must exist for results-dir to be created\n" \
        + "--test-type=<Test tags from test cases that will be run> - Test cases must have @attr as defined by the test framework rules for this to work\n" \
        + "--connection-file=<Path to host.properties file> - Described in the test framework rules\n" \
        + "--utils-dir=<Path to the litp test framework utilities>\n" \
        + "--continue-on-fail -> If this option is given, all test cases will be run regardless if there are failures. If option is not given then the test runner will stop on first failure\n" \
        + "--run-sanity -> If given, a sanity check will be run before and after every test case, ensuring test cases don't corrupt the test environment. If tests to not clean up, do not give this option\n" \
        + "--include-physical -> By default, test cases with the tag physical are ignored unless this tag is given\n" \
        + "--include-kgb-physical-only -> By default, test cases with the tag kgb-physical are ignored unless this tag is given\n" \
        + "--include-kgb-only -> Will run test cases with the tags kgb-other and kgb-other-setup\n" \
        + "--include-expansion -> Will run expansion test cases\n" \
        + "--include-bur-tests-only -> Will run backup and restore test cases\n" \
        + "--run-non-reg -> This option will only run new test cases and not show regression in the test report, if left out new test cases will not show up in the regression report. New test cases should be tagged as 'pre-reg'\n" \
        + "--create-allure-report -> Create an result xml file that can be used for allure test reporting - aimed at TAF\n" \
        + "--copy-vm-image=<path to vm image> -> Copies the vm image found in selected path to the MS\n\n" \
        + "The test runner run's based on test tags, with one of 'all' or 'pre-reg' must be included as a tag.\n" \
        + "Test case tags must conform to the standards described: https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/content/sites/litp2/ERIClitputils-testware/latest/fw_docs/processes/reviews.html#kgb-cdb-test-tags\n\n"

class RunTestCases():
    """
    Class to run a set of test cases
    """

    def __init__(self, test_runner_option, test_directory, results_dir, connection_file, is_snapshot, test_type='', continue_on_fail=False, run_sanity_check=False, run_regres=True, report_only_run=False, test_ai_option=False, include_physical=False, include_expansion=False, include_cdb=False, include_kgb_other=False, include_kgb_physical=False, include_module_report=False, allure_report=False, cdb_regression=False, include_prepare_restore_other=False, add_to_tms=False, exclude_db=False, ignore_sfs=False,ignore_va=False,verbose_logging=False):
        """
        initialise test runner properties
        """
        self.test_runner_option = test_runner_option
        self.test_directory = test_directory
        self.results_dir = results_dir
        self.res_report = []
        self.res_allure_report = []
        self.valid_options = ["-rs"]
        self.test_type = test_type
        self.connection_file = connection_file
        self.continue_on_fail = continue_on_fail
        self.run_sanity = run_sanity_check
        self.run_regres = run_regres
        self.include_physical = include_physical
        self.include_expansion = include_expansion
        self.include_cdb = include_cdb
        self.include_kgb_other = include_kgb_other
        self.include_prepare_restore_other = include_prepare_restore_other
        self.include_kgb_physical = include_kgb_physical
        self.test_ai_option = test_ai_option
        self.report_only_run = report_only_run
        self.include_module_report = include_module_report
        self.cdb_regression = cdb_regression
        self.tms = Tms()
        self.tms.add_to_tms = add_to_tms
        self.timeout_failure = False
        self.overall_start_time = None
        self.overall_finish_time = None
        self.allure_report = allure_report
        self.full_test_case_list = []
        self.email_url = "https://fem112-eiffel004.lmera.ericsson.se:8443/jenkins/job/Generate_Fail_Email/"
        self.fail_mail_count = 0
        # Max number of fail mails to send
        self.fail_mail_limit = 3
        # Enable to upload to TMS server
        # Temporarily disable upload
        if datetime.datetime.today().weekday() in [4]:
            print "TMS upload enabled - Thursday or Friday"
            self.tms.enable_tms_upload = True
        else:
            print "TMS upload disabled - Not Thursday or Friday"
            self.tms.enable_tms_upload = False
        self.exclude_db = exclude_db
        self.is_snapshot = is_snapshot
        self.ignore_va = ignore_va
        self.ignore_sfs = ignore_sfs
        self.log=self.VerboseLogger(verbose_logging)

    class VerboseLogger:
        def __init__(self,verbose):
            self.verbose = verbose

        def out(self,content):
            if self.verbose:
                print str(content)

    def output_to_json(self, passed, failed):
        """
        Output the test results to JSON file for passing further
        """
        # If the env variables exist we can put them into the file
        if (self.get_env("litp_iso_version") and self.get_env("JOB_NAME") and
            self.get_env("BUILD_TAG") and self.get_env("BUILD_URL")):
            iso_version = self.get_env("litp_iso_version")
            job_name = self.get_env("JOB_NAME")
            job_id = self.get_env("BUILD_TAG")
            build_url = self.get_env("BUILD_URL")
            # Checking whether it's a CDB job(for now)
            if ("VCDB" in job_name or "PCDB" in job_name or
                "ECDB" in job_name):
                job_suite = "CI CDB"
            else:
                job_suite = ""
            # Start time of tests execution(artifact name is hardcoded for now)
            job_time = time.ctime(self.overall_start_time)
            data = {
                "id": "{0}".format(job_id),
                "suite": "{0}".format(job_suite),
                "artifact_name": "LITP ISO",
                "artifact_version": "{0}".format(iso_version),
                "run_name": "{0}".format(job_name),
                "run_date": "{0}".format(job_time),
                "link": "{0}".format(build_url),
                "passing": "{0}".format(passed),
                "failing": "{0}".format(failed),
                "comment": " "
                }
            json_file = self.results_dir + "/" + "results.json"
            print "Creating the json file: {0}".format(json_file)
            with open(json_file, 'w') as outfile:
                json.dump(data, outfile)

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

    def run_test_suite(self):
        """
        Run a suite of test cases
        """
        # CHECK ENVIRONMENT IS OK FOR TESTING
        self.validate_environment()
        if self.run_sanity:
            self.sanity_setup()
        if not self.test_ai_option:
            # GET AND PRINT LITP VERSION
            self.get_litp_version()
        if self.is_snapshot:
            self.create_snapshot()
        if self.test_runner_option == "-rs":
            # RUN THE TESTS
            self.run_selected_test_cases()

    def run_selected_test_cases(self):
        """
        Run a selected list of test cases from a given file
        """

        # GET THE LIST OF TEST CASES TO BE RUN
        list_of_tcs = self.find_selected_test_cases()

        # RUN THE TESTS CASES AND RETURN THE RESULT
        run_result = self.run_test_cases(list_of_tcs)
        # IF PASSED THEN PASS THIS TO THE REPORT METHODS
        if run_result:
            res_run = True
            # CREATE LITP REPORT
            res_run = self.create_report(True)
            # IF ALLURE REPORT IS TO BE INCLUDED
            if self.allure_report:
                self.create_allure_report(True)
            if not res_run:
                exit(1)
        # IF FAILED THEN PASS THIS TO THE REPORT METHODS
        else:
            res_run = True
            # CREATE LITP REPORT
            res_run = self.create_report(False)
            # IF ALLURE REPORT IS TO BE INCLUDED
            if self.allure_report:
                self.create_allure_report(False)
            if not res_run:
                exit(1)

    def get_test_tags(self, testfile):
        """
        Gets all tags for a test, supports multiline tagging.

        testfile (str): The test file dict.

        Returns:
        str. A string of all the test tags.
        """
        cmd = 'grep -B5 "def {0}" {1}'.format(testfile[1], testfile[0])

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

        return tags.strip()

    def get_ordered_tc_list(self, unordered_test_case_list):
        """
        Given a test case list unordered, find ordered_tcs.txt file
        and if present order the tests based on the file
        """
        ordered_test_case_list = []
        new_ordered_test_case_list = []
        ordered_list = []
        # IF THERE ARE MULTIPLE DIRECTORIES WITH TEST CASES UNDERNEATH,
        # SEARCH AND ADD THEM TO THE ONE LIST TOGETHER
        if self.cdb_regression:
            cmd = "find {0} | grep ordered_tcs.txt".format(self.test_directory)
            order_files, stderr, exit_code = self.run_command_local(cmd, logs=True)
            if order_files != []:
                for ord_file in order_files:
                    cmd = "cat {0}".format(ord_file)
                    stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                    if stdout != []:
                        ordered_list.extend(stdout)
                    else:
                        print "No ordered tests found in ordered file: {0}".format(ord_file)
            else:
                print "No ordered task files found"
                return unordered_test_case_list
        # IF ONLY ONE DIRECTORY CONTAINING TEST CASES THEN SEARCH FOR ORDERED FILE
        else:
            if os.path.isfile("{0}/ordered_tcs.txt".format(self.test_directory)):
                print "{0}/ordered_tcs.txt has been found".format(self.test_directory)
                cmd = "cat {0}/ordered_tcs.txt".format(self.test_directory)
                stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                if stdout != []:
                    ordered_list.extend(stdout)
                else:
                    print "No ordered tests found in ordered file: {0}".format(self.test_directory)
                    return unordered_test_case_list
            else:
                print "No ordered task file found at: {0}/ordered_tcs.txt".format(self.test_directory)
                return unordered_test_case_list

        # BASED ON ORDERED LIST
        for order_test in ordered_list:
            found_in_list = False
            # LOOP UNORDERED LIST
            for unordered_test in unordered_test_case_list:
                # IF ORDERED TEST IS IN UNORDERED LIST *IF TEST IN FILE EXISTS*
                if order_test in unordered_test:
                    # ADD IT TO THE ORDERED TEST LIST IN CORRECT ORDER
                    ordered_test_case_list.append(unordered_test)
        # FOR UNORDERED TESTS
        for tcdec in unordered_test_case_list:
            # IF THEY ARE NOT IN ORDERED LIST
            if tcdec not in ordered_test_case_list:
                # ADD TO THE FINAL LIST
                new_ordered_test_case_list.append(tcdec)
        # APPEND THE ORDERED LIST TO THE UNORDERED LIST, SO THAT UNORDERED
        # TESTS ARE RUN FIRST THEN ORDERED TESTS ARE RUN LAST
        new_ordered_test_case_list.extend(ordered_test_case_list)
        return new_ordered_test_case_list

    def find_all_test_cases(self):
        """
        Find all test cases in the given directory
        """
        # GREP ALL FILES CALLED "testset*.py" FOR "def test_"
        cmd = 'grep -R "def test_" {0} | grep "testset" | grep ".py:"'.format(self.test_directory)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if stderr != [] or exit_code != 0:
            print "ERROR: stderr is {0} and exit code is {1}".format(stderr, exit_code)
            exit(1)
        if stdout == []:
            print "ERROR: stderr is {0}".format(stdout)
            exit(1)
        # THE RETURNED OUTPUT WILL BE PATH TO THE FILE AND THE TEST CASE
        test_case_list = []
        for ret_list in stdout:
            item1 = ret_list.replace(":    def ", ":")
            item = item1.split("(")[0]
            testfile = item.split(":")

            tags = self.get_test_tags(testfile)


            if tags:
                if "'pre-reg'" in tags and not self.run_regres:
                    test_case_list.append(item)

                if "'pre-reg'" not in tags and self.run_regres:
                    test_case_list.append(item)

        # If physical tests are not to be included, remove them
        if not self.include_physical:
            non_physical_list = []
            non_physical_list.extend(test_case_list)
            for ret_list in non_physical_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'physical'" in tags:
                        test_case_list.remove(item)


        if self.exclude_db:
            non_db_list = []
            non_db_list.extend(test_case_list)
            for ret_list in non_db_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'not_db_rdy'" in tags:
                        test_case_list.remove(item)

        # If expansion tests are not to be included, remove them
        if not self.include_expansion:
            non_expansion_list = []
            non_expansion_list.extend(test_case_list)
            for ret_list in non_expansion_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'expansion'" in tags:
                        test_case_list.remove(item)

        # If cdb only tests are not to be included, remove them
        if not self.include_cdb:
            non_cdb_list = []
            non_cdb_list.extend(test_case_list)
            for ret_list in non_cdb_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'cdb-only'" in tags:
                        test_case_list.remove(item)

        # If kgb other tests are not to be included, remove them
        if not self.include_kgb_physical:
            non_kgb_physical_list = []
            non_kgb_physical_list.extend(test_case_list)
            for ret_list in non_kgb_physical_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'kgb-physical'" in tags:
                        test_case_list.remove(item)

        if not self.include_kgb_other:
            non_kgb_list = []
            non_kgb_list.extend(test_case_list)
            for ret_list in non_kgb_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'kgb-other'" in tags:
                        test_case_list.remove(item)

        if not self.include_prepare_restore_other:
            non_bur_list = []
            non_bur_list.extend(test_case_list)
            for ret_list in non_bur_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if "'bur_only_test'" in tags:
                        test_case_list.remove(item)

        self.remove_if_has_tag(self.ignore_sfs, test_case_list, "'sfs-only'")
        self.remove_if_has_tag(self.ignore_va, test_case_list, "'va-only'")
        # If the test is a cloud only test, remove using tag and physical element

        cloud_only_list = []
        cloud_only_list.extend(test_case_list)
        for ret_list in cloud_only_list:
            item1 = ret_list.replace(":    def ", ":")
            item = item1.split("(")[0]
            testfile = item.split(":")

            tags = self.get_test_tags(testfile)

            if tags:
                if self.include_physical and "'cloud-only'" in tags:
                    test_case_list.remove(item)

        manual_tc_list = []
        manual_tc_list.extend(test_case_list)
        for ret_list in manual_tc_list:
            item1 = ret_list.replace(":    def ", ":")
            item = item1.split("(")[0]
            testfile = item.split(":")

            tags = self.get_test_tags(testfile)

            if tags:
                if "'manual-test'" in tags:
                    test_case_list.remove(item)



        ordered_final_list = []
        full_list = []
        if self.cdb_regression:
            cmd = "find {0} | grep ordered_tcs.txt".format(self.test_directory)
            order_files, stderr, exit_code = self.run_command_local(cmd, logs=True)
            if order_files != []:
                for filn in order_files:
                    ordered_final_list = []
                    filn1 = filn.replace("ordered_tcs.txt", "")
                    temp_full_list = []
                    neworderlist = []
                    newtclist = []
                    newtclist.extend(test_case_list)
                    for tcname in newtclist:
                        if filn1 in tcname:
                            test_case_list.remove(tcname)
                            temp_full_list.append(tcname)
                    cmd = "cat {0}".format(filn)
                    stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                    if exit_code != 0 or stderr != [] or stdout == []:
                        print "----------------------------------------------"
                        print stdout
                        print stderr
                        print exit_code
                        print "ERROR: Cannot get environment information "
                        print "----------------------------------------------"
                        exit(1)
                    for line in stdout:
                        for line1 in temp_full_list:
                            if line in line1:
                                temp_full_list.remove(line1)
                                ordered_final_list.append(line1)
                    test_case_list.extend(temp_full_list)
                    for line in stdout:
                        for line1 in ordered_final_list:
                            if line in line1:
                                test_case_list.append(line1)

            full_list.extend(test_case_list)

        else:
            if os.path.isfile("{0}/ordered_tcs.txt".format(self.test_directory)):
                print "{0}/ordered_tcs.txt has been found".format(self.test_directory)
                cmd = "cat {0}/ordered_tcs.txt".format(self.test_directory)
                stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                if exit_code != 0 or stderr != [] or stdout == []:
                    print "----------------------------------------------"
                    print stdout
                    print stderr
                    print exit_code
                    print "ERROR: Cannot get environment information "
                    print "----------------------------------------------"
                    exit(1)
                for line in stdout:
                    for line1 in test_case_list:
                        if line in line1:
                            test_case_list.remove(line1)
                            ordered_final_list.append(line1)
                full_list.extend(test_case_list)
                for line in stdout:
                    for line1 in ordered_final_list:
                        if line in line1:
                            full_list.append(line1)
            else:
                print "No ordered task file found"
                full_list.extend(test_case_list)

        self.full_test_case_list.extend(full_list)

        return full_list

    def remove_if_has_tag(self, excluding, test_list, token):
        if excluding:
            exclude_list = []
            exclude_list.extend(test_list)
            for ret_list in exclude_list:
                item1 = ret_list.replace(":    def ", ":")
                item = item1.split("(")[0]
                testfile = item.split(":")

                tags = self.get_test_tags(testfile)

                if tags:
                    if token in tags:
                        self.log.out("Excluding {0} because it has the {1} tag".format(str(item),token))
                        test_list.remove(item)

    def find_selected_test_cases(self):
        """
        Find a list of selected test cases passed to the test runner
        from a file
        """
        # EXTRACT THE TEST TAGS
        self.test_type = self.test_type.replace("--test-type=", "")
        test_types = self.test_type.split(",")
        print "Searching for testcases with the following tags:"
        for line in test_types:
            print "- {0}".format(line)
        # CREATE THE NOSETESTS COMMAND THAT WILL CHECK IF TEST BEING RUN HAS
        # THE TEST TAG EXISTS
        nosecheck = "nosetests -s --collect-only"
        for nosen in test_types:
            nosecheck = nosecheck + " -a '{0}'".format(nosen)
        # FIND ALL TEST CASES IN THE REGRESSION SUITE AND RETURN IN A LIST
        full_list = self.find_all_test_cases()

        # BASED ON THE RETURNED TEST CASES, CHECK EACH ONE, IF TEST RUNS
        # CORRECTLY THEN ADD IT TO LIST OF TEST CASES WHICH WILL BE RUN
        final_list = []
        debug_failure = []
        for testname in full_list:
            testfile = testname.split(":")
            cmd = "{0} --testmatch={1} {2}".format(nosecheck, testfile[1], testfile[0])
            for line in pexpect.spawn(cmd, timeout=2000):
                debug_failure.append(line)
                if "Ran 1 test in" in line:
                    final_list.append(testname)
        if final_list == []:
            print "ERROR: Cannot find any test cases with tags given"
            exit(1)
        else:
            print "Test cases found..."

        return final_list

    def run_test_cases(self, list_of_tcs):
        """
        Run a list of test cases
        """
        # CREATE PYTHON DIRECTORY
        self.create_results_dir(self.results_dir)
        # CREATE NOSETESTS DIRECTORY
        nose_res_dir = self.results_dir + "/" + "nose_results/"
        self.create_results_dir(nose_res_dir)
        test_col_width = 80
        file_col_width = 25
        self.overall_start_time = int(round(time.time() * 1000))
        time_test_start = 0
        time_test_stop = 0

        # FOR EACH TEST CASE BEING RUN
        for testcase in self.full_test_case_list:
            # Make a test case folder for results
            splitname = testcase.split(":")
            full_test_path = splitname[0]
            testcase_name = splitname[1]
            testfilename = full_test_path.split("/")[-1]
            moduledirname = full_test_path.split("/")[-2]
            res_dir = "{0}/{1}-{2}".format(self.results_dir, testfilename, testcase_name)
            os.mkdir(res_dir)

            # GET DOCUMENTATION FROM TEST CASE
            cmd = "/bin/cat {0}".format(full_test_path)
            stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
            if stderr != [] or exit_code != 0:
                print "ERROR: stderr is {0} and exit code is {1}".format(stderr, exit_code)
                exit(1)
            if stdout == []:
                print "ERROR: stderr is {0}".format(stdout)
                exit(1)
            # PARSE THE OUTPUT FOR TEST REPORT
            # THIS SHOULD BE REPLACED WHEN ALL TEST CASES ARE USING THE
            # TMS, UNTIL THEN THIS MUST REMAIN IN PLACE
            document = []
            testcopy = False
            startcopy = False
            desccopy = False
            testdoc = []
            for line in stdout:
                if testcopy and startcopy:
                    if "\"\"\"" in line or "'''" in line:
                        startcopy = False
                        testcopy = False
                        desccopy = False
                if startcopy:
                    if ":" in line and "Action" in line or "Pre-Requisites" in line \
                            or "Risks" in line or "Pre-Test Steps" in line \
                            or "Test Steps" in line or "Restore Steps" in line \
                                or "Expected Result" in line or "Steps" in line \
                                or "Pre-requisite" in line:
                        desccopy = False
                    if "\"\"\"" not in line or "'''" not in line:
                        document.append(line)
                        if desccopy:
                            addline = line.replace("Description:", "")
                            testdoc.append(addline + "<br>")
                if testcopy:
                    if "\"\"\"" in line or "'''" in line:
                        startcopy = True
                        desccopy = True
                if "def {0}(self):".format(testcase_name) in line:
                    testcopy = True

            document_str = '\n'.join(document)
            document_desc = '\n'.join(testdoc)

            tms_doc = self.tms.parse_tms(stdout, testcase_name)

            if "tms_id" in tms_doc and "tms_requirements_id" in tms_doc and "tms_title" in tms_doc \
                    and "tms_description" in tms_doc and "tms_test_steps" in tms_doc \
                    and "tms_test_precondition" in tms_doc and "tms_execution_type" in tms_doc and self.run_regres:

                self.tms.upload_to_tms(tms_doc)

                # OVERWRITE ORIGINAL DOC STRINGS
                write_data_desc = []
                write_data_desc_only = []
                write_data_desc_only.append("{0}".format(tms_doc["tms_description"]))
                write_data_desc.append("Title: {0}".format(tms_doc["tms_title"]))
                write_data_desc.append("")
                write_data_desc.append("Description: {0}".format(tms_doc["tms_description"]))
                write_data_desc.append("")
                write_data_desc.append("Requirements: {0}".format(tms_doc["tms_requirements_id"]))
                write_data_desc.append("")
                write_data_desc.append("Pre-conditions: {0}".format(tms_doc["tms_test_precondition"]))
                write_data_desc.append("")
                write_data_desc.append("Steps:")
                for line in tms_doc["tms_test_steps"]:
                    write_data_desc.append("")
                    write_data_desc.append("  Step -> {0}".format(line[0]))
                    for resp in line[1]:
                        write_data_desc.append("    Result -> {0}".format(resp))
                document_str = '\n'.join(write_data_desc)
                document_desc = '\n'.join(write_data_desc_only)

            # Create test output file for test logs
            result_file = res_dir + "/" + "test_output.txt"
            test_failure_file = self.results_dir + "/" + "test_failure_file.txt"
            result_file_report = "{0}-{1}".format(testfilename, testcase_name) + "/" + "test_output.txt"
            doc_file = res_dir + "/" + "test_doc.txt"
            doc_file_report = "{0}-{1}".format(testfilename, testcase_name) + "/" + "test_doc.txt"
            sopen = open(doc_file, "w")
            sopen.write(document_str)
            sopen.close()
            if self.run_sanity and testcase in list_of_tcs:
                self.pre_test_sanity()
            try:
                fopen = open(result_file, "a+")
                swrite = True
                time_taken = None
                final_result = None
                if testcase in list_of_tcs:
                    # Run the test case using nosetests, printing outout to the file when data is available
                    time_test_start = int(round(time.time() * 1000))
                    cmd = 'nosetests --with-xunit --xunit-file={0}/{3}-{1}-nosetests.xml -s --testmatch={1} {2}'.format(nose_res_dir, testcase_name, full_test_path, testfilename)
                    for line in pexpect.spawn(cmd, timeout=20000):
                        if swrite and "Ran 1 test in" not in line.strip():
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

                    time_test_stop = int(round(time.time() * 1000))
                    print_res = "{0} {1}".format(testfilename, testcase_name)
                    leng = len(print_res)
                    lesso = 100 - leng

                    n = 0
                    while n < lesso:
                        n += 1
                        print_res += " "
                    if final_result == "ERROR":
                        print "{0} ... ERROR   ... {1}".format(print_res, time_taken)
                    else:
                        print "{0} ... {1}    ... {2}".format(print_res, final_result, time_taken)

                else:
                    time_test_start = 0000000000000
                    time_test_stop = 0000000000000
                    if not self.report_only_run:
                        cmd = 'nosetests --with-xunit --xunit-file={0}/{3}-{1}-nosetests.xml -s --testmatch={1} --exclude={1} {2}'.format(nose_res_dir, testcase_name, full_test_path, testfilename)
                    else:
                        cmd = 'nosetests -s --testmatch={1} --exclude={1} {2}'.format(nose_res_dir, testcase_name, full_test_path, testfilename)
                    for line in pexpect.spawn(cmd, timeout=20000):
                        if "Ran 0 tests in" in line.strip():
                            line1 = line.strip().split()
                            time_taken = "0.000s"
                            final_result = "SKIPPED"


                    print_res = "{0} {1}".format(testfilename, testcase_name)
                    leng = len(print_res)
                    lesso = 100 - leng

                    n = 0
                    while n < lesso:
                        n += 1
                        print_res += " "
                    if not self.report_only_run:
                        print "{0} ... SKIPPED ... {1}".format(print_res, time_taken)
                        cmd = 'sed -i s/skip=\\"0\\"/skip=\\"1\\"/g {0}/{1}-{2}-nosetests.xml'.format(nose_res_dir, testfilename, testcase_name)
                        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                        if stdout != []  or stderr != [] or exit_code != 0:
                            print "ERROR: Running sed command failed"
                            exit(1)
                fopen.close()
            except Exception:
                print "ERROR: Print timeout value has been reached..."
                self.timeout_failure = True


            # Add results of test to dictionary for html report
            if self.report_only_run and final_result == "SKIPPED":
                pass
            else:
                if self.include_module_report:
                    self.res_report.append(["{0}.{1}".format(testfilename, testcase_name), document_desc, doc_file_report, final_result, time_taken, result_file_report, moduledirname])
                    self.res_allure_report.append([testfilename, testcase_name, result_file_report, final_result, time_test_start, time_test_stop, tms_doc, doc_file_report, moduledirname])
                else:
                    self.res_report.append(["{0}.{1}".format(testfilename, testcase_name), document_desc, doc_file_report, final_result, time_taken, result_file_report])
                    self.res_allure_report.append([testfilename, testcase_name, result_file_report, final_result, time_test_start, time_test_stop, tms_doc, doc_file_report])

            if final_result == "PASS" or final_result == "SKIPPED":
                pass
            else:
                ropen = open(test_failure_file, "a+")
                ropen.write("{0} {1} {2}\n".format(testfilename, testcase_name, final_result))
                ropen.close()
                if self.fail_mail_count < self.fail_mail_limit:
                    test_email_id = "{0}.{1}".format(testfilename,
                                                     testcase_name)
                    self.trigger_fail_email(test_email_id)

                if not self.continue_on_fail or self.timeout_failure:
                    break

            if self.run_sanity and testcase in list_of_tcs:
                if not self.post_test_sanity():
                    self.overall_finish_time = time.time()
                    return False

        self.overall_finish_time = int(round(time.time() * 1000))

        return True


    def post_url(self, url, list_type=False):
        """
        Poll the console url and return data.
        """
        cmd = "curl -X POST {0}".format(url)

        stdout, _, _ = \
            self.run_command_local(cmd, logs=False)

        if list_type:
            return stdout

        return "\n".join(stdout)

    def get_env(self, key, default=None):
        """
        Pick up environ variable or return None if not set
        """
        variable = os.getenv(key, default)
        return variable

    def trigger_fail_email(self, test_id):
        """
        Gathers information on job and then triggers jenkins job which will
        send a fail email.
        """
        build_url = self.get_env('BUILD_URL')
        build_tag = self.get_env('BUILD_TAG')
        email_list = None
        build_name = None

        if build_tag:
            if '-' in build_tag:
                build_name = build_tag.split('-')[1]
                if '_' in build_name:
                    email_env = "{0}_testware_Guard"\
                        .format(build_name.split('_')[0])
                    email_list = self.get_env(email_env)
                # Replace new line and commasa with hash
                    if email_list:
                        email_list = \
                            email_list.replace(' ', "#").replace(',', '#')

        # If variables set shows we are running in jenkins
        if build_url and build_name and email_list:
            parameter_part = \
                "\&email_list={0}\&source_job={1}\&source_link={2}\&test_name={3}"\
                .format(email_list,
                        build_name,
                        build_url,
                        test_id)
            token_url = "{0}/buildWithParameters?token=DUCKS1234"\
                .format(self.email_url)

            full_url = "{0}{1}".format(token_url,
                                       parameter_part)
            self.post_url(full_url)
            self.fail_mail_count += 1

    def create_results_dir(self, dir_make):
        """
        Create a results directory
        """
        os.mkdir(dir_make)

    def replace_xml_chars(self, text):
        """
        Replace any xml characters with the escaped xml replresentation:
        '&' = '&amp;', '<' = '&lt;', '>' = '&gt;'

        Args:
            text (str): String of text to be formatted.

        Returns:
            str: Reformatted string.

        """
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def create_allure_report(self, tr_result):
        """
        Create an xml result file which can be used for allure test reporting
        Allure is not supported in python 2.6, until then the xml needs to be generated manually.
        The report generation below is taken from a standard allure report, but also including TMS properties
        if given
        """
        print "Creating allure report..."
        allure_report_dir = "{0}/allure_reporting/".format(self.results_dir)
        os.mkdir(allure_report_dir)
        allure_report_file = allure_report_dir + "allure_report-testsuite.xml"
        fopen = open(allure_report_file, "a+")
        fopen.write('<ns2:test-suite xmlns:ns2="urn:model.allure.qatools.yandex.ru" start="{0}" stop="{1}">\n'.format(self.overall_start_time, self.overall_finish_time))
        if "JOB_NAME" in os.environ:
            fopen.write('  <name>{0}</name>\n'.format(os.environ["JOB_NAME"]))
        else:
            fopen.write('  <name>JOB NAME</name>\n')
        fopen.write('  <test-cases>\n')
        for line in self.res_allure_report:
            tms_doc = line[6]
            testfilename = line[0].replace(".py", "").replace("testset_", "")
            # COPY REPORT FILE
            testcase_doc_file = "{0}_{1}_documentation-attachment.txt".format(testfilename, line[1])
            testcase_doc_file_full = allure_report_dir + "/" + testcase_doc_file
            testcase_report_file_full = allure_report_dir + "{0}_{1}-attachment.txt".format(testfilename, line[1])
            testcase_report_file = "{0}_{1}-attachment.txt".format(testfilename, line[1])
            self.run_command_local("cp {0} {1}".format(self.results_dir + "/" + line[2], testcase_report_file_full), logs=False)
            self.run_command_local("cp {0} {1}".format(self.results_dir + "/" + line[7], testcase_doc_file_full), logs=False)
            if line[3] == "PASS":
                fopen.write('    <test-case start="{0}" status="passed" stop="{1}">\n'.format(line[4], line[5]))
            if line[3] == "FAIL":
                fopen.write('    <test-case start="{0}" status="failed" stop="{1}">\n'.format(line[4], line[5]))
            if line[3] == "ERROR":
                fopen.write('    <test-case start="{0}" status="broken" stop="{1}">\n'.format(line[4], line[5]))
            if line[3] == "SKIPPED":
                fopen.write('    <test-case start="{0}" status="skipped" stop="{1}">\n'.format(line[4], line[5]))
            if "add_to_allure" in tms_doc:
                fopen.write('     <name>{0} - {1} - {2}</name>\n'.format(testfilename, line[1], self.replace_xml_chars(tms_doc["tms_id"])))
                fopen.write('     <title>{0}</title>\n'.format(self.replace_xml_chars(tms_doc["tms_title"])))
                fopen.write('     <description>{0}</description>\n'.format(self.replace_xml_chars(tms_doc["tms_description"])))
            else:
                fopen.write('     <name>{0} - {1}</name>\n'.format(testfilename, line[1]))
            fopen.write('     <attachments>\n')
            fopen.write('       <attachment source="{0}" title="test_log.txt" type="text/plain"/>\n'.format(testcase_report_file))
            fopen.write('       <attachment source="{0}" title="test_doc.txt" type="text/plain"/>\n'.format(testcase_doc_file))
            fopen.write('     </attachments>\n')
            fopen.write('     <labels>\n')
            if self.include_module_report:
                fopen.write('       <label name="feature" value="{0}"/>\n'.format(line[8]))
            else:
                if "JOB_NAME" in os.environ:
                    fopen.write('       <label name="feature" value="{0}"/>\n'.format(os.environ["JOB_NAME"]))
                else:
                    fopen.write('       <label name="feature" value="LITP"/>\n')
            if "add_to_allure" in tms_doc:
                if 'tms_story_title' in tms_doc.keys():
                    for stor in tms_doc["tms_story_title"]:
                        fopen.write('       <label name="story" value="{0}"/>\n'.format(stor))
                    fopen.write('       <label name="execution_type" value="{0}"/>\n'.format(tms_doc["tms_execution_type"]))
                    fopen.write('       <label name="testId" value="{0}"/>\n'.format(tms_doc["tms_id"]))
                    fopen.write('       <label name="severity" value="{0}"/>\n'.format(tms_doc["tms_priority"]["tms_priority_title"].lower()))
            fopen.write('     </labels>\n')
            fopen.write('     <steps/>\n')
            fopen.write('    </test-case>\n')
        fopen.write('  </test-cases>\n')
        fopen.write('  <labels/>\n')
        fopen.write('</ns2:test-suite>\n')
        fopen.close()

    def create_report(self, tr_result):
        """
        Create a html test report of all test cases and results
        """

        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        module_res_dict = dict()
        for line in self.res_report:
            if self.include_module_report:
                if line[6] not in module_res_dict:
                    module_res_dict[line[6]] = [0, 0, 0, 0, 0, 0, 0]
            if "PASS" in line:
                passed += 1
                if self.include_module_report:
                    module_res_dict[line[6]][2] += 1
            if "FAIL" in line:
                failed += 1
                if self.include_module_report:
                    module_res_dict[line[6]][3] += 1
            if "ERROR" in line:
                errors += 1
                if self.include_module_report:
                    module_res_dict[line[6]][4] += 1
            if "SKIPPED" in line:
                skipped += 1
                if self.include_module_report:
                    module_res_dict[line[6]][5] += 1

        total = passed + failed + errors
        total_skip = passed + failed + errors + skipped
        if failed == 0 and errors == 0:
            passrate = 100.00
        else:
            passrate = float(passed) / float(total)
        # Create json with test name, test type, passed, failed, %
        self.output_to_json(passed, failed)

        if self.include_module_report:
            for line in module_res_dict:
                module_res_dict[line][0] = module_res_dict[line][2] + module_res_dict[line][3] + module_res_dict[line][4] + module_res_dict[line][5]
                module_res_dict[line][1] = module_res_dict[line][2] + module_res_dict[line][3] + module_res_dict[line][4]
                if module_res_dict[line][3] == 0 and  module_res_dict[line][4] == 0:
                    module_res_dict[line][6] = 100.00
                else:
                    module_res_dict[line][6] = float(module_res_dict[line][2]) / float(module_res_dict[line][1])

        print "{0} out of {1} test cases were run".format(total, total_skip)
        print "{0} test cases passed".format(passed)
        print "{0} test cases failed".format(failed)
        print "{0} test cases had errors".format(errors)
        print "{0} test cases were skipped".format(skipped)

        print "\nTMS upload report:"
        for entry in self.tms.logger:
            print entry

        report_file = self.results_dir + "/" + "test_report.html"
        fopen = open(report_file, "a+")

        fopen.write("<!DOCTYPE html>\n")
        fopen.write('<style type="text/css">\n')
        fopen.write(".myTable { background-color:#FFFFE0;border-collapse:collapse; }\n")
        fopen.write(".myTable td, .myTable th { padding:5px;border:1px solid #BDB76B; }\n")
        fopen.write("</style>\n")
        fopen.write("\n")
        fopen.write("<html>\n")
        fopen.write("<body>\n")
        fopen.write('<table class="myTable" border="8" width="1500" align="center"\n')
        fopen.write("<tr>\n")
        if self.include_module_report:
            fopen.write("<th><big>Module</big></th>\n")
        fopen.write("<th><big>Test Case Name</big></th>\n")
        fopen.write("<th><big>Test Case Description</big></th>\n")
        fopen.write("<th><big>Docs Link</big></th>\n")
        fopen.write("<th><big>Test Result</big></th>\n")
        fopen.write("<th><big>Test Time</big></th>\n")
        fopen.write("<th><big>Logs</big></th>\n")
        fopen.write("</tr>\n")

        for line in self.res_report:
            fopen.write("<tr>\n")
            if self.include_module_report:
                fopen.write("<td>{0}</td>\n".format(line[6]))
            fopen.write("<td>{0}</td>\n".format(line[0]))
            fopen.write("<td>{0}</td>\n".format(line[1]))
            fopen.write('<td><pre><a href="{0}">Doc Link</a><br></pre></td>'.format(line[2]))
            if line[3] == "PASS":
                fopen.write('<td bgcolor="#80FF00">\n'.format(line[3]))
            if line[3] == "FAIL" or line[3] == "ERROR":
                fopen.write('<td bgcolor="#FF0000">\n'.format(line[3]))
            if line[3] == "SKIPPED":
                fopen.write('<td bgcolor="#FACC2E">\n'.format(line[3]))
            fopen.write("{0}</td>\n".format(line[3]))
            fopen.write("<td>{0}</td>\n".format(line[4]))
            if line[3] == "SKIPPED":
                fopen.write('<td></td>'.format(line[5]))
            else:
                fopen.write('<td><pre><a href="{0}">Logs</a><br></pre></td>'.format(line[5]))
            fopen.write("</tr>\n")

        fopen.write("</tr>\n")
        fopen.write("</table>\n")
        fopen.write("<br>\n")
        fopen.write("<br>\n")
        fopen.write("<br>\n")
        fopen.write('<table class="myTable" border="8" width="1300" align="center">\n')
        fopen.write("<tr>\n")
        fopen.write('<th colspan="7"><big>OVERALL SUMMARY REPORT</big></th>\n')
        fopen.write("</tr>\n")
        fopen.write("<th><big>TOTAL TESTS FOUND</big></th>\n")
        fopen.write("<th><big>TOTAL TESTS RUN</big></th>\n")
        fopen.write("<th><big>PASSED</big></th>\n")
        fopen.write("<th><big>FAILED</big></th>\n")
        fopen.write("<th><big>ERRORS</big></th>\n")
        fopen.write("<th><big>SKIPPED</big></th>\n")
        fopen.write("<th><big>PASS PERCENTAGE RATE(OF TESTS RUN)</big></th>\n")
        fopen.write("</tr>\n")
        fopen.write("<tr><td><big>{0}</big></td><td><big>{1}</big></td><td><big>{2}</big></td><td><big>{3}</big></td><td><big>{4}</big></td><td><big>{5}</big></td><td><big>{6}</big></td></tr>\n".format(total_skip, total, passed, failed, errors, skipped, passrate))
        fopen.write("</table>\n")
        if self.include_module_report:
            fopen.write("</tr>\n")
            fopen.write("</table>\n")
            fopen.write("<br>\n")
            fopen.write("<br>\n")
            fopen.write("<br>\n")
            fopen.write('<table class="myTable" border="8" width="1300" align="center">\n')
            fopen.write("<tr>\n")
            fopen.write('<th colspan="8"><big>MODULE SUMMARY REPORT</big></th>\n')
            fopen.write("</tr>\n")
            fopen.write("<th><big>MODULE</big></th>\n")
            fopen.write("<th><big>TESTS FOUND</big></th>\n")
            fopen.write("<th><big>TESTS RUN</big></th>\n")
            fopen.write("<th><big>PASSED</big></th>\n")
            fopen.write("<th><big>FAILED</big></th>\n")
            fopen.write("<th><big>ERRORS</big></th>\n")
            fopen.write("<th><big>SKIPPED</big></th>\n")
            fopen.write("<th><big>PASS PERCENTAGE RATE(OF TESTS RUN)</big></th>\n")
            fopen.write("</tr>\n")
            for line in module_res_dict:
                fopen.write("<tr>\n")
                fopen.write("<tr><td><big>{7}</big></td><td><big>{0}</big></td><td><big>{1}</big></td><td><big>{2}</big></td><td><big>{3}</big></td><td><big>{4}</big></td><td><big>{5}</big></td><td><big>{6}</big></td></tr>\n".format(module_res_dict[line][0], module_res_dict[line][1], module_res_dict[line][2], module_res_dict[line][3], module_res_dict[line][4], module_res_dict[line][5], module_res_dict[line][6], line))
                fopen.write("</tr>\n")
            fopen.write("</table>\n")
        fopen.write("</body>\n")
        fopen.write("</html>\n")
        fopen.close()

        if not self.test_ai_option:
            self.collect_logs()

        if self.timeout_failure:
            print "ERROR: Timeout limit reached on last test run, please investigate"
            return False
        if failed == 0 and errors == 0:
            print "Test Run has Passed"
        else:
            print "ERROR: There are test failures"
            if not self.continue_on_fail:
                return False

        if not tr_result:
            print "ERROR: Test environment is corrupt, please investigate"
            return False
        return True

    def validate_environment(self):
        """
        Validate the test runner setup
        """

        # Check the test directory exists
        if not os.path.isdir(self.test_directory):
            print "Test directory {0} does not exist\n".format(self.test_directory)
            exit(1)
        # Check the correct test runner option was passed through
        if self.test_runner_option not in self.valid_options:
            print "INVALID OPTION:\n"
            exit(1)

    def copy_image_to_ms(self, filepath_local):
        """
        Copies a file from the local machine to the MS using the given paths.
        """
        # Create image dir
        ms_image_path = "/var/www/html/images"
        ms_ip, ms_passwd = self.get_ms_host_info()
        node = NodeConnect(ms_ip, "root", ms_passwd)
        cmd = "mkdir -p {0}".format(ms_image_path)
        node.run_command(cmd, logs=False)

        # Copy each file over
        image_filelist = ["vm-image-1.0.1.qcow2",
                          "vm_test_image-1-1.0.6.qcow2",
                          "vm_test_image-2-1.0.8.qcow2",
                          "vm_test_image-3-1.0.8.qcow2",
                          "vm_test_image-4-1.0.8.qcow2",
                          "vm_test_image-5-1.0.7.qcow2",
                          "vm_test_image_neg-1-1.0.7.qcow2",
                          "vm_test_image_neg-2-1.0.7.qcow2",
                          "vm_test_image_neg-3-1.0.6.qcow2",
                          "vm_test_image-SLES15-1.24.3.qcow2"]

        for image in image_filelist:

            image_filename = image
            local_path = "{0}/{1}".format(filepath_local,
                                          image_filename)

            cmd = "[ -f {0} ]".format(local_path)
            _, _, exit_code = self.run_command_local(cmd, logs=False)
            # If file doesn't exist
            if exit_code != 0:
                continue

            full_remote_path = "{0}/{1}".format(ms_image_path,
                                                image_filename)

            print "Copying {0} to MS ({1}) on path {2}"\
                .format(local_path,
                        ms_ip,
                        full_remote_path)

            node.copy_file_to(local_path, full_remote_path)
            awk_cmd = "awk  '{print $1;}'"
            cmd = "/usr/bin/md5sum {0} | {1} > {0}.md5"\
                .format(full_remote_path,
                        awk_cmd)

            print "Performing MD5 sum of {0}".format(full_remote_path)

            _, stderr, exit_code = node.run_command(cmd, logs=False)

            if exit_code != 0 or stderr != []:
                print "----------------------------------------------"
                print stderr
                print exit_code
                print "ERROR: Cannot MD5Sum Image"
                print "----------------------------------------------"
                exit(1)

            cmd = "rm -rf {0}".format(local_path)
            self.run_command_local(cmd, logs=False)

    def get_litp_version(self):
        """
        log onto the MS and get the litp version
        """

        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        # GET LITP VERSION
        node = NodeConnect(ms_ip, "root", ms_passwd)
        cmd = "litp version -a"
        stdout, stderr, exit_code = node.run_command(cmd, logs=True)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: LITP service is not running"
            print "----------------------------------------------"
            exit(1)
    def create_snapshot(self):

        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        status_command = '/usr/bin/litp show_plan | grep "Plan Status"'
        node = NodeConnect(ms_ip, "root", ms_passwd)

        cmd = "litp remove_snapshot"
        stdout, stderr, _ = node.run_command(cmd, logs=True)
        print "this is stdout {0}".format(str(stderr))

        if any("DoNothingPlanError" in s for s in stderr):
            print 'No snapshot exists: executing create_snapshot'
        else:
            while True:
                stdout, stderr, exit_code = node.run_command(status_command,
                                                                logs=True)
                if any("Success" in s for s in stdout):
                    break
                time.sleep(5)

        cmd = "litp create_snapshot"
        stdout, stderr, exit_code = node.run_command(cmd, logs=True)

        if any("DoNothingPlanError" in s for s in stderr):
            print "snapshot exist"
        else:
            while True:
                stdout, stderr, exit_code = node.run_command(status_command,
                                                                 logs=True)
                if any("Success" in s for s in stdout):
                    break
                time.sleep(5)
        return

    def collect_logs(self):
        """
        Collect logs after a test run has complete
        """

        print "Collecting litp logs from the system..."

        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        # SCP FILES TO MS

        node = NodeConnect(ms_ip, "root", ms_passwd)
        # COPY THE LOG COLLECTION SCRIPTS ACROSS TO THE MS
        local_path = os.path.dirname(os.path.realpath(__file__)) + "/collectlogs.sh"
        remote_path = "/tmp/collectlogs.sh"
        node.copy_file_to(local_path, remote_path)
        local_path = os.path.dirname(os.path.realpath(__file__)) + "/scp_file.exp"
        remote_path = "/tmp/scp_file.exp"
        node.copy_file_to(local_path, remote_path)
        local_path = os.path.dirname(os.path.realpath(__file__)) + "/key_setup.exp"
        remote_path = "/tmp/key_setup.exp"
        node.copy_file_to(local_path, remote_path)
        # Launching the script for db backup
        cmd_backup = '/opt/ericsson/nms/litp/bin/litp_state_backup.sh /tmp'
        stdout, stderr, exit_code = node.run_command(cmd_backup, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: state backup script failed"
            print "----------------------------------------------"
        if os.getenv("EXPORT_MODEL", "false") == "true":
            # This parameter helps to export the model to logs also
            cmd = "sh /tmp/collectlogs.sh -export > /tmp/message_collection_log.log"
        else:
            cmd = "sh /tmp/collectlogs.sh > /tmp/message_collection_log.log"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Node collection script failed"
            print "----------------------------------------------"


        cmd = "ls /tmp/ | grep 'litp_messages_' | grep '.tar.gz'"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: No log .tar.gz file exists"
            print "----------------------------------------------"


        remote_path = "/tmp/message_collection_log.log"
        local_path = self.results_dir + "/" + "message_collection_log.log"
        print "Copy of %s from %s to %s" % (remote_path, ms_ip, local_path)
        node.copy_file_from(remote_path, local_path)

        remote_path = "/tmp/" + stdout[0]
        local_path = self.results_dir + "/" + stdout[0]
        print "Copy of %s from %s to %s" % (remote_path, ms_ip, local_path)
        node.copy_file_from(remote_path, local_path)

        cmd = "rm -rf %s /tmp/message_collection_log.log /tmp/collectlogs.sh /tmp/scp_file.exp /tmp/key_setup.exp" % remote_path
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Deletion of files failed"
            print "----------------------------------------------"


    def sanity_setup(self):
        """
        Check the test environment is ok before running the test suite
        """
        print "In Setup Sanity"
        # GET ALL HOSTS IN TEST ENVIRONMENT TO PING
        cmd = "cat {0} | grep host | grep ip | sed 's/^.*=//'".format(self.connection_file)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Cannot get environment information "
            print "----------------------------------------------"
            exit(1)

        # RUN PING AGAINST ALL HOSTS IN THE ENVIRONMENT

        hosts = stdout
        for line in hosts:
            cmd = "ping %s -c 1" % line
            stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
            if exit_code != 0:
                count = 0
                while count < 30:
                    stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
                    if exit_code == 0 and "1 packets transmitted, 1 received, 0% packet loss" in stdout:
                        break
                    count += 1
                    time.sleep(1)
                if count == 30:
                    print "----------------------------------------------"
                    print "ERROR: Cannot ping %s, tried %d times" % (line, count)
                    print "----------------------------------------------"
                    exit(1)

        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        node = NodeConnect(ms_ip, "root", ms_passwd)
        cmd = "service litpd status"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: LITP service is not running"
            print "----------------------------------------------"
            exit(1)
        print "Pre test suite run Sanity Check has passed"

        # SETUP FOR POST TEST CASE CHECK TO MAKE SURE MODEL DOES NOT GET CORRUPTED
        cmd = 'litp show -r -p / | grep -v "timestamp:" > /tmp/initial_tr_plan.txt'
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Show of model failed"
            print "----------------------------------------------"
            exit(1)
        cmd = 'sort /tmp/initial_tr_plan.txt -o /tmp/initial_tr_plan_sorted.txt'
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Sort of file failed"
            print "----------------------------------------------"
            exit(1)

    def get_ms_host_info(self):
        # GET MS NODE INFORMATION
        cmd = "cat {0} | grep MS".format(self.connection_file)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Cannot get environment information "
            print "----------------------------------------------"
            exit(1)

        ms_hostname = stdout[0].split(".")[1]

        cmd = "cat {1} | grep host.{0}.ip | sed 's/^.*=//'".format(ms_hostname, self.connection_file)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Cannot get environment information "
            print "----------------------------------------------"
            exit(1)
        ms_ip = stdout[0]
        cmd = "cat {0} | grep host.{1}.user.root | sed 's/^.*=//'".format(self.connection_file, ms_hostname)
        stdout, stderr, exit_code = self.run_command_local(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Cannot get environment information "
            print "----------------------------------------------"
            exit(1)
        ms_passwd = stdout[0]

        return ms_ip, ms_passwd

    def pre_test_sanity(self):
        """
        Pre test case sanity check
        """
        # Print "DEBUG - RUNNING PRE SANITY CHECK"
        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        node = NodeConnect(ms_ip, "root", ms_passwd)
        cmd = "service litpd status"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: LITP service is not running"
            print "----------------------------------------------"
            exit(1)

    def post_test_sanity(self):
        """
        Post test case sanity check
        """
        # GET MS NODE INFORMATION
        ms_ip, ms_passwd = self.get_ms_host_info()

        node = NodeConnect(ms_ip, "root", ms_passwd)
        cmd = "service litpd status"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout == []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Cannot get environment information "
            print "----------------------------------------------"
            return False

        cmd = 'litp show -r -p / | grep -v "timestamp:" > /tmp/latest_tr_plan.txt'
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Show of model failed"
            print "----------------------------------------------"
            return False

        cmd = 'sort /tmp/latest_tr_plan.txt -o /tmp/latest_tr_plan_sorted.txt'
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: Sort of file failed"
            print "----------------------------------------------"
            exit(1)

        cmd = "diff <(sed 's/ \[\*\]//g' /tmp/initial_tr_plan_sorted.txt) <(sed 's/ \[\*\]//g' /tmp/latest_tr_plan_sorted.txt)"
        stdout, stderr, exit_code = node.run_command(cmd, logs=False)
        if exit_code != 0 or stderr != [] or stdout != []:
            print "----------------------------------------------"
            print stdout
            print stderr
            print exit_code
            print "ERROR: LITP Model has changed during test case"
            print "----------------------------------------------"
            return False

        return True

class Util:

    @staticmethod
    def run_command_local(cmd, logs=True):
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

    @staticmethod
    def do_get(url_to_get):
        r = TmsResponse()
        r.method="GET"
        r.url=url_to_get
        try:
            res = urllib.urlopen(url_to_get)
            r.rc=res.getcode()
            r.url=res.geturl()
            if res.getcode() in [200,201]:
                parse =  json.loads(res.read())
                r.response=parse
            else:
                r.error="Unexpected return code " + str(res.getcode())
        except urllib2.HTTPError as e:
            r.error=e.read()
            r.url=e.geturl()
            r.rc=e.getcode()
        except Exception as e:
            print e
            r.error="Unexpected error during GET"
        return r

    @staticmethod
    def do_call(url_to_post, data=None, method="POST",session_id=None):

        req = urllib2.Request(url_to_post)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Cookie', session_id)
        req.get_method = lambda: method
        r = TmsResponse()
        r.method=method
        r.url=url_to_post
        try:
            if data:
                res = urllib2.urlopen(req, json.dumps(data))
            else:
                res = urllib2.urlopen(req)
            res = urllib.urlopen(url_to_post)
            r.rc=res.getcode()
            r.url=res.geturl()
            if res.getcode() in [200,201]:
                parse =  json.loads(res.read())
                r.response=parse
        except urllib2.HTTPError as e:
            r.error=e.read()
            r.url=e.geturl()
            r.rc=e.getcode()
        except Exception as e:
            r.error="Unexpected error during {0}".format(method)
        return r

class TmsResponse:
    def __init__(self):
        self.response = None
        self.error = None
        self.rc = None
        self.url = None
        self.method = None

    def __str__(self):
        return json.dumps(self.__dict__)

    __repr__=__str__

class Tms:


    def __init__(self):
        self.add_to_tms=True
        self.enable_tms_upload=True
        self.tms_url="https://taftm.seli.wh.rnd.internal.ericsson.com/" \
            + "tm-server/api/"
        self.tms_login_url = self.tms_url + "login/"

        self.session_id = None

        self.logger=[]

        self.username = "YZNGLKXJQW"
        self.password = "C7GjBnDNmWryjNZXYHFXUDmJ"

    def do_tms_update(self, tms_data):
        tms_data_from_file = self.build_tms_request(tms_data)
        tms_id = tms_data["tms_id"]
        test_info = self.get_test(tms_id)
        update = None
        if test_info.response:
            if not self.compare_tms_records(tms_data_from_file, test_info.response):
                update = self.put_test_data(test_info.response["id"],
                                            tms_data_from_file)
                if update.error or not update.response:
                    if "reliminary" in update.error:
                        self.post_test_version(tms_id)
                        attempt_2 = self.put_test_data(
                            test_info.response["id"],
                            tms_data_from_file)
                        update =attempt_2
                        if attempt_2.error:
                            self.log(tms_id,
                                    "Failed: {0}".format(str(attempt_2.error)))
                        else:
                            self.log(tms_id, "OK - Created new version")
                    else:
                        self.log(tms_id, "ERROR - Unexpected error {0}".format(
                            update.error))
                else:
                    self.log(tms_id, "OK - Test modified, no version change needed")
            else:
                self.log(tms_id, "N/A - Update not required")
        else:
            self.log(tms_id, "Test not found in TMS, creating...", test_info)
            creation_status = self.post_test_data(tms_data_from_file)
            if creation_status.error:
                self.log(tms_id, "Error creating test record", creation_status)
            else:
                self.log(tms_id, "OK - Created new test record")
        return update

    def compare_tms_records(self, rec1, rec2,reasons=None):
        d1 = rec1["description"]
        d2 = rec2["description"]
        s1 = rec1["testSteps"]
        s2 = rec2["testSteps"]

        if d1 != d2:
            return False

        if len(s1) != len(s2):
            return False

        for i, s in enumerate(s1):
            if s["name"] != s2[i]["name"]:
                return False
            v1= s["verifies"]
            v2= s2[i]["verifies"]
            if len(v1) != len(v2):
                return False
            for j, res1 in enumerate(v1):
                if res1["name"] != v2[j]["name"]:
                    return False
        return True



    def upload_to_tms(self, tms_doc):
        # UPDATE TMS WITH INFO

        fail_tms_upload_count=0

        if self.add_to_tms and self.enable_tms_upload:
            self.login_tms_session()
            try:
                tms_doc["add_to_allure"] = True
                update_status = self.do_tms_update(tms_doc)
                tms_doc["tms_story_title"] = self.get_requirements_data(update_status,tms_doc)
                if tms_doc["tms_story_title"] == None:
                    del tms_doc["add_to_allure"]

            except Exception as e:
                pprint.pprint(e)
                print "Error during TMS update - does not affect test execution."
                fail_tms_upload_count += 1
            finally:
                if fail_tms_upload_count > 2:
                    # Disable uploads after failures.
                    self.enable_tms_upload = False

    def parse_tms(self,file_lines, testcase_name):
        # TMS RELATED INFORMATION FROM TEST CASE DESCRIPTION
        tms_doc = {}
        tms_test_steps = []
        testcopy = False
        tmsid_copy = ""
        tmsid_copy_p = False
        tmsreq_copy = ""
        tmsreq_copy_p = False
        tmstitle_copy = ""
        tmstitle_copy_p = False
        startcopy = False
        copy_desc = ""
        desc_copy = False
        steps_copy = False
        step_desc = ""
        steps_copy_p = False
        res_copy_p = False
        res_copy_list = []
        res_desc = ""
        req_copy = False
        req_desc = ""
        # DEFAULT PROPERTIES (IF NEEDED TO BE MANDATORY IN FUTURE CAN BE ADDED BELOW)
        tms_doc["tms_type"] = {"tms_type_id": 1,
                               "tms_type_title": "Functional"}
        tms_doc["tms_component"] = "LITP"
        tms_doc["tms_priority"] = {"tms_priority_id": 2,
                                   "tms_priority_title": "Normal"}
        tms_doc["tms_groups"] = []
        tms_doc["tms_test_case_status"] = {"tms_test_case_status_id": 1,
                                           "tms_test_case_status_title": "Approved"}
        tms_doc["tms_automation_candidate"] = {
            "tms_automation_candidate_id": 1,
            "tms_automation_candidate_title": "Yes"}
        tms_doc["tms_contexts"] = []
        tms_doc["tms_feature"] = {"id": "21", "title": "Deployment",
                                  "product": {"id": 2, "externalId": "ENM",
                                              "name": "ENM",
                                              "dropCapable": True}}
        tms_doc["tms_techComponent"] = {"id": "1152", "title": "LITP"}
        # PARSE EACH LINE IN TEST DESCRIPTION
        for line in file_lines:
            # IF TEST IS FOUND THEN START COPY
            if "def {0}(self):".format(testcase_name) in line:
                testcopy = True
            # IF END OF TEST DESCRIPTION THEN BREAK OUT
            if "\"\"\"" in line or "'''" in line:
                if testcopy and startcopy:
                    break
            # UPDATE TO START DOC COPY IF """/''' IS FOUND
            if "\"\"\"" in line or "'''" in line:
                if testcopy and not startcopy:
                    startcopy = True
            if testcopy and startcopy:
                # IF TMS ID IS PRESENT SET IT
                if "@tms_id:" in line:
                    tmsid_copy_p = True
                    tmsid_copy = line.split(":")[-1].replace(" ", "")
                if "@tms_id:" not in line and tmsid_copy_p and "@tms_requirements_id:" not in line:
                    tmsid_copy = tmsid_copy + line.strip().replace(" ", "")
                # IF REQUIREMENT ID IS PRESENT SET IT
                if "@tms_requirements_id:" in line:
                    tmsid_copy_p = False
                    tms_doc["tms_id"] = tmsid_copy
                    tmsreq_copy = line.split(":")[-1].replace(" ", "")
                    tmsreq_copy_p = True
                if "@tms_title:" not in line and tmsreq_copy_p and "@tms_requirements_id:" not in line:
                    tmsreq_copy = tmsreq_copy + line.strip().replace(" ", "")
                # IF TITLE IS PRESENT SET IT
                if "@tms_title:" in line:
                    tms_doc["tms_requirements_id"] = tmsreq_copy
                    tmsreq_copy_p = False
                    tmstitle_copy = "{0}{1}".format(tmstitle_copy,
                                                    line.split(":")[-1])
                    tmstitle_copy_p = True
                # IF DESCRIPTION IS PRESENT START COPYING IT
                if "@tms_title:" not in line and tmstitle_copy_p and "@tms_description:" not in line:
                    tmstitle_copy = "{0} {1}".format(tmstitle_copy,
                                                     line.strip())
                if "@tms_description:" in line:
                    tms_doc["tms_title"] = tmstitle_copy.replace("'",
                                                                 "").replace(
                        '"', '')
                    tmstitle_copy_p = False
                    desc_copy = True
                    copy_desc = "{0}{1}".format(copy_desc, line.split(":")[-1])
                # UNTIL NEXT TAG IS FOUND THE DESCRIPTION STILL NEEDS TO BE COPIED (SPREAD OVER MULTIPLE LINES)
                if desc_copy and "@tms_description:" not in line and "@tms_test_steps:" not in line:
                    copy_desc = "{0} {1}".format(copy_desc, line.strip())
                # IF DESCRIPTION IS PRESENT START COPYING IT
                if "@tms_test_steps:" in line:
                    # BUT FIRST SET THE PREVIOUS DESCRIPTION AS NOW IT HAS COMPLETED COPY
                    tms_doc["tms_description"] = copy_desc.replace("'",
                                                                   "").replace(
                        '"', '')
                    desc_copy = False
                    copy_desc = ""
                    steps_copy = True
                # START COPYING STEPS AND RESULTS
                # ORDER IS ALWAYS STEP/RESULT, STEP/RESULT
                if steps_copy and "@tms_test_steps:" not in line and "@tms_test_precondition:" not in line:
                    if "@result:" in line and steps_copy_p and res_copy_p:
                        res_copy_list.append(
                            res_desc.replace("'", "").replace('"', ''))
                        res_desc = ""
                        res_desc = "{0}{1}".format(res_desc,
                                                   line.split(":")[-1].strip())
                    # IF RESULT IN LINE, START COPY OF RESULT STRING
                    if "@result:" in line and steps_copy_p and not res_copy_p:
                        res_copy_p = True
                        res_desc = "{0}{1}".format(res_desc,
                                                   line.split(":")[-1].strip())
                    # IF RESULT COPY IS STILL ONGOING IN LINE, CONTINUE COPY OF RESULT STRING
                    if res_copy_p and "@step" not in line and "@result:" not in line:
                        res_desc = "{0} {1}".format(res_desc, line.strip())
                    # IF NEW STEP IS FOUND STOP COPYING PREVIOUS STEP/RESULT
                    if "@step:" in line and steps_copy_p:
                        res_copy_p = False
                        steps_copy_p = False
                        res_copy_list.append(
                            res_desc.replace("'", "").replace('"', ''))
                        # APPEND PREVIOUS STEP/RESULT TO STEP TEST LIST
                        tms_test_steps.append(
                            [step_desc.replace("'", "").replace('"', ''),
                             res_copy_list])
                        step_desc = ""
                        res_desc = ""
                        res_copy_list = []
                    # IF STEP IN LINE, START COPY OF STEP STRING
                    if "@step:" in line and not steps_copy_p:
                        steps_copy_p = True
                        step_desc = "{0}{1}".format(step_desc, line.split(":")[
                            -1].strip())
                    # IF STEP COPY IS STILL ONGOING IN LINE, CONTINUE COPY OF RESULT STRING
                    if steps_copy_p and "@step:" not in line and not res_copy_p and "@result:" not in line:
                        step_desc = "{0} {1}".format(step_desc, line.strip())
                # IF PRECONDITION IS SET, START COPY
                if "@tms_test_precondition:" in line:
                    # APPEND PREVIOUS STEP/RESULT TO STEP TEST LIST
                    res_copy_list.append(
                        res_desc.replace("'", "").replace('"', ''))
                    tms_test_steps.append(
                        [step_desc.replace("'", "").replace('"', ''),
                         res_copy_list])
                    res_copy_list = []
                    # SET IN DICTIONARY
                    tms_doc["tms_test_steps"] = tms_test_steps
                    res_copy_p = False
                    steps_copy_p = False
                    steps_copy = False
                    step_desc = ""
                    res_desc = ""
                    req_copy = True
                    req_desc = "{0}{1}".format(req_desc,
                                               line.split(":")[-1].strip())
                if req_copy and "@tms_test_precondition:" not in line and "@tms_execution_type:" not in line:
                    req_desc = "{0} {1}".format(req_desc, line.strip())
                # IF EXECUTION TYPE FOUND SET IT
                if "@tms_execution_type:" in line:
                    # NOW PRECONDITION PROPERTY COPY COMPLETE, SET IT
                    tms_doc["tms_test_precondition"] = req_desc.replace("'",
                                                                        "").replace(
                        '"', '')
                    req_copy = False
                    tms_doc["tms_execution_type"] = line.split(":")[
                        -1].replace(" ", "")
        return tms_doc

    def login_tms_session(self):
        """
        Login to TMS and return session id to be used for further rest calls
        """
        outp, errp, rc = Util.run_command_local('curl -v -H "Content-Type: application/json"' \
         + ' -X POST {0} -d \'{{"username": "{1}", "password": "{2}"}}\' 2>&1'.format(self.tms_login_url, self.username, self.password), logs=False)
        for line in outp:
            if "JSESSIONID=" in line:
                self.session_id = line.split(";")[0].split()[-1]
        if self.session_id == None:
            print "ERROR: Cannot log into TMS server"
            return False
        return True

    def get_test(self, id):
        url = self.tms_url + "test-cases/" + str(id) + "?view=detailed"
        res = Util.do_get(url)
        return res

    def get_test_versions(self, id):
        url = self.tms_url + "test-cases/" + str(id)+"/versions"
        return Util.do_get(url)

    def post_test_data(self, data):
        url = self.tms_url+"test-cases/"
        return Util.do_call(url,data,session_id=self.session_id)

    def post_test_version(self,test_id):
        url = self.tms_url+"test-cases/"+str(test_id)+"/versions"
        return Util.do_call(url,session_id=self.session_id)

    def put_test_data(self, test_id, data):
        url = self.tms_url+"test-cases/"+str(test_id)
        data["id"]=test_id
        return Util.do_call(url,data,"PUT",self.session_id)

    def log(self, test_id, message, response_object=None):
        using = str(response_object)
        if not response_object:
            using=""
        self.logger.append("{0} - {1} - {2}".format(test_id,message,using))

    def get_requirements_data(self, ret_data, tms_doc):
        # LOOP THROUGH REQUIREMENTS IN RETURN
        # AS TMS WILL RETURN THE TEST CASE SUMMARY IN THE OUTPUT, APPEND AND RETURN
        # SO IT CAN BE USED IN THE ALLURE REPORT
        story_descriptions = []

        if ret_data == None:
            if not tms_doc["tms_requirements_id"]==None:
                for desc in tms_doc["tms_requirements_id"].split(","):
                    story_descriptions.append("{0}".format(desc))
        else:
            if ret_data \
                    and ret_data.response \
                    and "requirements" in ret_data.response:
                if ret_data.response["requirements"]==None:
                    reqs = []
                else:
                    reqs = ret_data.response["requirements"]
                for desc in reqs:
                    story_descriptions.append("{0} - {1}".format(desc["label"],
                                                                 desc[
                                                                     "summary"].replace(
                                                                     "'",
                                                                     "").replace(
                                                                     '"',
                                                                     '').replace(
                                                                     '&',
                                                                     '&amp;')))
        return story_descriptions

    def build_tms_request(self, tms_doc):
        # PROPERTIES ORGANISED/PARSED TO BE USED BELOW TO GENERATE REST CALL
        if tms_doc["tms_execution_type"] == "Automated":
            execution_type_id = "2"
            execution_type_title = "Automated"
        else:
            execution_type_id = "1"
            execution_type_title = "Manual"
        test_stps = tms_doc["tms_test_steps"]
        teststeps = []
        for step in test_stps:
            step_dict = {}
            verifies = []
            step_dict["name"] = step[0]
            for resstp in step[1]:
                verifies.append({"name": resstp})
            step_dict["verifies"] = verifies
            teststeps.append(step_dict)
        datar = {
            "title": "{0}".format(tms_doc["tms_title"]),
            "requirementIds": tms_doc["tms_requirements_id"].split(","),
            "testCaseStatus": {"id": tms_doc["tms_test_case_status"][
                "tms_test_case_status_id"], "title": "{0}".format(
                tms_doc["tms_test_case_status"][
                    "tms_test_case_status_title"])},
            "automationCandidate": {"id": tms_doc["tms_automation_candidate"][
                "tms_automation_candidate_id"], "title": "{0}".format(
                tms_doc["tms_automation_candidate"][
                    "tms_automation_candidate_title"])},
            "priority": {"id": tms_doc["tms_priority"]["tms_priority_id"],
                         "title": "{0}".format(
                             tms_doc["tms_priority"]["tms_priority_title"])},
            "executionType": {"id": execution_type_id,
                              "title": "{0}".format(execution_type_title)},
            "testCaseId": "{0}".format(tms_doc["tms_id"]),
            "description": "{0}".format(tms_doc["tms_description"]),
            "precondition": "{0}".format(tms_doc["tms_test_precondition"]),
            "type": {"id": tms_doc["tms_type"]["tms_type_id"],
                     "title": "{0}".format(
                         tms_doc["tms_type"]["tms_type_title"])},
            "groups": [],
            "contexts": [],
            "component": "{0}".format(tms_doc["tms_component"]),
            "testSteps": teststeps,
            "feature": tms_doc["tms_feature"],
            "technicalComponents": [tms_doc["tms_techComponent"]]
        }
        return datar

def main():
    """
    main function
    """

    # Disable output buffering to receive the output instantly
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)
    if len(sys.argv) < 2:
        print USAGE
        exit(1)
    test_runner_option = sys.argv[1]
    if test_runner_option == "-rs" or test_runner_option == "--help" or test_runner_option == "-h":
        if test_runner_option == "--help" or test_runner_option == "-h":
            print USAGE
            exit(0)
    else:
        print USAGE
        exit(1)
    target_dir = None
    results_loc = None
    selected_tc_file = None
    connection_file = None
    utils_dir = None
    image_path = None
    for line in sys.argv:
        if "--test-dir=" in line:
            target_dir = line.split("=")[-1]
        if "--results-dir=" in line:
            results_loc = line.split("=")[-1]
        if "--test-type=" in line:
            selected_tc_file = line.split("=")[-1]
        if "--connection-file=" in line:
            connection_file = line.split("=")[-1]
        if "--utils-dir=" in line:
            utils_dir = line.split("=")[-1]
        if "--copy-vm-image=" in line:
            image_path = line.split("=")[-1]

    if target_dir == None or results_loc == None or selected_tc_file == None or connection_file == None or utils_dir == None:
        print USAGE
        exit(1)
    continue_fail = False
    run_sanity = False
    run_regr = True
    report_only = False
    report_module = False
    testoption = False
    nasserver = False
    physical = False
    expansion = False
    cdb_tests = False
    kgb_only_tests = False
    kgb_physical_only = False
    report_allure = False
    cdb_regression_run = False
    add_tms_det = False
    bur_run = False
    exclude_db = False
    is_snapshot = False
    ignore_va = False
    ignore_sfs = False
    verbose_logging=False

    if "--exclude_db" in sys.argv:
        exclude_db = True
    if "--continue-on-fail" in sys.argv:
        continue_fail = True
    if "--run-sanity" in sys.argv:
        run_sanity = True
    if "--run-non-reg" in sys.argv:
        run_regr = False
    if "--include-physical" in sys.argv:
        physical = True
    if "--include-expansion" in sys.argv:
        expansion = True
    if "--include-cdb-only" in sys.argv:
        cdb_tests = True
    if "--include-kgb-only" in sys.argv:
        kgb_only_tests = True
    if "--include-kgb-physical-only" in sys.argv:
        kgb_physical_only = True
    if "--include-bur-tests-only" in sys.argv:
        bur_run = True
    if "--report-tests-run" in sys.argv:
        report_only = True
    if "--include-module-report" in sys.argv:
        report_module = True
    if "--create-allure-report" in sys.argv:
        report_allure = True
    if "--add-to-tms" in sys.argv:
        add_tms_det = True
    if "--cdb-regression-run" in sys.argv:
        cdb_regression_run = True
        # Including modules for cdb_regression run automatically
        report_module = True
    if "--ignore-sfs-only" in sys.argv:
        ignore_sfs=True
    if "--ignore-va-only" in sys.argv:
        ignore_va=True
    # OPTION TO TEST AUTOINSTALL CODE LOCALLY
    if "--test-ai" in sys.argv:
        testoption = True
    # THIS IS A TEMP WORKAROUND, PLEASE DO NOT TOUCH
    if "--add-local-nas" in sys.argv:
        nasserver = True
    if "--verbose" in sys.argv:
        verbose_logging=True
    print ""
    print "----------------------------"
    print "Test runner Option: ", test_runner_option
    print "Test cases parent directory: ", target_dir
    print "Location of test results: ", results_loc
    print "Test Tags to run: ", selected_tc_file
    print "Test connection file: ", connection_file
    print "Test utilities location", utils_dir
    print "Option to continue if a test case fails: ", continue_fail
    print "Option to run a sanity check in between test cases: ", run_sanity
    print "Option to ignore regression and run only new test cases with tag 'pre-reg': ", run_regr
    print "Option to include test cases with tag 'physical' in the test run", physical
    print "Option to include test cases with tag 'expansion' in the test run", expansion
    print "Option to include test cases with tag 'cdb-only' in the test run", cdb_tests
    print "Option to include test cases with tag 'kgb-other' in the test run", kgb_only_tests
    print "Option to include test cases with tag 'kgb-physical' in the test run", kgb_physical_only
    print "Option to copy image selected. Image:", image_path
    print "Option to create an allure test framework report:", report_allure
    print "Option to exclude db not ready tcs:", exclude_db
    print "----------------------------"
    print ""
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + ":" + utils_dir
    else:
        os.environ["PYTHONPATH"] = utils_dir
    print os.environ["PYTHONPATH"]
    os.environ["LITP_CONN_DATA_FILE"] = connection_file
    if "CREATE_SNAPSHOT" in os.environ:
        if os.environ["CREATE_SNAPSHOT"] == 'true':
            is_snapshot = True

    run_tests = RunTestCases(test_runner_option, target_dir, results_loc, connection_file, is_snapshot, test_type=selected_tc_file, continue_on_fail=continue_fail, run_sanity_check=run_sanity, run_regres=run_regr, report_only_run=report_only, test_ai_option=testoption, include_physical=physical, include_expansion=expansion, include_cdb=cdb_tests, include_kgb_other=kgb_only_tests, include_kgb_physical=kgb_physical_only, include_module_report=report_module, allure_report=report_allure, cdb_regression=cdb_regression_run, include_prepare_restore_other=bur_run, add_to_tms=add_tms_det, exclude_db=exclude_db,ignore_sfs=ignore_sfs,ignore_va=ignore_va,verbose_logging=verbose_logging)
    if nasserver:
        cmd = "hostname -i"
        stdout, _, _ = run_tests.run_command_local(cmd, logs=False)
        nasip = stdout[0]
        cmd = "hostname"
        stdout, _, _ = run_tests.run_command_local(cmd, logs=False)
        nashost = stdout[0]
        cmd = "echo '' >> %s" % connection_file
        run_tests.run_command_local(cmd, logs=False)
        cmd = "echo 'host.%s.ip=%s' >> %s" % (nashost, nasip, connection_file)
        run_tests.run_command_local(cmd, logs=False)
        cmd = "echo 'host.%s.ipv6=2001:1b70:82a1:103::171' >> %s" % (nashost, connection_file)
        run_tests.run_command_local(cmd, logs=False)
        cmd = "echo 'host.%s.user.root=shroot' >> %s" % (nashost, connection_file)
        run_tests.run_command_local(cmd, logs=False)
        cmd = "echo 'host.%s.port.ssh=22' >> %s" % (nashost, connection_file)
        run_tests.run_command_local(cmd, logs=False)
        cmd = "echo 'host.%s.type=NFS' >> %s" % (nashost, connection_file)
        run_tests.run_command_local(cmd, logs=False)

    if image_path:
        run_tests.copy_image_to_ms(image_path)

    if not testoption:
        cmd = "cat %s" % connection_file
        print "Test System Information:"
        print "---------------------------------"
        stdout, _, _ = run_tests.run_command_local(cmd, logs=False)
        for line in stdout:
            print line
        print "---------------------------------"
    if run_sanity:
        print "Sanity check is turned on"
    run_tests.run_test_suite()


if  __name__ == '__main__': main()
