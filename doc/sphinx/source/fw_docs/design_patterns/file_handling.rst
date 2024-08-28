File Handling in the Test Framework
=====================================

There are a number of circumstances where we need to perform file actions such as checking logs for certain messages, or comparing a file LITP generates with expected output. How to perform these actions in the framework is detailed below.


Checking a File for Specific Text
---------------------------------

In the first use case shown below, we want to check that after running certain test steps, we get the expected logs in /var/log/messages.

**Checking a file for expected messages**

.. code-block:: python

    @attr('all', 'example')
    def test_logs_example(self):
            #All potential files we check on nodes should have their path in the constants file
            log_path = test_constants.GEN_SYSTEM_LOG_PATH
     
            #We are going to search the logs for these items
            msg_to_check = list()
            msg_to_check.append("INFO: Created Item")
            msg_to_check.append("INFO: Plan created")
     
            #Find the current log position so we can ignore all log messages before our test
            start_log_pos = self.get_file_len(self.test_node, log_path)
     
            #Other test steps which create an item and a plan
            #..
            #..
             
            #See if expected logs are found in /var/log/messages between the log length at the start of the test and now +10 secs
	    log_found = self.wait_for_log_msg(self.test_node, msg_to_check, timeout_sec=10, log_len=start_log_pos)
		 
            self.assertTrue(log_found, "Expected log not found")
            

We can note the following from the above example:

- The path to the log is saved in a constants file. Any files that are used in tests should have their paths included in the constant file and not hardcoded in the test.

- We check the length of the log file at the start and end of the test using the get_file_len utility. This can then be used to tail the log file so we are only checking for logs that were generated during the running of our test to avoid false positives/false negatives.

- The wait_for_log_msg utility can take as argument a single string or a list of messages to check for. It will only return true if all logs are present

- The wait_for_log_msg utility by default looks in /var/log/messages. However to check other files you can pass in the log_file/rotated_log arguments

- The wait_for_log_msg utility will automatically handle log rotatation that may occur while waiting for a log to appear (in this case it checks the last part of the rotated log and the new logfile from
  start at each loop)

- You should supply a reasonable timeout value depending on how long it will take for the msg to be present in the logs

- The utilities above can be used for checking the negative case, that a specific log does not appear in the logfile, in this case you just assert that the log_found variable is False.


Copying a Test File or Files to a Node
---------------------------------------

During testing a common use case may be to copy specific files to a node (for example, rpm packages to test plugin installs) to support our tests. We can do this using the copy_file_to (single file) or copy_filelist_to (list of files) methods of Generic Test as shown below.

**Copying Single Test File**

.. code-block:: python

    @attr('all', 'example')
    def test_01_copy_single_file(self):
        #Assuming the file we intend to copy is in the same directory as our test file
        #we can reliable get the current file location using the below command
        local_filepath = os.path.dirname(__file__)
     
        local_file1_full_path = self.join_paths(local_filepath, "testfile1.txt")
     
        remote_path1 = "/tmp"
        remote_path2 = "/root/testfile1_newname.txt"
     
        #In this first example we copy to a directory so the filename will be the same as the local filename
        copy_success = self.copy_file_to(self.test_node, local_file1_full_path, remote_path1)
        self.assertTrue(copy_success, "File copy failed")
     
        #In this second example the remote path contains the full path with filename so we copy and rename to the filename stated in the remote path.
        #Note we also pass in the su_root flag as we are copying to a remote directory which requires root privledges
        copy_success = self.copy_file_to(self.test_node, local_file1_full_path, remote_path2, root_copy=True) 
        self.assertTrue(copy_success, "File copy failed")

Note the following:

- As stated in :ref:`cleanup-env-label`, all files copied will automatically be deleted at the end of a test. If you need to do this cleanup manually for some reason, pass in the add_to_cleanup flag as False.

- The copy_file_to command returns a boolean which is True if the copy is successful or False otherwise.

**Coping Multiple Test Files**

.. code-block:: python

    @attr('all', 'example')
    def test_02_copy_multiply_files(self):
        local_filepath = os.path.dirname(__file__)
     
        local_file1_full_path = self.join_paths(local_filepath, "testfile1.txt")
     
        remote_path1 = "/tmp"
        remote_path2 = "/tmp/testfile1_newname.txt"
     
        filelist = list()
        filelist.append(self.get_filelist_dict(local_file1_full_path, remote_path1))
        filelist.append(self.get_filelist_dict(local_file1_full_path, remote_path2))
     
        all_successful = self.copy_filelist_to(self.test_node, filelist)

Note the following:

- The copy_filelist_to command also takes arguments of root_copy and add_to_cleanup which will be applied to all copy operations in the list.

- The copy_filelist_to method returns True if all files are copied successfully or False if one file or more fails to copy.


Finding out if a Path Exists
-------------------------------

Find out if a remote path exists as shown below:

**Find out if a Path Exists**

.. code-block:: python

    @attr('all', 'example')
    def test_01_path_exists(self):
     
        #Here we want to test for the existance of a file
        path_to_check_1 = "/tmp/testfile1.txt"
     
        #The method returns a boolean, True if exists or False otherwise
        file_exists = self.remote_path_exists(self.test_node, path_to_check_1)
     
        #Here we want to test the the existence of a directory
        path_to_check_2 = "/tmp"
     
        #We need to set the expect_file flag to False if we are testing for the existance of a directory
        #The method returns a boolean, True if exists or False otherwise
        dir_exists = self.remote_path_exists(self.test_node, path_to_check_1, expect_file=False)


