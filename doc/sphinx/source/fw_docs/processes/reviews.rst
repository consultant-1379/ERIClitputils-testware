d.. _review-label:

Test Review Checklist
========================

This checklist should be followed when performing a review of a test script:


KGB/CDB Test Tags
~~~~~~~~~~~~~~~~~~~~~~~

With the KGB, tests are determined for running based on tags written above each test.

See the following exampls for details:

**1. Tests in development which are run in the beta-KGB:**

- @attr('pre-reg', 'non-revert', 'story100', 'story100_tc01')   (If a test is non-revertible)
- @attr('pre-reg', 'revert', 'story100', 'story100_tc01')   (If a test is revertible)

Note the following:

- The 'pre-reg' tag means the test is only run in beta-KGB. A story cannot be set to done if it has only ever been run in the beta-KGB.

- Each test should be tagged as 'non-revert' or 'revert'. The 'revert' tag means that after the test has been run, the LITP model is unchanged.

- Each test should have tags to indicate the story and test number so the test or the whole story of tests can be selected to run for debugging purposes.

**2. Tests in the KGB:**

- @attr('all', 'non-revert', 'story100', 'story100_tc01') (If a test is non-revertible)
- @attr('all', 'revert', 'story100', 'story100_tc01') (If a test is revertible)
- @attr('all', 'revert', 'story100', 'story100_tc01', 'kgb-physical') (If the test is a physical only test case. NOTE: Only use this tag if your module is set up for physical KGB.)

Note the following:

- By replacing the 'pre-reg' tag with 'all', the tests are now run in each KGB run. If the test fails, it will block publication of the RPM.

**3. Tests that can only be run on physical hardware:**

- @attr('all', 'revert', 'story100', 'story100_tc01', 'physical')

Note the following:

- The addition of the physical tag means that this test is only suitable for running on real hardware. This means that these tests will be run on the physical CDB.

**4. Tests which are run in the CDB:**

- @attr('all', 'revert', 'story100', 'story100_tc01', 'cdb_priority1')
- @attr('all', 'revert', 'story100', 'story100_tc01', 'cdb_priority1', 'cdb-only')

**5. Tests which can only be run in the cloud:**

- @attr('all', 'revert', 'story100', 'story100_tc01', 'cdb_priority1', 'cloud-only')

**6. Tests that are semi-automated, that can be run in an automated fashion but not in KGB/CDB (This tag is a way to store manual test cases):**

- @attr('manual-test')

**7. Tests that are for expansion KGB testing

- @attr('all', 'revert', 'story100', 'story100_tc01', 'expansion')

Note the following:

- Adding the 'cdb_priority1' tag means that after every new ISO, the CDB will automatically run this test case.

- Each new user story should have one test case to run in the CDB.

- If a CDB test case does not need to be run in the KGB of the affected team then, it can be tagged as 'cdb-only'.

- Tests to be run in the VCDB but not on physical should be tagged with 'cloud-only' and 'cdb_priority1'.


If a test in KGB fails, your RPM will not be published to the CDB/ISO. If a test in the CDB fails, then all Vapps will not be updated to the new baseline and a blocker bug is liable to be raised.


Review Preconditions
~~~~~~~~~~~~~~~~~~~~~~~

If the below conditions are not met, the review should be rejected and returned to the author to correct.

#. Pylint is passing 10/10. (See Framework Rules section for details of Pylint version and config file.)
#. Pep8 is passing with zero errors. (See Framework Rules section for details of Pylint version and config file.)
#. The file contains the following import line: from litp_generic_test import GenericTest, attr
#. The class inherits from Generic Test
#. No commenting out of test tags or tests due to bugs
#. No new tests which are named as 'obsolete\_'. You can specify specific tags in the beta-KGB so there is no need to comment out tests which don't currently pass or corrupt the environment.



Review Checklist Functional
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following functional items should be checked in the review:

#. Ensure all revertible tests perform cleanup as detailed in :ref:`cleanup-env-label`.

#. If a property is updated on a path, ensure it is backed up first (See :ref:`cleanup-env-label`). The only exception to this is if reverting values for these properties is unsupported or if the new values are required in later tests.

#. Ensure all non-revertible tests do not break the system. (For example, after running the test, create_plan should work.) The reviewer should not be running the test themselves, but if there is any doubt with regards to cleanup, the test script author should do a test run.

