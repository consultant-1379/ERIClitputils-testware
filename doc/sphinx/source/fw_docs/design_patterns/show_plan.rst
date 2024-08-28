.. _showplan-env-label:

Parsing Information from show_plan Output
==========================================

Any changes to the LITP model which affect an item in the deployment will cause a plan to be generated after the create_plan command. There are often cases where a tester may want to parse and view information in the plan which can be done using the utils described in this section.
 
See an example of the utility methods in the CLI utils being used below:

.. code-block:: python

    #Get show_plan output
    stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)

    #Get number of phases in total
    number_of_phases = self.cli.get_num_phases_in_plan(stdout)
    #Get number of tasks in total for phase 1
    number_of_tasks_phase1 = self.cli.get_num_tasks_in_phase(stdout, 1)

    #Parse plan into dict
    plan_dict = self.cli.parse_plan_output(stdout)

    #Query the dict for different tasks
    status_task_phase1_task1 = plan_dict[1][1]["STATUS"]
    desc_task_phase1_task1 = plan_dict[1][1]["DESC"]
    status_task_phase1_task2 = plan_dict[1][2]["STATUS"]
    desc_task_phase1_task2 = plan_dict[1][2]["DESC"]

    #Print out all information
    print "Number of phases:", number_of_phases
    print "Number of tasks 1st phase:", number_of_tasks_phase1
    print "Phase 1 Task 1 status:", status_task_phase1_task1
    print "Phase 1 Task 1 desc:", desc_task_phase1_task1
    print "Phase 1 Task 1 status:", status_task_phase1_task1
    print "Phase 1 Task 2 desc:", desc_task_phase1_task2
    print "Phase 1 Task 2 status:", status_task_phase1_task2

When run, the above code would print out the following to the display:

.. code-block:: bash

   [litp-admin@10.44.86.45]# /usr/bin/litp show_plan
   Phase 1
   Task status
   -----------
   Initial     /ms
   Update node "node1" host file with "node1" entry
   Initial     /ms
   Configure interface "eth1" on node "node1"
   Initial     /ms
   Update node "node2" host file with "node1" entry
   Initial     /ms
   Update node "ms1" host file with "node1" entry
   Tasks: 4 | Initial: 4 | Running: 0 | Success: 0 | Failed: 0 | Stopped: 0
   A snapshot of the deployment was completed on Wed May 28 02:57:50 2014
   Plan Status: Initial
   0
   Number of phases: 1
   Number of tasks 1st phase: 4
   Phase 1 Task 1 status: Initial
   Phase 1 Task 1 desc: ['/ms', 'Update node "node1" host file with "node1" entry']
   Phase 1 Task 1 status: Initial
   Phase 1 Task 2 desc: ['/ms', 'Configure interface "eth1" on node "node1"']
   Phase 1 Task 2 status: Initial
