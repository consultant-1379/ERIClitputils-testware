How to Run Interactive Commands in the Automated Test Framework
================================================================

There are a number of cases where a command may respond with a prompt or number of prompts before it executes. Lets take the simple use case of changing a user password and look at how we handle these prompts when creaing tests in the automated test framework.

The Manual Steps
--------------------

Firstly, let's run the command manually and see what prompts we get and how we should respond. In our example, we are going to change our password from litp_admin to litp_admin_newpw


**Cleanup of Rest commands**

.. code-block:: bash

   [litp-admin@10.248.22.250]# passwd
   Changing password for user litp-admin.
   Changing password for litp-admin.
   (current) UNIX password: litp_admin
   New password: litp_admin_newpw
   Retype new password: litp_admin_newpw
   passwd: all authentication tokens updated successfully.

In the above example, we are given three prompts and we respond as shown below:

.. Again the document generates fine, no idea why rest of code is purple as if part of table code

+--------------------------+--------------------+
|Prompt                    |  Response          |
+==========================+====================+
|(current) UNIX password:  |  litp_admin        |
+--------------------------+--------------------+
|New password:             |  litp_admin_newpw  |
+--------------------------+--------------------+
|Retype new password:      |  litp_admin_newpw  |
+--------------------------+--------------------+


How to Automate the Manual Steps in the Framework
---------------------------------------------------

As you can see in the above example, to automate these kinds of commands we need to be able to store what prompts we would expect and what should be the response to each prompt. We then need to pass these 'prompt-response' pairs to a run_command like method. How we handle this in the framework is shown in the example below:

**Automating interactive commands**

.. code-block:: python

    @attr('all', 'example')
    def test1_change_user_pw(self):
          cmd_to_run = "passwd"
          #We make a list of prompt-response dictionaries created using the get_expects_dict method in Generic Test
          expects_cmds = list()
          expects_cmds.append(self.get_expects_dict("(current) UNIX password:",
                                                    "litp_admin"))
          expects_cmds.append(self.get_expects_dict("New password:",
                                                    "litp_admin_newpw"))
          expects_cmds.append(self.get_expects_dict("Retype new password:",
                                                    "litp_admin_newpw"))
     
          #We now pass out expects dictionary list to the run_expects_command method in Generic Test
          stdout, stderr, rc = self.run_expects_command(self.test_node,
                                                        cmd_to_run,
                                                        expects_cmds)


An important point is that by design the list is order specific. So for example, if the first prompt received back from the command does not equal the first prompt in your list, the command will fail. So for example, the below test will fail because the list has been created in the wrong order:

**Error case - expects in wrong order**

.. code-block:: python

    @attr('all', 'example')
    def test1_change_user_pw(self):
          cmd_to_run = "passwd"
          #We make a list of prompt-response dictionaries created using the get_expects_dict method in Generic Test
          expects_cmds = list()
          expects_cmds.append(self.get_expects_dict("(current) UNIX password:",
                                                    "litp_admin"))
          expects_cmds.append(self.get_expects_dict("Retype new password:",
                                                    "litp_admin_newpw"))
          expects_cmds.append(self.get_expects_dict("New password:",
                                                    "litp_admin_newpw"))
     
          #We now pass out expects dictionary list to the run_expects_command method in Generic Test
          stdout, stderr, rc = self.run_expects_command(self.test_node,
                                                        cmd_to_run,
                                                        expects_cmds)
