How to get Attributes or Property Values from Items in the LITP Tree
=================================================================

Understanding Attributes and Properties
-----------------------------------------

If you were to run a show command on an item in the LITP tree, you would see a number of attribute and property values returned as shown below:

**Showing an item's attributes and properties**

.. code-block:: bash

    [root@ms1 ~]# litp show -p /deployments/single_blade/clusters/cluster1/nodes/node1/ipaddresses/ip1
    /deployments/single_blade/clusters/cluster1/nodes/node1/ipaddresses/ip1
    links to: /infrastructure/networking/ip_ranges/range1
    type: ip-range
    state: Initial
    properties:
    network_name: nodes
    address: 10.46.86.96

We can see the following attributes for this item:


+---------------------+-----------------------------------------------+
|Attribute            |  Attribute Value                              |
+=====================+===============================================+
|type                 |  ip-range                                     |
+---------------------+-----------------------------------------------+
|state                |  Initial                                      |
+---------------------+-----------------------------------------------+
|links to             |  /infrastructure/networking/ip_ranges/range1  |
+---------------------+-----------------------------------------------+

We can see the following properties for this item:


+----------------+------------------------+
|Property        |  Property Value        |
+================+========================+
|network_name    |  nodes                 |
+----------------+------------------------+
|address         |  10.46.86.96           |
+----------------+------------------------+

The test framework provides two different methods to allow us to extract the above items as explained below.


Using the Test Framework to Extract Attributes
------------------------------------------------

The CLI area class provides the method get_show_data_value_cmd to extract a particular field from a LITP item. See an example of it being used below:

**Using the get_show_data_value_cmd command**

.. code-block:: python

    @attr('all', 'example')
    def test_get_data_cmd(self):
        #Get a URL for the ip range using the find command
        ip_range_urls = self.find(self.test_node,
                                  "/deployments",
                                  "ip-range")
        ip_range_example_url = ip_range_urls[0]
     
        #Get a cmd which finds the 'state' value of the returned ip range path
        get_data_cmd = self.cli.get_show_data_value_cmd(ip_range_example_url,
                                                        "state")
        #Now we run the passed command, the state value is output to stdout
        stdout, stderr, returnc = self.run_command(self.test_node,
                                                   get_data_cmd)
        print "State is {0}".format(stdout[0])


Note the following:

- The function get_show_data_value_cmd does not return the actual state value but rather returns a command which can be run which will return the state value to stdout. (Essentially, it is a show command with sed and grep to remove information we don't want)

- Assuming the above method is run against the path in the show command at the top of this section, the final print out will be "State is Initial"

- This method also allows properties to be extracted by simply passing the property name (e.g. 'address') instead of an attribute name to get_show_data_value_cmd


Using the Test Framework to Extract Properties
-------------------------------------------------

The get_props_from_url method of Generic Test will return either a dictionary of all property values on that url or just a string if you pass in the filter parameter to just get a single property. See the example below for more details.

**Using the get_props_from_url function**

.. code-block:: python

    @attr('all', 'example')
    def test_get_properties_cmd(self):
        #Get a URL for the ip range using the find command
        ip_range_urls = self.find(self.test_node,
                                  "/deployments",
                                  "ip-range")
        ip_range_example_url = ip_range_urls[0]
        #Get all properties for the url in a dict
        props_dict = self.get_props_from_url(self.test_node,
                                             ip_range_example_url)
     
        print "The network name property is: {0}"\
            .format(props_dict['network_name'])
        print "The address property is: {0}"\
            .format(props_dict['address'])
     
        ##Use the filter option to just get the address property
        address_prop = self.get_props_from_url(self.test_node,
                                             ip_range_example_url,
                                             "address")
        print "The address property (using filter) is: {0}"\
            .format(address_prop)

**Note the following:**

- If we have more than one property, then it is more efficient to get all the properties returned in a dict and then to reference the dict as shown above

- If we are only interested in the value of one of the properties, then we can pass this in as a filter parameter and the function will return just the value of that property as a string

- The printouts from the above function display the following:
    - The network name property is: nodes

    - The address property is: 10.46.86.96

    - The address property (using filter) is: 10.46.86.96

**NOTE**: Method 1 can be used to extract properties instead of method 2. It will depend on your test case as to which is best to use. If you have a number of properties to check, then method 2 is better as it returns a dictionary of all properties, whereas method 1 just returns one property value.
