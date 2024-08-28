"""
Third Party Product Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""


class ThirdPPUtils(object):
    """
    Third Party Product related utilities.
    """

    def __init__(self):
        """Initialise 3pp path variables.
        """
        self.cobbler_path = "/usr/bin/cobbler"
        self.puppet_path = "/usr/bin/puppet"

    def get_cobbler_system_cmd(self, args=''):
        """
        Generate a cobbler system command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. 'list').

        Returns:
            str. Correctly formatted cobbler system command.
        """
        cmd = "{0} system {1}".format(self.cobbler_path, args)
        return cmd

    def get_puppet_cert_list_cmd(self, args=''):
        """
        Generate a puppet cert list command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--all').

        Returns:
            str. Correctly formatted puppet cert list command.
        """
        cmd = "{0} cert list {1}".format(self.puppet_path, args)
        return cmd
