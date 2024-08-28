"""
Storage Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""

from litp_generic_utils import GenericUtils
import re


class StorageUtils(object):
    """Storage related utilities.
    """

    def __init__(self):
        """init area class
        """
        self.gen_utils = GenericUtils()
        self.vol_status_key = "status"
        self.vol_origin_key = "origin"
        self.vol_size = "size"
        self.vol_alloc_pol = "alloc"
        self.vol_group_key = "volume_group"
        self.lvscan_path = "/sbin/lvscan"
        self.lvs_path = "/sbin/lvs"
        self.lvremove_path = "/sbin/lvremove"
        self.lvcreate_path = "/sbin/lvcreate"
        self.lvconvert_path = "/sbin/lvconvert"
        self.lvdisplay_path = "/sbin/lvdisplay"
        self.mount_path = "/bin/mount"
        self.umount_path = "/bin/umount"
        self.vxsnap_path = "/sbin/vxsnap"
        self.vxedit_path = "/sbin/vxedit"

        # Keys for lvs dict
        self.lvname_key = "LV"
        self.vgname_key = "VG"
        self.attr_key = "Attr"
        self.size_key = "LSize"
        self.origin_key = "Origin"
        self.data_key = "Data"

    def convert_gb_to_mb(self, size):
        """
        Converts given size to MB.

        Args:
            size (str): The size in GB.

        Returns:
            int. The size in MB.
        """
        return self.convert_size_to_megabytes(size)

    @staticmethod
    def convert_size_to_megabytes(size_units):
        """
        Description:
           Utility method to convert a combined size-and-unit string
           into a Numeric Megabytes value.
           Any of the following will work:
               '5G', '2T', '300.00 GiB', '15M'.
           If no unit is passed, the function will return None.

        Args:
            size_units: Combined size-and-unit string

        Returns:
            int. An integer representation of the size in MB.
                 None if conversion is not possible.
        """

        pattern = r'^\s*(?P<size>[1-9][.0-9]*)\s*(?P<unit>[MGT](iB)?)\s*$'
        regexp = re.compile(pattern)

        match = regexp.search(size_units)
        size = None
        if match:
            parts = match.groupdict()
            if parts:
                if 'size' in parts.keys() and 'unit' in parts.keys():
                    size = float(parts['size'])
                    unit = parts['unit'][0]
                    if unit == 'M':
                        pass  # no change
                    elif unit == 'G':
                        size *= 1024
                    elif unit == 'T':
                        size *= 1024 * 1024

        return int(size)

    @staticmethod
    def get_mounted_permissions_cmd(path):
        """
        Returns a command to get permissions from a mounted path.

        Args:
            Path (str): The path to check permissions on
                (e.g. /vx/ossrc1-file_system4).

        Returns:
            str. Command to check the status of the mounted path.
        """
        cmd_part1 = "stat {0} | ".format(path)
        cmd_sed = \
            r"/bin/sed -n '/^Access: (/{s/Access: (\([0-9]\+\).*$/\1/;p}'"

        full_cmd = "{0} {1}".format(cmd_part1, cmd_sed)

        return full_cmd

    def get_vxsnap_cmd(self, disk_group, vxsnap_args='list',
                       grep_args=None):
        """
        Returns a vxsnap command, optionally filtered using grep.

        Args:
            disk_group (str): The diskgroup to list snapshots in.

        Kwargs:
            vxsnap_args (str): Arguments to supply to vxsnap. Default is
                'list -g' to list snapshots within the given disk_group.

            grep_args (str): If set, will grep the resulting output.

        Returns:
            str. A vxsnap command. For example, "vxsnap list -g <disk_group>"
        """
        cmd = "{0} -g {1} {2} ".format(self.vxsnap_path,
                                       disk_group, vxsnap_args)

        if grep_args:
            cmd = cmd + "| /bin/grep {0}".format(grep_args)

        return cmd

    def get_vxedit_cmd(self, disk_group, vxedit_args='',
                       grep_args=None):
        """
        Returns a vxedit command, optionally filtered using grep.

        Args:
            disk_group (str): The diskgroup to list snapshots in.

        Kwargs:
            vxedit_args (str): Arguments to supply to vxedit.

            grep_args (str): If set, will grep the resulting output.

        Returns:
            str. A vxedit command.
        """
        cmd = "{0} -g {1} {2} ".format(self.vxedit_path,
                                       disk_group, vxedit_args)

        if grep_args:
            cmd = cmd + "| /bin/grep {0}".format(grep_args)

        return cmd

    def get_mount_list_cmd(self, grep_item=None, mount_type=None):
        """Returns a mount list command with optional
        grep or mount type filter added.

        Kwargs:
            grep_item (str): If set, will add a piped grep to
                the mount command for this item.

            mount_type (str): If set, will add the type filter (-t option) to
                the mount list command.

        Returns:
            str. The mount list command str with optional grep/type filters.
                For example, '/bin/mount -l | grep "/dev/sda"'.
        """
        grep_cmd_part = ""
        mount_type_part = ""

        if grep_item:
            grep_cmd_part = " | /bin/grep {0}".format(grep_item)

        if mount_type:
            mount_type_part = " -t {0}".format(mount_type)

        return "{0} -l {1} {2}".format(self.mount_path,
                                       mount_type_part, grep_cmd_part)

    def get_lvdisplay_cmd(self, lvdisplay_args='', grep_args=None):
        """
        Returns a lvdisplay command, optionally filtered using grep.

        Kwargs:
            lvdisplay_args (str): Arguments to pass to lvdisplay.

            grep_args (str): If set, will run grep with these
                arguments. If not set, will not filter lvdisplay output.

        Returns:
            str. A lvdisplay command.
        """
        cmd = "{0} {1}".format(self.lvdisplay_path, lvdisplay_args)

        if grep_args:
            cmd = cmd + "| /bin/grep {0}".format(grep_args)

        return cmd

    def get_lvscan_cmd(self, lvscan_args='', grep_args=None):
        """
        Returns a lvscan command, optionally filtered using grep.

        Kwargs:
            lvscan_args (str): Arguments to pass to lvscan.

            grep_args (str): If set, will run grep with these
                arguments. If not set, will not filter lvscan output.

        Returns:
            str. A lvscan command.
        """
        cmd = "{0} {1}".format(self.lvscan_path, lvscan_args)

        if grep_args:
            cmd = cmd + "| /bin/grep {0}".format(grep_args)

        return cmd

    def get_lvs_cmd(self, lvs_args='', grep_args=None):
        """
        Returns a lvs command, optionally filtered using grep.

        Kwargs:
            lvs_args  (str): Arguments to pass to lvs.

            grep_args (str): If set, will run grep with these
                arguments. If not set, will not filter lvs output.

        Returns:
            str. A lvs command.
        """
        cmd = "{0} {1}".format(self.lvs_path, lvs_args)

        if grep_args:
            cmd = cmd + "| /bin/grep {0}".format(grep_args)

        return cmd

    def get_lvremove_cmd(self, vol_to_remove, lvremove_args=''):
        """
        Returns a lvremove command.

        Kwargs:
            vol_to_remove  (str): The volume group to remove.

            lvremove_args  (str): Arguments to supply to lvremove.

        Returns:
            str. A lvremove command.
        """
        cmd = "{0} {1} {2}".format(self.lvremove_path, lvremove_args,
                                   vol_to_remove)

        return cmd

    def get_lvcreate_cmd(self, lvcreate_args=''):
        """
        Returns a lvcreate command.

        Kwargs:
            lvcreate_args (str): Arguments to supply to lvcreate.

        Returns:
            str. A lvcreate command.
        """
        cmd = "{0} {1}".format(self.lvcreate_path, lvcreate_args)

        return cmd

    def parse_lvscan_stdout(self, std_out):
        """
        Takes as input the std_out from running the lvscan command and
        returns a dictionary of the returned results.

        Args:
            std_out (list): The standard output of a lvscan command.

        Returns:
            dict. Dictionary of returned results from lvscan command.
        """
        vol_list = list()

        try:
            for line in std_out:
                ##Redhat can output spurious read failed errors.
                #We can safely ignore these.
                if "read failed" in line:
                    continue

                vol_item = dict()
                vol_item[self.vol_status_key] = line.split("'")[0].strip()
                vol_item[self.vol_origin_key] = \
                    line.split("'")[1].split("'")[0]
                vol_item[self.vol_size] = line.split("[")[1].split("]")[0]
                vol_item[self.vol_alloc_pol] = line.split("]")[1].strip()
                vol_item[self.vol_group_key] = \
                    line.split("'")[1].split("'")[0]\
                    .split("/")[3].split('_')[0]

                vol_list.append(vol_item)

        except Exception:
            raise ValueError("lvscan output cannot be parsed")

        return vol_list

    def parse_lvs_stdout(self, std_out):
        """
        Takes as input the std_out from running the lvs command
        and returns a dictionary of the returned results.

        Args:
            std_out (list): The standard output of a lvs command.

        Returns:
            dict. Dictionary of returned results from lvs command.
        """
        vol_list = list()

        try:
            for line in std_out:
                # Ignore line with headers if included in output.
                if 'LSize' in line:
                    continue

                vol_item = dict()
                line_parts = line.split()

                vol_item[self.lvname_key] = line_parts[0].strip()
                vol_item[self.vgname_key] = line_parts[1].strip()
                vol_item[self.attr_key] = line_parts[2].strip()
                vol_item[self.size_key] = line_parts[3].strip()
                if 'swi' in vol_item[self.attr_key]:
                    vol_item[self.origin_key] = line_parts[4].strip()
                    vol_item[self.data_key] = line_parts[5].strip()
                vol_list.append(vol_item)

        except Exception as exc:
            raise ValueError("lvs output cannot be parsed: {0}".format(exc))

        return vol_list


class FileSystemData(object):
    """
    Class to store data related to a file system object.
    """

    def __init__(self, props):
        """
        Init method. Pass probs dict from storage profile.
        """
        self.url = props["url"]
        self.type = props["type"]
        self.size = props["size"]
        if "mount_point" in props:
            self.mount_point = props["mount_point"]
        else:
            self.mount_point = ''
        self.snap_external = props['snap_external']
        self.snap_size = int(props["snap_size"])
        self.snappable = (self.snap_external == 'false' and self.snap_size > 0)
        self.snappable_ext4 = self.snappable and self.type == 'ext4'

    def __eq__(self, file_sys):
        """
        Test if the passed object matches this object by comparing path values.

        Args:
            file_sys (FileSystemData): Another FileSystemData object

        Returns:
           bool. True if objects match or false otherwise.
        """
        return self.url == file_sys.url

    def as_string(self):
        """
        Return the current object as a string.

        Returns:
           str. Representation of current object.
        """
        return "{0}('{1}', mount_point='{2}', snappable='{3}')"\
            .format(self.__class__.__name__,
                    self.url, self.mount_point,
                    self.snappable)