#. Paths in the LITP tree should NEVER be hardcoded. (E.g. node_path = "/deployments/d1/clusters/c1/nodes/n1") Instead, use the find command.

#. Test code must NEVER contain workarounds for existing bugs. (E.g. Unexplained sleep calls needed to make something work.)

#. The file contains a setUp and tearDown method.

#. Classnames should follow the convention 'StoryXXX' where XXX is the story under test. In rare cases where a file tests two storys, the convention StoryXXXStoryYYY may be used.

#. The setUp and tearDown methods have calls to the parent setUp and tearDown method. (super(StoryXXX, self).setUp() and super(StoryXXX, self).tearDown()).

#. The test code should always fail cleanly without reporting errors. Some examples of things to avoid in relation to this:
    - Do not add assertions to your setUp or tearDown methods. If you are doing common things that involve assertions before every test these should be declared in a seperate method which is called at the start of each test.
    - Do not index data structures directly without first asserting they are of a suitable length. (In some cases this will be handled in utils; for example, the find call asserts the returned path list is non-empty.)

#. Does the code do anything which is already covered in an existing util? The util should be used if it exists.

#. If code is reuseable but is not an existing util, discuss with the CI team about adding it as a utility.

#. File paths should be in the test_constants file, not hardcoded in the test.

#. No sleeps in test code should be required. In almost all cases where a sleep is required, a utility is available. (E.g. To wait for a plan to run etc.)

#. Assertions should follow the pattern identified in :ref:`logging-env-label`.

#. Are all return types asserted (e.g. stderr, stdout, rc) to be as expected?  Note that the LITP execute methods perform this at a basic level. (See :ref:`runcmds-env-label`)



Review Checklist Code Style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is important to follow a consistent style in test cases so that code is easy to read. A test case written by person A may well be later managed by person B so code that is readable and understandable is very important.

In light of this, the following should be considered:

#. Does each test method have a clear description stating what the method is testing and each step that the method performs?

#. Test case names follow the convention 'def test_xx_p_<high_level_name>(self):' or 'def test_xx_n_<high_level_name>(self):', where _p_ is a positive TC and _n_ is negative TC.

#. Use the Python .format notation instead of using %s. (%s is to be depreceated in later Python versions)


After the author has completed comments, the reviewer should take back the code to check comment implementation.

Reviewers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CI Code Reviewers are:

- The Mighty Ducks

On your Gerrit review, add "ERIClitp_themightyducks_guard" as a Reviewer. This will automatically add Mighty Ducks code reviewers to your review. 

Please note that any in-team reviews should be completed before adding the CI reviewers to the review. If a modification is being made to a KGB that another LITP team owns, that other team should +1 the review before CI are added.

How to Obsolete/Remove a Test Case
==================================

In some cases, new functionality can make existing test cases obsolete. This means that what the test case used to test is no longer part of system behavior or any part of the test. In another scenario, test cases may be merged to ensure more efficient testing in KGB and CDB, resulting in the need to obsolete/remove unused test cases.

Following agreement to obsolete the test case, the following steps should be followed in the test code:
    #. Change the name of the test from 'test_' to 'obsolete_'
    #. The test code should be removed from the testset file and replaced with 'pass'.
    #. Any @attr tags should be replaced with #attr.
    #. Any TMS statements should have the @ changed to #. Ex. Change @tms_id to #tms_id
    #. If there are no remaining test cases in the testset file, remove testset file.
    #. If it doesn't already exist, a README file should be added to the same directory in which the testset files are located in the repo.
    #. README file should be updated with the following information for each obsoleted/removed test case:
        - TEST: testset_storyxxxx.py test case.

        - DESCRIPTION: <simply copy existing description at time of obsoletion>

        - TMS-ID:

        - REASON OBSOLETED:

        - GERRIT REVIEW(to obsoleted test case(s)):
    #. Finally, log onto TMS(https://taftm.lmera.ericsson.se/#tm), search for the Test Case that is getting obsoleted and update its 'Description', keeping what is already there and adding 'Obsoleted <the reason why>'.


Specifying the order in which test cases are ran
================================================

The order in which test cases are ran can be specified with the file ordered_tcs.txt. If the test runner detects a file with the name "ordered_tcs.txt" in the directory where test cases live it will first(in no particular order) run any tests not specified in ordered_tcs.txt and then go on to run all test cases named in the file in the order in which they appear.
