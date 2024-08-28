How to use the Find Command to Avoid Hard-coding LITP Paths
=============================================================

Why We Don't Hardcode
----------------------

When we design automated tests, assumptions have to be made that the LITP tree has been populated with certain objects. For example, we can expect that node objects exist somewhere in the tree. However, although we can assume that certain object types exist, we must never make assumptions in our test about where exactly they exist. For example, the below is hard-coding paths and is very BAD.


**Bad Coding - Hardcoded Paths**

.. code-block:: python

   NODE_URL = "/deployments/single_blade/clusters/cluster1/nodes/node1"


The reason this is bad is because in different test environments this path will be different - it is entirely dependent on how the environment has been configured in the deployment setup scripts.


How to Find an Item Type
--------------------------

As mentioned above, although we cannot assume on the location of certain objects for our test, we have to assume that certain types of items exist. Every object in the LITP tree has a specific type as is shown below.

**An example resource collection and resource**

.. code-block:: bash

    [litp-admin@ms1 ~]$ litp show -p /deployments/single_blade/clusters/cluster1/nodes
    /deployments/single_blade/clusters/cluster1/nodes
        type: collection-of-node
        state: Initial
        children:
            /node1
            /node2
    [litp-admin@ms1 ~]$ litp show -p /deployments/single_blade/clusters/cluster1/nodes/node1
    /deployments/single_blade/clusters/cluster1/nodes/node1
        type: node
        state: Initial
        properties:
            hostname: node1
        children:
            /storage_profile
            /items
            /system
            /network_profile
            /ipaddresses
            /os
    [root@ms1 ~]# litp show -p /deployments/d1/clusters/c1/nodes/n1/os
    /deployments/d1/clusters/c1/nodes/n1/os
        inherited from: /software/profiles/os_prof1
        type: reference-to-os-profile
        state: Applied
        properties (inherited properties are marked with asterisk):
            name: os-profile1 [*]
            kopts_post: console=ttyS0,115200 [*]
            breed: redhat [*]
            version: rhel6 [*]
            path: /var/www/html/6/os/x86_64/ [*]
            arch: x86_64 [*]


Note the following:

- The first item seen above is of type collection-of-node. This means that it is a container containing potentially many items of the same type.

- The second item is an actual type, node, which is defined by its properties and its related children items.

- The third item is of type reference-to-os-profile which links to an os profile defined in the infrastructure.


How to Find an Item of a Specific Type in the Framework
--------------------------------------------------------------

Given that we should know what type of item we require for our test, we need some kind of find command which will search the entire LITP tree in the current environment for items of a certain type. How this is done in the framework is shown below:

**Example of the find command**

.. code-block:: bash

    @attr('all', 'example')
    def test_01_find(self):  
     
        #This code gets the node collection url    
        node_collection_url = self.find(self.test_node, "/deployments",
                                        "node", False)
     
        #This code gets all the noe path urls
        node_urls = self.find(self.test_node, "/deployments",
                              "node")
     
        #NB: If the find cannot find any matching paths an assertion will be automatically triggered within the find. If you 
        #do not expect to find any paths you will need to pass in the assert_not_empty flag as False
        node_urls = self.find(self.test_node, "/deployments",
                              "node", assert_not_empty=False)
     
        self.assertEqual([], node_urls)
     
     
        #This code gets all os-profiles references for each node
        net_profile_urls = self.find(self.test_node, node_collection_url,
                                    "os-profile")

        #This code gets all os-profiles references for each node (as above) but looks for the exact
	#'reference-to-os-profile' name
        net_profile_urls = self.find(self.test_node, node_collection_url,
                                    "reference-to-os-profile", exact_match=True)




Note the following:

- The find command takes the following arguments:

    - The **node** which contains the LITP tree it should search (e.g. 'ms1').

    - The **path** it should search in. This makes the search more efficient but should only be set to the top level paths that LITP already has by default before any deployment script has been run or a path which you already know exists from running other finds.

    - The **type** it should search for.

    - A boolean flag on whether it should return **only collections** (set to False) **or only children** (set to True). By default it is set to True.

- The find command will return a list of all the paths which match the type. Here's an example of what the above two commands could return:

    - **self.find(self.test_node, "/deployments", "node", False)** could, for example, return: **['/deployments/single_blade/clusters/cluster1/nodes']**

    - **self.find(self.test_node, "/deployments", "node")** could, for example, return: **['/deployments/single_blade/clusters/cluster1/nodes/node1', '/deployments/single_blade/clusters/cluster1/nodes/node2']**

    - **self.find(self.test_node, node_collection_url, "network-profile")** could, for example, return **['/deployments/single_blade/clusters/cluster1/nodes/node1/network-profile', '/deployments/single_blade/clusters/cluster1/nodes/node2/network-profile']**

- If an empty list is returned by the find command, the command itself will fail with an assertion error. If you are expecting 0 items to exist you need to pass the **assert_not_empty** flag with a value of False.

- Note that the type parameter we pass is the same as the item type we would use if we were to create the item. So, for example, we don't use 'reference-to-os-profile', we just pass 'os-profile'. Also, we don't pass 'collection-of-node', we just pass 'node' but set the flag to False.
