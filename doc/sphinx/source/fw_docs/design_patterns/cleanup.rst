.. _cleanup-env-label:

Cleanup in the Automated Test Framework
=========================================

An important concept of automated testing is that at the end of every test the system must be reverted to the state it was at before the test began. This means that after every test we need to perform a level of 'cleanup' to revert the system back. How the framework handles cleanup is described below.


Cleanup of Items Created in the LITP Tree using CLI Create or Inherit Commands Run Directly on the Node
--------------------------------------------------------------------------------------------------------

The LITP inherit and create commands add items to the LITP tree. The below code in your test story will cleanup up these commands:


**Cleanup of CLI commands**

.. code-block:: python

    class Story236(GenericTest):

        def tearDown(self):
            """Runs for every test"""
            super(Story236, self).tearDown()

Essentially, the framework does all the work for you providing you call the parent teardown method within your own teardown. All test stories must call this teardown method.

A few notes:

- This cleanup works because the only allowed way to run commands on a node is with the Generic Test run_command or run_commands methods. When you call one of these methods, the framework makes a list of all successful create or inherit commands run, and then in the teardown() does a remove on all these paths.

- If there is a special use case where you need to handle cleanup in your own way, then you can set the **'add_to_cleanup' parameter** to False in your call to run_command, run_commands or the cli_execute methods. Then the commands will not be added to the list of commands to clean up.


**NOTE: There is currently no automated cleanup for the LITP XML load or import commands. You must perform cleanup manually.**


Cleanup of Plans
-------------------

This cleanup is run by the parent tearDown and works as is detailed here: :ref:`runplan-env-label`

Cleanup of Files Generated or Copied over to a Node
----------------------------------------------------

Currently, providing the add_to_cleanup flag has not been overridden to false, so any files created with the below methods will be automatically deleted at the end of the test:

- XML files generated with the export command
- Files copied to a node using the Generic Test copy_file_to method


This auto-deletion will work providing you call the parent tearDown as shown in the above example. If you have another use case where files are created on a node which need to be cleaned up, please speak to the framework authors so they can investigate updating the file autocleanup utilities.


Cleanup of New Users Created on a Node
---------------------------------------------

Providing a new user is created using the create_posix_usr command in Generic Test, the user will be automatically deleted at the end of the test (unless the del_usr flag is overidden to False). This auto-deletion will work providing you call the parent tearDown, as shown in the above example.


Cleanup of Items Created in the LITP Tree using the REST Interface
---------------------------------------------------------------------

The REST interface allows you to add items to the LITP tree. Use the below code to cleanup these items:

**Cleanup of Rest commands**

.. code-block:: python

    class Story296(GenericTest):
     
        def setUp(self):
            super(Story296, self).setUp()
            self.test_node = self.get_management_node_filename()
            self.ms_ip_address = self.get_node_att(self.test_node, 'ipv4')
            self.rest = RestUtils(self.ms_ip_address)
     
        def tearDown(self):
            self.rest.clean_paths()
            super(Story296, self).tearDown()

When testing with the REST interface, you will need to create an instance of the REST area class in your setup method. You can then call REST methods in your tests using this instance. (In the above example self.rest.METHOD_NAME)

To cleanup at the end of your test, you need to just make a call to the **clean_paths()** method of your REST instance. This will remove any items you have added to the LITP tree in your test.


Cleanup of Updates to Existing Items in the LITP Tree
-------------------------------------------------------

Cleanup of items that are updated during the test is done by using the backup_path_props util.

**Cleanup of updates on the LITP Tree**

.. code-block:: python

    @attr('all', 'example')
    def test_01_update(self):
     
                # 1. Get the os url
                os_url = self.find(self.test_node, "/software", "os-profile", True)[0]
     
                # 2. Backup the current value of all props on this profile
		self.backup_path_props(self.test_node, os_url)

                # 3. Update properties on path as required
                new_breed_prop = "breed='new_system236'"
                self.execute_cli_update_cmd(self.test_node, os_url, new_breed_prop)
                self.execute_cli_createplan_cmd(self.test_node)
     

The original property values of the os_url path is automatically restored by the parent tearDown.


Deleting Files After the Cleanup Plan has Run
-------------------------------------------------

In some use cases, there are specific files that need to be deleted after something has been removed from the model (i.e. after the automatic cleanup plan has run). This is because if they are removed before the cleanup plan has run, LITP will automatically restore them.

To cover this case, you should use the del_file_after_run method as shown below:

.. code-block:: python

    @attr('all', 'example')
    def test_01_del_file(self):
          ##This will add the file /tmp/file1.txt to a list which will be removed at the end of a test after any cleanup plan has run
          self.del_file_after_run(self.test_node, "/tmp/file1.txt")

          ##This will add the file /tmp/file2.txt to a list which will be removed at the end of a test after any cleanup plan has run
	  #In this case it will wait a puppet cycyle after the cleanup plan has run before deleting the file. 
          self.del_file_after_run(self.test_node, "/tmp/file1.txt", wait_for_puppet=True)

	  .
	  .
          .

Note the following:

- The cleanup will do no assertions for success for each deletion. This means that you can declare all the files you expect will need to be deleted at the very beginning of the test.

- If the test fails part way, it will attempt to delete all files you have listed.

- Some files may be restored by Puppet even after the test completes if LITP is in the middle of a Puppet cycle. If you know this is the case for the file you need to delete, you can set the wait_for_puppet flag to True. Note the cleanup logic is such that if you have 10 files which need to wait for Puppet before deleting, you should set the flag for all of them and when the cleanup has to wait just one cycle, it will delete all files. (Don't worry, it won't wait 10 puppet cycles!)



Other Cleanup Cases
----------------------

The basic rule always stands that if you change something you need to change it back using the principles outlined in the first paragraph. If you have a common cleanup use case which is not covered in the above sections, please speak to the test framework owners so that the prospect of adding extra cleanup utilities can be investigated.

In some rare cases, the system may not yet have the functionality to perform cleanup (e.g. cleanup is a later story). In these cases, discuss with the Continuous Integration team (currently the same people as the framework owners) and the tests will be run in a separate environment.
