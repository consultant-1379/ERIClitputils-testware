.. _logging-env-label:

Logging and Assertions in the Test Framework
================================================

Assertions in the Test Framework
-------------------------------------------------

When coding in the test framework, Python unit test assertion methods should always be used, as documented here: http://docs.python.org/2/library/unittest.html#assert-methods

Note that currently only the first four assertion methods are supported as test development is currently done using Python 2.6.

Below are some examples of these methods being used:

.. code-block:: python

    # Run grep command
    std_out, std_err, rcode = self.run_command(self.test_ms, grep_cmd)

    # assert out grep returns items to std_out
    self.assertNotEqual([], stdout)

    #Assert no errors reported in the error stream
    self.assertEqual([], std_err)

    #Assert that return code reports success
    self.assertEqual(0, rcode)

    self.assertTrue(self.is_text_in_list(exp_item, stdout),
                    "The text {0} does not appear in grep std_out".format(exp_item))


Note the following:

- All **assert equal commands** are in the order **'expected value, actual'**.

- Assert equal and assert not equal commands **should not have** messages, as the built-in error message is sufficient: it displays the values tested and whether they are equal.

- All assert true and assert false commands **must** have messages to help explain the meaning of the check and make it clearer as to why the assertions failed.


Logging in the Test Framework
--------------------------------------------------

The test framework automatically logs the following items (including time stamps for each):

- Which file and specific TC is currently being run.

- Each command that the test attempts to execute.

- The stdout, stderr and rc code returned from each executed command.

For example, when we execute the below method found in a file called testset_dummy.py:

.. code-block:: python

    @attr('all', 'example')
    def test_hostname_is_ms1(self):
        expected_hostname = "ms1"
        cmd_to_run = "hostname"
        stdout, stderr, returnc = self.run_command(self.test_node,
                                                  cmd_to_run)
        self.assertEqual(0, returnc)
        self.assertEqual([], stderr)
        self.assertTrue(self.is_text_in_list(expected_hostname, stdout),
                       "Actual hostname {0} does not match expected {1}" \
                              .format(stdout, expected_hostname))



we get the following output:

.. code-block:: bash

    root>nosetests --nocapture testset_dummy.py:Dummy.test_hostname_is_ms1
    2014-03-03 14:16:02,066 - litp.test - INFO - START testset_dummy.Dummy.test_hostname_is_ms1

    Current timestamp: 2014-03-03 14:16:02.066760
    [litp-admin@10.248.22.250]# hostname
    ms1
    0

    ###################################################
    2014-03-03 14:16:02,714 - litp.test - INFO - END OF TEST, START CLEANUP: testset_dummy.Dummy.test_hostname_is_ms1

    2014-03-03 14:16:02,714 - litp.test - INFO - END testset_dummy.Dummy.test_hostname_is_ms1
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.649s
    OK



Given that all the above items are logged automatically, then generally speaking it would be rare that we would need to add any extra logging or printouts to our tests. Providing we take care to write assertion messages which are easy to understand, all our tests should be quite clear without any additional logging. (Indeed, extra logging may act to confuse things.)

If you ever do have a case where you need to log something, it is recommended to use the Python logger functionality which allows you to set the log level as shown by the below examples:

.. code-block:: python

    def test_logging(self):
        self.log("info", "Hello world")
        self.log("warning", "Hello world")
        self.log("error", "Hello world")

This will output to the screen the following:

.. code-block:: bash

    >nosetests --nocapture testset_dummy.py:Dummy.test_logging
    2014-03-03 14:30:55,959 - litp.test - INFO - START testset_dummy.Dummy.test_logging

    2014-03-03 14:30:55,959 - litp.test - INFO - Hello world
    2014-03-03 14:30:55,959 - litp.test - WARNING - Hello world
    2014-03-03 14:30:55,959 - litp.test - ERROR - Hello world

    ###################################################
    2014-03-03 14:30:55,959 - litp.test - INFO - END OF TEST, START CLEANUP: testset_dummy.Dummy.test_logging

    2014-03-03 14:30:55,959 - litp.test - INFO - END testset_dummy.Dummy.test_logging
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.001s
    OK
