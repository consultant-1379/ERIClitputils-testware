Using the Area Classes in your Tests
========================================

A key principle to the test framework is that the only methods which actually execute commands on LITP nodes are the methods in GenericTest. The main purpose of the area classes is to provide command strings to your test story so that your test story can perform the command by calling the Generic Test run_command or run_commands methods.

See from the below example how we can use methods from area classes to support our test. Take special note of what happens on the following lines:

- **Line 16:** Here we initialise the CLI area class in our setup. It is initialised here as it will be used for many test cases.
- **Line 40:** Here we use methods in the CLI area class. Note that the methods just return a string value which we then run using the run_command method.
- **Line 11/36/42:** Here we use methods declared in GenericTest using the self keyword which execute commands for us.

**Using the area classes to construct commands**

.. code-block:: python

    from litp_generic_test import GenericTest, attr
    from litp_cli_utils import CLIUtils
     
    class Story242(GenericTest):
        """As a LITP user I want to authenticate for access
           to the REST API (locally stored username/password)"""
     
        def setUp(self):
            super(Story242, self).setUp()
            self.cli = CLIUtils()
            self.test_ms = self.get_management_node_filename()
     
        def tearDown(self):
            super(Story242, self).tearDown()
     
        @attr('all', 'example')
        def test_01_p_authenticate_cli_args(self):
            """
            Description: See section on test case description
            """
            #1. Create a new user
     
            uname = "litp_{0}".format(self.__class__.__name__)
            pword = "litpc0b6lEr"
            self.assertTrue(self.create_posix_usr(self.test_ms, uname, pword), "Failed to create user")
     
            # 2. run LITP show passing username and password as
            # CLI args
            show_cmd = self.cli.add_creds_to_litp_cmd(self.cli.get_show_cmd("/"), uname, pword)
     
            std_out, std_err, rcode = self.run_command(
                self.test_ms, show_cmd, username=uname, password=pword
            )
     
            # 3. assert command ran successfully
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, rcode)
