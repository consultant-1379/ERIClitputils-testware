Source Code Documentation
===========================


Generic Classes
-----------------------


.. toctree::
   :maxdepth: 2
      
.. automodule:: litp_generic_test
   :members:
   :synopsis: There is a generic test framework in unittest module in python.
              The intention I had was to use this predefined framework and
              extend it for our needs. For the start I wanted to use
              class TestCase and later on extend more classes
              from the module such as TestResult, TestLoader, TestSuite,
              TestProgram. A generic test needs to execute command on remote
              machine and process the result.

.. automodule:: litp_generic_node
   :members:

.. automodule:: litp_generic_cluster
   :members:

.. automodule:: litp_generic_utils
   :members:

Module Area classes
-----------------------

.. automodule:: litp_cli_utils
   :members:  
   :synopsis: Inherited class from :module: litp_generic_test
              in order to separate CLI related methods somewhere

.. automodule:: rest_utils
   :members:  
   :synopsis: Utils for REST tests

.. automodule:: xml_utils
   :members:   
   :synopsis: xml related utility

.. automodule:: storage_utils
   :members:   
   :synopsis: Contains Storage related methods somewhere

.. automodule:: networking_utils
   :members:    
   :synopsis: Utils for Networking tests

.. automodule:: litp_security_utils
   :members:   

.. automodule:: libvirt_utils
   :members: 
   :synopsis: Libvirt related functions

.. automodule:: redhat_cmd_utils
   :members: 
   :synopsis: Inherited class from :module: litp_generic_test
              in order to separate CLI related methods somewhere

.. automodule:: json_utils
   :members:
   :synopsis: Class to handle json related functionality

.. automodule:: vcs_utils
   :members:  
   :synopsis: VCS related commands/methods constructed to lessen the size
              of test code.

.. automodule:: third_pp_utils
   :members:
   :synopsis: Utils related to 3PP

Test Constants
-----------------------

.. automodule:: test_constants
   :members:   
