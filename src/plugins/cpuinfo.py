import os,re
from lib.config import settings

class Cpuinfo(object):
    def process(self, cmd_func, test):
        if test:
            output = open(os.path.join(settings.BASEDIR, 'files/cpuinfo.out'), 'r', encoding='utf-8').read()

        else:
            output = cmd_func("sudo cat /proc/cpuinfo")
        return self.parse(output)
    
    def parse(self,content):
        response = {}
        p = 0
        for core in content.split("processor")[1:]:
            key_map = {}
            for row_line in core.strip().split('\n'):
                key,val = row_line.split(':')
                if not key :
                    key_map['processor'] = val.strip()
                if key.startswith('model name'):
                    key_map['model name'] = val.strip()
                if key.startswith('cpu cores'):
                    key_map['cpu cores'] = val.strip()
            response['processor%s' % p] = key_map
            p+=1
        return response