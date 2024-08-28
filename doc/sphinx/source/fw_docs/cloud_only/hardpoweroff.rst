.. _poweroff-label:

Simulating a hard poweroff in the cloud (in review)
====================================================

As part of robustness testing it is useful in some cases to perform a hard poweroff of a peer node in different circumstances and test how LITP responds. The below steps detail how this can be done in a VAPP environment.


Performing a hard poweroff 
-------------------------------

The poweroff_peer_node method can be used to do a hard poweroff of the selected peer node as shown in the below code example.

.. code-block:: python


    def setUp(self):
	"""
	Setup of testcase
	"""
        #Get references for ms and an example peer node in normal way
	self.ms_node = self.get_management_node_filename()
	self.peer_node = self.get_managed_node_filenames()[0]

    @attr('all', 'example')
    def test_01_p_hard_poweroff(self):
        """
        Description:
          Test robustness after hard poweroff
        """
	#1. Run steps to set up scenario for robustness test
	.
	.
	.
	#2. Perform hard shutdown of the peer node
 	self.poweroff_peer_node(self.test_ms, self.peer_node)

        #3 Run steps to test LITP when in this state of a powered off node
        .
        .

Power on a powered off node
-----------------------------

After performing a power off of a node you will need to turn it on again to further test robustness and return the system to the same state. You can do this with the **poweron_peer_node** method as shown below.

.. code-block:: python


    def setUp(self):
	"""
	Setup of testcase
	"""
        #Get references for ms and an example peer node in normal way
	self.ms_node = self.get_management_node_filename()
	self.peer_node = self.get_managed_node_filenames()[0]

    @attr('all', 'example')
    def test_01_p_hard_poweroff(self):
        """
        Description:
          Test robustness after hard poweroff
        """
	#1. Run steps to set up scenario for robustness test
	.
	.
	.
	#2. Perform hard shutdown of the peer node
 	self.poweroff_peer_node(self.test_ms, self.peer_node)

        #3 Run steps to test LITP when in this state of a powered off node
        .
        .
        #4 Poweron peer node
        #Note that by default this will poweron and wait for the node to be up and able to accept ssh connections.
        self.poweron_peer_node(self.test_ms, self.peer_node)

Note that the poweron_peer_node by default will wait until the node in question responds to pings and ssh requests. If you want to just power on the node you can set the wait_poweron parameter to false as shown below:


.. code-block:: python
 
   .
   .
   #This will return immedietly rather than wait for the node to reach a powered on state again.
   self.poweron_peer_node(self.test_ms, self.peer_node, wait_poweron=False)
   .
   .

