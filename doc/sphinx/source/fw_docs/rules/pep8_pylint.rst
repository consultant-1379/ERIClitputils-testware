Running Pylint and pep8
=========================

Pylint and pep8 should be installed and configured as stated in the section :ref:`test-env-setup-label`

**All testscripts should be scoring 10/10 in Pylint and reporting zero pep8 errors.**

These tools can be run as shown below:


**Running Pylint**

.. code-block:: bash

    david.appleton@27G9KY1>pylint --rcfile=~/git/ERIClitputils-testware/src/main/resources/scripts/pylint/pylintrc_test_2_1 testset_story236.py
     
    Report
    ======
    183 statements analysed.
    Messages by category
    --------------------
    +-----------+-------+---------+-----------+
    |type       |number |previous |difference |
    +===========+=======+=========+===========+
    |convention |0      |0        |=          |
    +-----------+-------+---------+-----------+
    |refactor   |0      |0        |=          |
    +-----------+-------+---------+-----------+
    |warning    |0      |0        |=          |
    +-----------+-------+---------+-----------+
    |error      |0      |0        |=          |
    +-----------+-------+---------+-----------+
    Global evaluation
    -----------------
    Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
    Statistics by type
    ------------------
    +---------+-------+-----------+-----------+------------+---------+
    |type     |number |old number |difference |%documented |%badname |
    +=========+=======+===========+===========+============+=========+
    |module   |1      |1          |=          |100.00      |0.00     |
    +---------+-------+-----------+-----------+------------+---------+
    |class    |1      |1          |=          |100.00      |0.00     |
    +---------+-------+-----------+-----------+------------+---------+
    |method   |14     |14         |=          |100.00      |0.00     |
    +---------+-------+-----------+-----------+------------+---------+
    |function |0      |0          |=          |0           |0        |
    +---------+-------+-----------+-----------+------------+---------+
    External dependencies
    ---------------------
    ::
        litp_cli_utils
          \-CLIUtils (testset_story236)
        litp_generic_test
          \-GenericTest (testset_story236)
        redhat_cmd_utils
          \-RHCmdUtils (testset_story236)
        test_constants (testset_story236)
    Raw metrics
    -----------
    +----------+-------+------+---------+-----------+
    |type      |number |%     |previous |difference |
    +==========+=======+======+=========+===========+
    |code      |236    |42.14 |236      |=          |
    +----------+-------+------+---------+-----------+
    |docstring |216    |38.57 |216      |=          |
    +----------+-------+------+---------+-----------+
    |comment   |56     |10.00 |56       |=          |
    +----------+-------+------+---------+-----------+
    |empty     |52     |9.29  |52       |=          |
    +----------+-------+------+---------+-----------+
    Duplication
    -----------
    +-------------------------+------+---------+-----------+
    |                         |now   |previous |difference |
    +=========================+======+=========+===========+
    |nb duplicated lines      |0     |0        |=          |
    +-------------------------+------+---------+-----------+
    |percent duplicated lines |0.000 |0.000    |=          |
    +-------------------------+------+---------+-----------+
    david.appleton@27G9KY1:>


**Running pep8**

.. code-block:: bash

    david.appleton@27G9KY1:>pep8 testset_story236.py
    david.appleton@27G9KY1:>
