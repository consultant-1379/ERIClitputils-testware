.. _runplan-env-label:

Running a LITP Plan in the Test Framework
============================================

Be Careful Of What You Run!
----------------------------

The LITP run_plan command causes the system to execute the current plan. A plan can be as simple as updating an item's property to as complex as deploying multiple managed nodes. In terms of integration story testing, a plan which attempts to install other nodes should never be run. Firstly, this is because this functionality is already tested in the nightly automated install jobs and, secondly, because attempting to re-install the nodes would break the continuous integration environment. 

Below, we describe methods provided by the framework to help you manage plans in a safe way. It is important to handle plans in a safe way because in some error cases a plan may not complete, so if your test is waiting for a plan to finish, your test may wait forever (infinite loop).


How to Run a Plan in the Framework
-------------------------------------------

In the below code, we run a plan and assert that it finishes successfully:

**Running a plan**

.. code-block:: python

   def setUp():
       self.cli = CLIUtils()

    @attr('all', 'example')
    def test_run_plan(self):
       .Somewhere here you would do your changes to the LITP tree and create_plan

       timeout_mins = 3
       #Perform the run_plan command
       self.execute_cli_runplan_cmd(self.test_node)
                                 
       #Wait for plan to complete with success
       completed_successfully = self.wait_for_plan_state(MS_NODE, test_constants.PLAN_COMPLETE, timeout_mins)
       self.assertTrue(completed_successfully, "Plan was not successful")

Note the following:

- We use the wait_for_plan_state method of Generic Test to wait for the plan to reach the specified state.

- This is a safe waiting method because an infinite loop is impossible if the plan state is unexpected as explained below:-

- If the plan reaches a state where it can no longer get to the state you are waiting for (e.g. you are waiting for PLAN_COMPLETE but the plan status becomes PLAN_FAILED), then the method will return with a value of False.

- If the plan is still running after reaching the timeout value, it will exit and return False. Timeout is 10 minutes by default or can be set by the parameter.

- The possible plan states are defined in the test_constants file.

- If you just need to get the current plan state rather than wait for a certain state to be reached you can use the method get_current_plan_state in Generic Test, which will return an integer corresponding to the plan state. These integers correspond to the values defined in the test_constants file.


Cleanup of Plans in the Automated Framework
--------------------------------------------------

In the test framework plans are automatically cleaned up using the below rules:

- If a plan is currently running when the test ends, the automatic cleanup will call the stop_plan command and wait until the plan has stopped.

- If a plan has been run in the test, then after all removes have been handled by cleanup (see :ref:`cleanup-env-label`), a create_plan and then a run_plan are executed.

- After run_plan has completed, remove_plan is called.


How to Check the Status of a Task in a Plan
-------------------------------------------

In some cases, rather than wait for the status of the whole plan, you may wish to perform some action after a particular task has reached a certain state. You can do this using the wait_for_task_state method as detailed below:


**Waiting for a task state**

.. code-block:: python

    @attr('all', 'example')
    def waiting_for_a_task_state(self):
        .
    	.
    	#Example 1
    	#In this example we wait for all tasks that match 'Generate Cobbler Kickstart file for host' to report success.
    	#If the task does not report success (ie the plan fails beforehand or the timeout is reached) the function returns False
    	#NB: By default the description ignores variables (text inside (" "))
    	self.execute_cli_runplan_cmd(MS_NODE)
 
    	task_descrip = 'Generate Cobbler Kickstart file for host "node1"'
    	task_success = self.wait_for_task_state(MS_NODE, task_descrip, test_constants.PLAN_TASKS_SUCCESS)
    	self.assertTrue(task_success, "Task: {0} was not successful".format(task_descrip))
 
    	self.execute_cli_stopplan_cmd(MS_NODE)
 
    	#Example 2
    	#In this example we wait for the task that match 'Generate Cobbler Kickstart file for host "node99"' to report success.
    	#If the task does not report success (ie the plan fails beforehand or the timeout is reached) the function returns False
    	self.execute_cli_runplan_cmd(MS_NODE)
 
 
    	task_descrip = 'Generate Cobbler Kickstart file for host "node99"'
    	task_success = self.wait_for_task_state(MS_NODE, task_descrip, test_constants.PLAN_TASKS_SUCCESS, ignore_variables=False, timeout_mins=5)
    	self.assertTrue(task_success, "Task: {0} was not successful".format(task_descrip))
 
 
    	self.execute_cli_stopplan_cmd(MS_NODE)


Note the following:

- By default, variables in the description are ignored (i.e. anything inside " ") as these are likely to be different depending on the system.

- Because variables are ignored, potentially multiple tasks will match the description. The method will only return True if all matched tasks reach a state of success.

- By overriding the ignore_variables parameter, you can force the test to look for an exact match including variables. This should only be done if the variable in the description has been generated by your test so it not liable to be different on different deployments.

- The method has an optional parameter timeout_mins, which defaults to 10 minutes. This can be overidden if required by the test.

