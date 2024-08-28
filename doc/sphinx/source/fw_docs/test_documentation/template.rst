.. _doc_template-label:

Test Case Documentation Standard
==========================================

LITP is part of the wider ENM community. As part of the ENM Test Strategy, all test cases in the ENM product must be traceable to their requirements, 
including LITP test cases. LITP has a separate test framework to that used in other ENM teams, however it must produce the same reporting mechanism as those in other ENM teams.
The tools used for the test reports is Allure and the TMS (Test Management System) is used to trace test cases back to requirements in JIRA. In order to produce the Allure report and to be able to add test cases to TMS automatically, the following description template MUST be adhered to.

.. code-block:: python

    def test_xx_example_test(self):
    """
        @tms_id: litpcds_xxxx_tcxx / torf_xxxx_tcxx
        @tms_requirements_id: LITPCDS-xxxx
        @tms_title: <Title for the test case>
        @tms_description: <1 - 2 line description of test case>
        @tms_test_steps:
         @step: <Test Step description>
         @result: <Expected result>
         @step: <Test Step description>
         @result: <Expected result>
         @step: <Test Step description>
         @result: <Expected result>
         @result: <Expected result> -> Can have multiple expected results of a step
         @step: <Test Step description>
         @result: <Expected result>
         @step: <Test Step description>
         @result: <Expected result>
         @step: <Test Step description>
         @result: <Expected result>
        @tms_test_precondition: <NA or give any preconditions if any>
        @tms_execution_type: Automated
    """
    ...

An alternative supported structure is as follows:

.. code-block:: python

    def test_xx_example_test(self):
    """
        @tms_id: 
            litpcds_xxxx_tcxx
        
        @tms_requirements_id: LITPCDS-xxxx,LITPCDS-xxxx,TORF-xxxxx,
                LITPCDS-yyyy,TORF-yyyyy

        @tms_title: 
            <Title for the test case>
        @tms_description: 
            <1 - 2 line description of test case>
        @tms_test_steps:
         @step:
            <Test Step description>
         @result: 
            <Expected result>
         @step: 
            <Test Step description>
         @result: 
            <Expected result>
         @step: 
            <Test Step description>
         @result: 
            <Expected result>
         @result: 
            <Expected result> -> Can have multiple expected results of a step
         @step: 
            <Test Step description>
         @result: 
            <Expected result>
         @step: 
            <Test Step description>
         @result: 
            <Expected result>
         @step: 
            <Test Step description>
         @result: 
            <Expected result>
        @tms_test_precondition: 
            <NA or give any preconditions if any>
        @tms_execution_type: Automated
    """
    ...

Please note the following details:

	1. The @tms_id above must be unique for every test case in LITP and should following the below format:
	 
	   <JIRA TYPE>_<JIRA ID>_<TEST CASE NUMBER>

	   where:
	     JIRA TYPE is litpcds or torf depending on what is in JIRA.

	     JIRA ID is the number attached to the JIRA item. So for example a story torf-123 would have an id of **123**

	     TEST CASE NUMBER is the number of the test case preceeded by 'tc'. So for example the first test case in a file testing story torf-123 
	     would have **tc01**

	  Example id: **torf_123_tc01**

          This format means that no test case will have the same id. The id should all be lower case.

	2. The @tms_requirements_id should a comma-seperated list of JIRA references. 
	   NOTE: The JIRA references should match JIRA so **TORF-1234** is correct but torf-1234 (lower case) or TORF_1234 (using _ not -) are not correct. This should be linked to stories **only**.
	   This can't be an improvement, task, bug - it always has to be type **Story**!
	   Where a test case is added for a bug, add the story reference for which the bug is related. (see more details below)

	3. The @tms_title should be a high level description of the area being tested.

	   So for example if your test case is in the area of bonding a title might be **Test creation of a bond**. The same title may be used for several TCs.

	4. The @tms_description should give a summary of what the specific test case is testing

	   So for example a description might be something like **Tests a validation error is given on attempting to assign an ip to a interface being used by a bond**

	5. The @tms_test_steps should contain @step/@result substeps which explain what the test does.

	6. The @tms_test_precondition should contain any required precondition for the test. If the test can be run on the standard two node cluster and is not dependent on other tests being run first this should be set to NA. 

        7. The @tms_execution_type should be set to Automated if the test is scripted. If it is a manual test with just a method stub describing steps to perform the type should be set to Manual.  

   
It is important that the order of the tags above are preservered. The pre_code_review jobs for test code will check that the description matches the template above, if it is incorrect then it will fail.
The format will also be checked in CI code reviews, paying particular attention to the standard of information given in the test steps and expected result of that step. Anyone should be able to read the test description

For the sake of clarity when debugging tests it is advised that the TMS steps be added as logs within your test code before the point the code is executed.

NOTE: Currently TMS don't support adding bugs as a requirement ID, in this case you should add the story that the bug is related to as an ID or if there is no story (should be rare) then find the EPIC that it is related to and add that as the ID. In the description add the bug ID into the description field an example as follows:

.. code-block:: python

    @attr('all', 'revert', 'story295', '295_02')
    def test_02_p_kickstart_snippets(self):
        """
        @tms_id: litpcds_295_tc02
        @tms_requirements_id: LITPCDS-295
        @tms_title: kickstart snippet generation
        @tms_description:
            Verify that the kickstart snippet files have been created for the
            nodes in the cluster
            NOTE: also verifies LITPCDS-13441
        @tms_test_steps:
            @step: Verify that the kickstart snippet files exists on the nodes
            @result: The kickstart files exist
            @step: Compare the mount point of the volume with the one in the
            kickstart for every node
            @result: mount points match
            @step: Compare the size of the volume with the one in the
            kickstart for every node
            @result: sizes match
            @step: Verify that the kickstart files have the permission 644 set
            in the ms
            @result: kickstart permissions are 644
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', 'Verify that the kickstart snippet files exists on the nodes')
	#code here whichs performs above step
	.
	.
	self.log('info', 'Compare the mount point of the volume with the one in the kickstart for every node')
	#code here whichs performs above step
	.
	.
	self.log('info', 'Compare the size of the volume with the one in the kickstart for every node')
	#code here whichs performs above step
	.
	.
	self.log('info', 'Verify that the kickstart files have the permission 644 set in the ms')
	#code here whichs performs above step
	.
	.	
    ...



 
