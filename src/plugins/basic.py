
class Basic(object):

    @classmethod
    def initial(cls):
        return cls()

    def process(self,cmd_func,test):
        if test:
            output = {
                'os_platform': "linux",
                'os_version': "CentOS release 6.6 (Final)\nKernel \r on an \m",
                'hostname': 'c4.com',
                'cpu_physical_count': '4',
                'cpu_count': '8',
                'cpu_model': 'X86'
            }
        else:
            output = {
                'os_platform': cmd_func("uname").strip(),
                'os_version': cmd_func("cat /etc/issue").strip().split('\n')[0],
                'hostname': cmd_func("hostname").strip(),
                'cpu_physical_count' : cmd_func("sudo cat /proc/cpuinfo | grep 'physical id' | sort | uniq | wc -l"),
                'cpu_count' : cmd_func("sudo cat /proc/cpuinfo | grep 'processor' | wc -l"),
                'cpu_model' : cmd_func("sudo cat /proc/cpuinfo | grep name | cut -f2 -d:| uniq -c")
            }
        return output
