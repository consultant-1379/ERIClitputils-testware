How to Run Commands as Different Users
==========================================

What is the Default User?
------------------------------

The test framework reads the default username and password to use in running all commands from the connection data files. Each node in the test must have one of these files which contains key data such as host name, IP address and login credentials. The current default user for tests is litp-admin which is a standard (non-root) user.

There are some use cases where you will need to run commands as other users (most commonly the root user) and the steps to do this in the framework are described below.

**Please note that commands should only be run as root if there is a valid usecase, wherever possible the default user should be used.**

To run commands as root using su (this is the only way to run as root on peer nodes)
---------------------------------------------------------------------------------------

.. _LITPCDS-558: http://jira-nam.lmera.ericsson.se/browse/LITPCDS-558

As stated in LITPCDS-558_, connecting to peer nodes directly as root is not allowed. Therefore, in order to run commands as root on peer nodes, we need to connect as a normal user (such as litp-admin) and then su to root and execute the command. This functionality is provided with a flag 'su_root' on the run_command, run_commands and run_expect_commands methods and can be used as shown below:


**Using su_root**

.. code-block:: python

    @attr('all', 'example')
    def test_01_run_as_su(self):
        #First we get all available peer node to run our test on
        peer_nodes = self.get_managed_node_filenames()
     
        #Now we can run our commands using either run_command or run_commands methods
        cmd_to_run1 = 'ls /root'
        cmd_to_run2 = 'ls /etc'
     
        #This will run this single command as root on all peer nodes by looping through the node list
        for node in peer_nodes:
            stdout, stderr, returnc = self.run_command(node, cmd_to_run1, su_root=True)
     
        #This will run a list of commands on a list of nodes as root
        cmd_list = list()
        cmd_list.append(cmd_to_run1)
        cmd_list.append(cmd_to_run2)
     
        #Note we are passing a list of nodes and a list of commands to run on each of the nodes
        results = self.run_commands(peer_nodes, cmd_list, su_root=True)


**NOTE:** By default, when a root command is run it will exit with a -1 error code if the task has not been completed within 15 seconds. To override this timeout you can supply a timeout to run_command or run_commands by passing the  timeout value in su_timeout_secs parameter as shown in the example below:

**Passing a timeout value for su_root**

.. code-block:: python

    def test_01_install_something(self):
    .
    .
    #In the below example we have a cmd we need to run as root which we expect will take up to 2 minutes to return.
    #Therefore we override the su timeout as shown below.
    new_timeout=120
    stdout, stderr, rc = self.run_command(self.test_node, cmd_to_run, su_root=True, su_timeout_secs=new_timeout)

**Important Note**

Due to firewall issues, connection to peer nodes on singleblade or multiblade servers hosted in Athlone may report permission errors. You will need to run your tests on local VMs or upload your test file to Jenkins (which is also hosted in Athlone) to successfully run it.


To Run Commands by Connecting to a Node using Different User Credentials than those stated in Connection Data Files
--------------------------------------------------------------------------------------------------------------------

The run command related methods in Generic Test allows us to connect to a node using different user credentials than those stated in the connection data files. This method is shown below:

**Connecting to a node with different user credentials**

.. code-block:: python

    @attr('all', 'example')
    def test_01_run_as_su(self):
        #First we get an available peer node to run our test on
        ms_node = self.get_management_node_filename()
     
        #Now we can run our commands using either run_command or run_commands methods
        cmd_to_run1 = 'ls /home/dummy_user'
        cmd_to_run2 = 'ls /home/dummy_user/dir1'
      
        #This will run this single command as the user 'dummy_user' using the password 'dummy_pw"
        stdout, stderr, returnc = self.run_command(ms_node, cmd_to_run1, "dummy_user", "dummy_pw")
      
        #This will run a list of commands all as root
        cmd_list = list()
        cmd_list.append(cmd_to_run1)
        cmd_list.append(cmd_to_run2)
      
        results = self.run_commands(ms_node, cmd_list, "dummy_user", "dummy_pw")
