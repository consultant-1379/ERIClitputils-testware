import sys
from datetime import datetime


class CheckSleeps(object):
    """
    Class to check sleeps in log are as long as expected
    """

    def __init__(self, logfile):
        """
        Set logfile name
        """
        self.log_file = logfile
        ###Will flag failure if wait is greater than 1 second. Alter
        ##as required.
        self.threshold = 1

    def get_second(self, line):
        """
        Get the current second
        """
        second = int(line.split("second(s) elapsed out of")[0].split()[-1])
        #print "Second found: " + second

        return second

    def get_month_num(self, time_str):
        """
        Uses the month dict to find the month from a string
        """
        month_dict = dict()
        month_dict['Jan'] = 1
        month_dict['Feb'] = 2
        month_dict['Mar'] = 3
        month_dict['Apr'] = 4
        month_dict['May'] = 5
        month_dict['Jun'] = 6
        month_dict['Jul'] = 7
        month_dict['Aug'] = 8
        month_dict['Sep'] = 9
        month_dict['Oct'] = 10
        month_dict['Nov'] = 11
        month_dict['Dec'] = 12

        for month in month_dict.keys():
            if month.lower() in time_str.lower():
                return month_dict[month]

        return None

    def get_delta(self, before, after):
        """
        Check if timestamp shows exactly 1 second has passed.
        """
        if not before:
            return 1

        time_before = before.split()[2]
        hour, minutes, seconds = time_before.split(":")
        month = self.get_month_num(before.split()[0])
        date = before.split()[1]
        year = datetime.now().year
        dt_before = datetime(int(year),
                             int(month),
                             int(date),
                             int(hour),
                             int(minutes),
                             int(seconds))

        time_after = after.split()[2]
        hour, minutes, seconds = time_after.split(":")
        month = self.get_month_num(before.split()[0])
        date = before.split()[1]
        year = datetime.now().year

        dt_after = datetime(int(year),
                            int(month),
                            int(date),
                            int(hour),
                            int(minutes),
                            int(seconds))

        delta_secs = (dt_after - dt_before).seconds

        return delta_secs

    def report_line(self, last_line, line, secs):
        """
        Print out warning when sleeps are longer than expected.
        """
        print "#######ERROR#########"
        print "Time delay between below lines is greater than expected:"
        print last_line
        print line
        print ">>> Sleep between lines:", secs

    def parse_log(self):
        """
        Reads logfile
        """
        next_sec = 0
        last_line = None
        num_sleep_checks = 0
        num_failures = 0
        with open(self.log_file, "r+") as f:
            for line in f:
                if "second(s) elapsed out of" in line:
                    current_sec = self.get_second(line)

                    #Next count in sequence
                    if current_sec == next_sec:
                        num_sleep_checks += 1
                        time_delta = self.get_delta(last_line, line)
                        if time_delta > self.threshold:
                            self.report_line(last_line, line, time_delta)
                            num_failures += 1

                    next_sec = current_sec + 1
                    last_line = line

        print "##########################"
        print "Number of log sleep cases: {0}"\
            .format(num_sleep_checks)
        print "Number of failures: {0}"\
            .format(num_failures)

        if num_failures > 1:
            exit(1)
        else:
            exit(0)

if __name__ == "__main__":

    if len(sys.argv) == 2:
        messages = sys.argv[1]
    else:
        print "Must supply path of logfile for testing"
        exit(1)

    #con = FullTestReport('2.25.16')
    con = CheckSleeps(messages)
    con.parse_log()