Deleting a File or Directory
------------------------------------

Note that in many cases cleanup of files is handled automatically as detailed here: :ref:`cleanup-env-label`. However, for the cases where you do need to delete a file, follow the steps below:

**Deleting an item**

.. code-block:: python

    @attr('all', 'example')
    def test_01_delete_item(self):
     
        file_to_del_1 = "/tmp/my_file.txt"
        file_to_del_2 = "/root/my_file.txt"
        dir_to_del = "/tmp/my_dir"
     
        #Here we delete a file
        delete_success = self.remove_item(self.test_node, file_to_del_1)
     
        #Here we delete a file with root permissions
        delete_success = self.remove_item(self.test_node, file_to_del_2, su_root=True)
     
        #Here we delete a directory
        delete_success = self.remove_item(self.test_node, dir_to_del)


Note the following:

- The same method is used to delete both files or directories.

- If you know the file has root permissions, you can pass the su_root flag as True. (Take great care with this option!)

- The method returns a boolean, True if delete was successful or False otherwise.


Moving a File
--------------------------

To move a file on a node follow the below steps:

**Moving a file**

.. code-block:: python

    @attr('all', 'example')
    def test_01_moving_file(self):
        file_orig_path = "/tmp/file1.txt"
        file_new_path = "/tmp/file2.txt"
        file_new_root_path = "/root"
     
        #Returns a boolean on whether the mv was successful
        mv_success = self.mv_file_on_node(self.test_node, file_orig_path, file_new_path)
     
        #Here we need to provide the su_root option as we are moving to a root protected path
        mv_success = self.mv_file_on_node(self.test_node, file_new_path, file_new_root_path, su_root=True)

**NB: The advantage to using the frameworks built-in mv command is that any files that are listed as requiring cleanup will have their paths updated so cleanup will delete the file at its new location.**


Creating a Directory on the Node
-------------------------------------

To create a directory on the node:

**Creating a directory on a node**

.. code-block:: python

    @attr('all', 'example')
    def test_01_create_dir(test):
       dir_to_create = "/tmp/my_new_dir"

       #Returns True if the creation was successful
       create_success = self.create_dir_on_node(self.test_node, dir_to_create)

A few things to note:

- As in other examples, you can pass a su_root flag set as True to create the directory with root privledges.

- Any directory created will be added to the list of items to delete at the end of the test unless the add_to_cleanup flag has been passed in as False.


Listing the Contents of a Directory
----------------------------------------

List a directory as shown below:

**Listing a directory**

.. code-block:: python

    @attr('all', 'example')
    def test_01_list_dir(test):
    
         #This lists the temp directory returning a list to dir_contents
         dir_to_list = "/tmp"
         dir_contents = self.list_dir_contents(self.test_node, dir_to_list)
                 
         #List a directory with root privileges
         dir_to_list = "/root"
         dir_contents = self.list_dir_contents(self.test_node, dir_to_list, su_root=True)


Getting the Length of a File
-------------------------------

Get the length of a file as shown below:

**Get length of a file**

.. code-block:: python

    @attr('all', 'example')
    def test_01_get_file_len(test):
       #This returns the file length of /var/log/messages using the defined test 
       #constant for the filepath
       file_len = self.get_file_len(self.test_node, test_constants.GEN_SYSTEM_LOG_PATH)

**NB: Any filepath not created by the user during the test should be in the test_constants file.**


Getting a Files Contents
--------------------------

Get the contents of a file as shown below:

**Get the contents of a file**

.. code-block:: python

    @attr('all', 'example')
    def test_01_get_file_len(test):
        #This returns a list corresponding to the contents of a file
        file_contents = self.get_file_contents(self.test_node, test_constants.GEN_SYSTEM_LOG_PATH)
                 
        #This is hardcoded for an example. See example 1 above to see a more sensible usuage
        tail_log_by = 10
                                 
        #This returns a list corresponding to the contents of a file tailed by the 3rd parameter
        file_contents = self.get_file_contents(self.test_node, test_constants.GEN_SYSTEM_LOG_PATH, tail_log_by)

Things to note:

- A su_root flag can be passed if the file in question requires root privileges to read.

- See example 1 above for a practical usage of this.

Backing up a File
--------------------------

An important principle of test is that any changes made to files are reverted at the end of a test, regardless of whether the test passes or fails. This is why the framework provides the backup_file util.
This util copies or moves the selected file on the selected node to a backup location and then restores it automatically when the test completes. See examples below:

**Backing up a file**

.. code-block:: python

    @attr('all', 'example')
    def test_01_backupfile():
     	#Example 1
     	#This will copy the /etc/hosts file to /tmp and then restore it at the end of the test
     	self.backup_file(self.test_node, test_constants.ETC_HOSTS)
 
     	#Example 2
     	#This will move the /etc/hosts file to /tmp and then restore it at the end of the test
     	self.backup_file(self.test_node, test_constants.ETC_HOSTS, backup_mode_cp=False)
 
 
     	#Example 3
     	#This will copy the file to the folder /mydir. If this file doesn't exist the test will automatically fail.
     	self.backup_file(self.test_node, test_constants.ETC_HOSTS, backup_path="/mydir")

  
Things to note:

- If the backup operation fails the test will automatically fail.

