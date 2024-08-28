.. _runcmds-env-label:

How to Run Commands in the Automated Test Framework
=========================================================

The framework allows commands to be run on LITP nodes in a number of ways, as described below. In deciding which way to run a command, you should take into account which way is the most efficient and cleanest for your particular test case.

Use the execute_cli_XX Methods
----------------------------------

Generic Test provides several execute functions to run CLI commands. These functions perform some basic assertions of the returned values to ensure they return as expected in success or failure cases. Whether the assertions should check for failure or success depends on the value of the expect_positive parameter passed.


**Running CLI execute methods**

.. code-block:: python

    @attr('all', 'example')
    def run_cli_execute_methods(self):
        .
        .
     
        #Example 1 - Here we attempt to create an item with an invalid type. 
        #            The expect_positive flag has been set to False which means
        #            we perform basic assertions after running the command
        #            to check the command fails (ie check RC != 0, check std_err != [])
        #
        #            The tester only needs to process the result t cares about, in this case
        #            it loads std_err so it can assert it finds the expected error
         
        _, std_err, _ = self.execute_cli_create_cmd(self.test_node, url,
                                                    "invalid-type", expect_positive=False)
        # assert we get correct error message
        self.assertTrue(self.is_text_in_list("InvalidTypeError", std_err), "InvalidTypeError message missing")
     
        #Example 2 - Here we attempt a cli inherit command.
        #            The expect_positive flag is True so we perform basic assertions
        #            after running the command to assert success (ie check RC == 0, check
        #            std_err == [])
        #            The tester does not need to do any other assertions so we don't even need to collect return values
     
        self.execute_cli_inherit_cmd(self.test_node, node_os_url_path, infra_os_url_path, expect_positive=True)
     
        #Example 3 - Here we attempt a cli create_plan command. 
        #            Note the following:
        #            a) We want to assert the success case so we set expect_positive to True
        #            b) We want json output to be loaded automatically for us so we don't have to
        #               run json.load manually ourself. Therefore we set the load_json flag to True
        #            c) We want to run the command as a different user to that specified in the connection data files
        #               so we pass in user credentials to use when running the command
     
     
        stdout, _, _ = self.execute_cli_createplan_cmd(self.test_node, "-j", "dummy_user", "dummy_pw"
                                                       expect_positive=True, load_json=True)


Using the run_command Method
-------------------------------

The run_command method allows you to run a single command on the stated node and returns std_out, std_err and rc. An example of the command being run is below:

**Using run_command**

.. code-block:: python

    from litp_generic_test import GenericTest, attr
    from litp_cli_utils import RHCmdUtils
    import test_constants
    class Story100(GenericTest):
     
        def setUp(self):
            # 1. Call super class setup
            super(Story100, self).setUp()
     
            # 2. Set up variables used in the test
            self.test_node = self.get_management_node_filename()
            self.cli = CLIUtils()
     
        @attr('all', 'example')
        def test_01_p_test_show(self):
            .
            .
            .
            grep_cmd = RHCmdUtils().get_grep_file_cmd(
                test_constants.GEN_SYSTEM_LOG_PATH, "item",
                file_access_cmd="tail -n {0}".format(test_logs_len)
            )
            
            std_out, std_err, rcode = self.run_command(self.test_ms, grep_cmd)
     
            # assert our grep runs without error and returns some items
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, rcode)


Note the following:

- We do not need to handle any connection related code, we just call run_command and the framework handles the SSH connection for us using connection data defined in the data connection files.

- The first argument corresponds to the name of the connection data file which defines this node, this is set with the generic function get_management_node_filename.

- The second argument is a string corresponding to a command that we have generated using the Red Hat area class.


Using the run_commands Method
----------------------------------

The run_commands method allows you to run a list of commands potentially on a list of different nodes. It then returns a results dictionary which can be quickly parsed using helper functions to check things such as all commands returned without error etc. A common practice is to use the run_commands method to run a list of commands you need to setup your environment, assert they all run without error and then run your actual test command with run_command.

Below is an example of the run_commands method being used:

**Using run_commands**

.. code-block:: python

    @attr('all', 'example')
    def test_06_n_validate_plugin(self):
        """
        Description: See section on test case description
        """
        # 0. Fetch URL
        network_pro_url = self.get_network_pro_url()
     
        # 1. Create libvirt provider and network
        libvirt_url = network_pro_url + "/libvirt_provider_236"
        props = "name='libvirt_provider_236' " + \
                "management_network='test_236'"
     
        setup_cmds = list()
        setup_cmds.append(
            self.cli.get_create_cmd(libvirt_url,
                                    "network-profile", props))
     
        network_url = libvirt_url + "/networks/network0"
        props = "network_name=test_236 bridge=br09"
        setup_cmds.append(
            self.cli.get_create_cmd(network_url,
                                    "network", props))
     
        # 2. Get node deployment commands which link to libvirt provider
        create_node_cmds = \
            self.get_create_node_deploy_cmds(
                self.test_node, net_profile_name="libvirt_provider_236")
        setup_cmds.extend(create_node_cmds)
     
        # 3. Run all setup commands and assert success
        self.results = self.run_commands(self.test_node, setup_cmds)
        errors = self.get_stderr(self.results)
        self.assertEqual([], errors)
        # check stdout empty
        self.assertTrue(self.is_std_out_empty(self.results),
                        "Error std_out not empty")
     
        # 4. Create plan and assert failure
        create_plan_cmd = self.cli.get_create_plan_cmd()
        outlist, stderr, exit_code = \
            self.run_command(self.test_node, create_plan_cmd)
        self.assertNotEqual(0, exit_code)
        self.assertEqual([], outlist)
     
        # 5. Check ValidationError present in std_err
        self.assertTrue(
            self.is_text_in_list("ValidationError", stderr),
            "ValidationError message is missing")


Note the following:

- We have a list, setup_cmds, which we are adding commands to which we wish to run.

- The commands are only run when we call the run_commands method and pass it the list of commands we have created.

- We run the command on just one node (self.test_node which is set to 'ms1' elsewhere). However, we can pass a list of nodes and all the commands will be run on every node in the list.

- The method returns a dictionary storing all the returned values from each command run. We can use helper functions to process this dictionary. For example self.get_stderr returns a list of all error messages in the dictionary - the list will be empty if no errors were reported.
