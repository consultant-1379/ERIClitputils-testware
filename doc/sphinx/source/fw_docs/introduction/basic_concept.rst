Basic Concept
================

The idea behind this Automated Test Framework is to be able to write a set of test cases with ease using a set of common method utilities that already exist within the framework. Most of these utilites are written specific to testing LITP 2.1. The tester writing the test case will have a list of commands that will be used in the test case and have expected outputs that will be compared with actual results. Writing a test case should be a simple process, with all tools and examples provided by the core framework documentation and code base.

**Layout of a Test Case**

The setup of a test case in all cases will have the following pattern:

- Loading of node connection data from connection data files and setting any global parameters.

- Connecting to a node, running a command and disconnecting from a node.

- Cleanup of any changes done on the node during the test.


Most of the above steps are done automatically by the framework so that the tester does not have to do any handling or creating of connections, instead just using the run_command like methods to execute the commands they need for their test. Cleanup of any items created in the LITP tree is also handled automatically by the framework.

When writing the test body of the test case code, a typical pattern will be:


- Construct the command to be run - Given by a utility or a once-off command only specific to the test case.

- Run the command on a node(s).

- Assert the returned outputs and return codes are as expected.

- If needed - Parse the output for specific paramaters - in test code or a given utility.


With this structure, and all the utilities in place, the tester can write the test case with ease.
In the case of CLI commands, some helper execute methods have been added which automatically run the command and perform the assertions for you. (See section :ref:`runcmds-env-label`.)

