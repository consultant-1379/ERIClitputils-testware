"""
LITP Generic Cluster
"""

from os import listdir, path, environ
from litp_generic_node import GenericNode


class GenericCluster(object):
    """Abstraction of a cluster of nodes.

    .. note::
       This will be instantiated from :class:`GenericTest`
    """

    def __init__(self):
        """Initialization of properties plus instantiation
           of multiple classes :class:`GenericNode` forming a cluster.
        """
        self.nodes = []

        new_format = False
        # This is where the new style taf file format is found
        if "LITP_CONN_DATA_FILE" in environ:
            self.con_data_path = environ['LITP_CONN_DATA_FILE']
            new_format = True
        # This is where the old style file format is found
        elif "LITP_CON_DATA_PATH" in environ:
            self.con_data_path = environ['LITP_CON_DATA_PATH']
        else:
            self.con_data_path = '/opt/ericsson/SIT/connection_data_files/'

        print "NOTE: Using connection data in this path: {0}"\
            .format(self.con_data_path)

        if new_format:
            #print "NEW STUFF"
            self.parse_taf_con_file()
        else:
            # slave is set up in Jenkins as environment variable to
            # distinguish between environments
            print "Using legacy connection format."\
                         + " Export LITP_CONN_DATA_FILE to"\
                         + " use the new format"

            self.slave = environ['LITP_SLAVE']

            self.fields = 7
            filepath = path.dirname(__file__)

            # relative path to connection data files depending on absolute path
            # to this file
            self.path = path.join(filepath, self.con_data_path)

            for item in listdir(path.join(self.path, self.slave)):
                with open(path.join(self.path, self.slave, item), 'r') \
                        as nodefile:
                    for line in nodefile:
                        if not line.startswith('#'):
                            line = line.strip().strip('\n').split(',')
                            if line and len(line) == self.fields:
                                try:
                                    #line = line.split(',')
                                    node = GenericNode()
                                    ##This will soon be set by the connection
                                    #data files. Hardcoded temp
                                    node.rootpw = "@dm1nS3rv3r"

                                    node.ipv4 = line[0]
                                    node.username = line[1]
                                    node.password = line[2]
                                    node.mac = line[3]
                                    node.ipv6 = line[4]
                                    node.hostname = line[5]
                                    # node.nodetype = line[6].lower()
                                    node.nodetype = line[6].lower()
                                    node.filename = item.lower()
                                    # If not set in the file, set based
                                    # on filename
                                    if not node.nodetype or \
                                            "end" in node.nodetype:
                                        node.nodetype = \
                                            self.set_type_by_filename(
                                            node.filename)

                                    self.nodes.append(node)
                                except Exception:
                                    raise ValueError(
                                        """
                                        Processing: {fname}

                                        Please check your data conn files!
                                        """.format(fname=item))

    def load_taf_data_fields(self):
        """
        Loads the TAF config file into a dict.
        """
        variable_list = list()
        created_nodes = list()

        # Load all variables into a dictionary list
        with open(self.con_data_path, 'r') as nodefile:
            for line in nodefile:
                # Ignore hash comments
                if not line.startswith('#'):
                    variable_dict = dict()
                    # Split variable between value and variable name.
                    # N.b. We limit the split as value may contain '=',
                    # e.g. in password
                    variable_parts = line.split("=", 1)
                    # If line contains no name/value parts, skip line
                    if len(variable_parts) < 2:
                        continue
                    variable_name = variable_parts[0]
                    variable_value = variable_parts[1]

                    # Get hostname from variable name
                    hostname = variable_name.split(".")[1]

                    if not hostname in created_nodes:
                        created_nodes.append(hostname)

                    variable_dict[variable_name] = variable_value
                    variable_list.append(variable_dict)

        return variable_list, created_nodes

    def parse_taf_con_file(self):
        """
        Read data from TAF format connection data files.
        """

        variable_list, created_nodes \
            = self.load_taf_data_fields()

        for hostname in created_nodes:
            node = GenericNode()
            node.hostname = hostname
            node.filename = hostname
            node.mac = None
            node.ipv6 = None

            for variable in variable_list:
                for key, value in variable.iteritems():
                    #print "KEY", key
                    #print "VALUE", value
                    if hostname in key:
                        #print "--------------------------"
                        if ".ipv6" in key:
                            node.ipv6 = value.strip()
                        if ".ip" in key and ".ipv6" not in key:
                            node.ipv4 = value.strip()
                            #print "ipv4: ", node.ipv4
                        if ".vip" in key:
                            splitted = key.split(".vip")
                            if len(splitted) < 2:
                                vip_name = "vip1"
                            else:
                                vip_name = splitted[-1]
                            node.vips[vip_name] = value.strip()
                        elif "user.root.pass" in key:
                            node.rootpw = value.strip()
                            #print "root passwd: ", node.rootpw
                        elif "user." in key and ".type" not in key:
                            node.password = value.strip()
                            node.username = key.split(".")[3]
                            #print "user: ", node.username
                            #print "passwd: ", node.password
                        elif ".type" in key and "user.root" not in key:
                            node.nodetype = self.__get_nodetype(value)

            self.nodes.append(node)

    @staticmethod
    def __get_nodetype(value):
        """
        Processes a line in the TAF connection data file to find the type.

        Args:
           value (str): The line in connection data file.

        Returns:
            str. The type of node - "management", "rhel", "sfs" or "managed".
        """

        if "MS" in value:
            return "management"
        elif "NFS" in value:
            return "rhel"
        elif "SFS" in value:
            return "sfs"
        elif "VA" in value:
            return "va"
        else:
            return "managed"

    @staticmethod
    def set_type_by_filename(fname):
        """
        Sets the type of node based on filename.

        Args:
            fname (str): Filename of the node.

        Returns:
            "management" if 'ms' is contained in the filename or
            "sfs" if 'sfs' is contained in the filename or
            "rhel" if 'rhel' is contained in the filename.
            If none of the aforementioned strings exist in the filename,
            "managed" is returned.
        """
        if "ms" in fname:
            n_type = "management"
        elif "sfs" in fname:
            n_type = "sfs"
        elif "va" in fname:
            n_type = "va"
        elif "rhel" in fname:
            n_type = "rhel"
        else:
            n_type = "managed"
        return n_type
