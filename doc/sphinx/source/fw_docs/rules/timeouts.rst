Overriding the Default Timeout Period for a Test
===================================================

By default, the test runner will stop a test if it runs for more than 30 minutes. In most cases, a test should never exceed this length. However, there may be some legitimate test cases where a test may take longer to complete, and in these cases you will need to override the automatic timeout value of Jenkins with a new value.


To do this, create a file named XX_TIMEOUT in the directory of your test file where XX is the filename of the file containing your tests. This file should contain only a number corresponding to the number of minutes that the timeout value should be set to.


So, for example, if I have a file called testset_story100.py which contains tests which you expect to take 40 minutes, you may want to set a timeout of 50 minutes. To do this, create a file called testset_story100.py_TIMEOUT in the same directory as your test file and inside that file just write the number 50 as shown below:

N.B.: Ensure TIMEOUT is uppercase.

**__TIMEOUT file for 50 min timeout**

.. code-block:: bash

   50
