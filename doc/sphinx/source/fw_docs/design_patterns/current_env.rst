How to Find Out the Current Environment in a Test (e.g. SINGLEBLADE or MULTIBLADE)
===================================================================================

There are a number of cases where a test will need to behave differently depending on whether it is running on a singleblade or multiblade environment.

The test framework provides the method is_singleblade_env in GenericTest which can be used as shown below:

**Using is_singleblade_env method**

.. code-block:: python

    @attr('all', 'example')
   def test_network_example(self):
      is_singleblade = self.is_singleblade_env()
       
      if is_singleblade:
          #Do singleblade specific stuff
                    
      else:
          #Do multiblade specific stuff


The method works by querying the SINGLEBLADE environment variable, which is set to 'yes' if the test is run on a singleblade environment or 'no' otherwise. If you are running the test on your local machine you will need to export this variable as shown below:


.. code-block:: bash

   > export SINGLEBLADE="yes"
