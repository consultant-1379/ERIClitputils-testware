Using Nosetests to Run Tests
======================================

As a test case is developed, it is important that they can be run in a test environment.

How to set up this environment can be found in `RunningTestCasesintheCloud <https://confluence-nam.lmera.ericsson.se/pages/viewpage.action?spaceKey=ELITP&title=Continuous+Integration+Test+Framework#ContinuousIntegrationTestFramework-RunningTestCasesintheCloud>`_

How can the tests be run on the environment? Use **nosetests** and some examples below show how:

.. code-block:: bash

    # Run all tests in a file and return how many tests failed or passed.
    > nosetests testset_story100.py
 
    # Run all tests in a file and print out all logging messages to screen.
    > nosetests -s testset_story100.py
 
    # Run one test from a file and print out all logging messages to screen.
    > nosetests -s testset_story100.py --testmatch="test_01_n_test_boolean"
    > nosetests -s testset_story100.py --testmatch=test_01_n_test_boolean


Note:

- The tests are run against the nodes defined in the connection data files as noted in :ref:`test-env-setup-label`.
