Test Code Rules and Structure
==============================

Directory Structure
------------------------

Test Scripts
~~~~~~~~~~~~~~~~~~~~~~~

Each test area has its own test repo which will need to be cloned by the team in question. For more details on cloning a test repo, see the notes here: :ref:`getting_started_repo-label`

For example, tests for the core test repo are found here:

- /git/ERIClitpcore-testware/python-testcases/src/main/resources/core 

The general format is:

- /git/<REPO NAME>/python-testcases/src/main/resources/<MODULE>/testset_story<NUMBER>.py


Supporting Test Files
~~~~~~~~~~~~~~~~~~~~~~

Supporting files (except plugins - see below) should be placed in the same folder as the test story tagged with the story number it is part of.

For example, lets say a core test story 212 has a file xml_example1.xml used in its test. It should be named xml_example1_story212.xml and exist here:

- /git/ERIClitpcore-testware/python-testcases/src/main/resources/core/xml_example1_story212.xml


which is the same folder as the test story.


Plugins
~~~~~~~~~~~~~~~~~~~~~


The only exception to the above rule is plugins (.rpm files) which should exist in the following directory:

- /git/<REPO NAME>/python-testcases/src/main/resources/<MODULE>/plugins/ 


while the plugin test stories and other supporting files exist in 

- /git/<REPO NAME>/python-testcases/src/main/resources/<MODULE>/


Utilities
~~~~~~~~~~~~~~~~~~~

The test framework utilities are located in a seperate utils repo as noted here: :ref:`getting_started_repo-label`  


**N.B. You should consult The Mighty Ducks (themightyducks@ammeon.com) if you need a utility to be written/updated, no one else is permitted to edit the utility files.**

 

Standard Conventions
----------------------------

**N.B:** Please ensure your pylint/pep8 are running the versions and configured as stated in :ref:`test-env-setup-label`.


The review checklist should be followed for all test code development: :ref:`review-label` 


System Test Special Rules
-----------------------------

All of the above sections should apply to system test scripts with the following exceptions:

- System test files should be saved in the following directory structure:

    - git/test/src/testScripts/ST/litp_2_1/AREA/SUB-AREA/testset_sub-area.py

- The naming convention for the files should be testset_XX.py, where XX is the name of the SUB-AREA parent folder. 

- For example, the system test file for logging can be found here:

    - git/test/src/testScripts/ST/litp_2_1/FUNCTIONAL/logging/testset_logging.py

- The classname used in system test files should follow the sub area name noted above. (E.g. 'class Logging()' in the above example.)

- Plugins should not follow the structure stated above and instead be copied to plugins/plugin_rpms with the plugins folder containing the actual code.
