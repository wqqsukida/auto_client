# -*- coding: UTF-8 -*-
from .base import BasePlugin
from lib.config import settings

class Basic(BasePlugin):

    @classmethod
    def initial(cls):
        return cls()

    def linux(self,cmd_func,test):
        if test:
            output = {
                'os_platform': "linux",
                'os_version': "CentOS release 6.6 (Final)\nKernel \r on an \m",
                'hostname': 'c4.com',
                'cpu_physical_count': '4',
                'cpu_count': '8',
                'cpu_model': 'X86',
                'client_version': settings.CLIENT_VERSION
            }
        else:
            output = {
                'os_platform': cmd_func("uname").strip(),
                'os_version': cmd_func("cat /etc/issue").strip().split('\n')[0],
                'hostname': cmd_func("hostname").strip(),
                'cpu_physical_count' : cmd_func("sudo cat /proc/cpuinfo | grep 'physical id' | sort | uniq | wc -l"),
                'cpu_count' : cmd_func("sudo cat /proc/cpuinfo | grep 'processor' | wc -l"),
                'cpu_model' : cmd_func("sudo cat /proc/cpuinfo | grep name | cut -f2 -d:| uniq -c"),
                'client_version': settings.CLIENT_VERSION
            }
        return output
    
    def win(self,cmd_func,test):
        output = {

        }
        
        return output