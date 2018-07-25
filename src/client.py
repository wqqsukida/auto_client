# -*- coding: UTF-8 -*-

import datetime
import requests
from src.plugins import PluginManager
from lib.config import settings
# from concurrent.futures import ThreadPoolExecutor
import json
import os
import copy_reg
import types
import hashlib
import time

def _pickle_method(m):
    if m.im_self is None:
        return getattr,(m.im_class,m.im_func.func_name)
    else:
        return getattr,(m.im_self,m.im_func.func_name)
    
copy_reg.pickle(types.MethodType,_pickle_method)



class BaseClient(object):
    def __init__(self):
        self.api = settings.API
        self.task_api = settings.TASK_API
        self.api_token = settings.API_TOKEN

    def post_server_info(self,server_dict):
        # requests.post(self.api,data=server_dict) # 1. k=v&k=v,   2.  content-type:   application/x-www-form-urlencoded
        response = requests.post(self.api,json=server_dict,headers={'auth-token':self.auth_header_val}) # 1. 字典序列化；2. 带请求头 content-type:   application/json
        rep = json.loads(response.text)
        return rep

    @property
    def auth_header_val(self):
        ctime = str(time.time())
        new_key = "%s|%s" % (self.api_token, ctime,)  # asdfuasodijfoausfnasdf|时间戳
        hs = hashlib.md5()
        hs.update(new_key.encode('utf-8'))
        md5_str = hs.hexdigest()

        # 6f800b6a11d3f9c08c77ef8f77b2d460，  # asdfuasodijfoausfnasdf|时间戳
        auth_header_val = "%s|%s" % (md5_str, ctime,)  # 6f800b6a11d3f9c08c77ef8f77b2d460|时间戳

        return auth_header_val

    def exe(self):
        raise NotImplementedError('必须实现exec方法')

class AgentClient(BaseClient):

    def exe(self):
        obj = PluginManager()
        server_dict = obj.exec_plugin()
        new_hostname = server_dict['basic']['data']['hostname']
        cert_path = os.path.join(settings.BASEDIR,'conf','cert.txt')

        f = open(cert_path,mode='r')
        old_hostname = f.read()
        f.close()

        if not old_hostname:
            """第一次运行"""
            with open(cert_path,mode='w') as ff:
                ff.write(new_hostname)
        else:
            server_dict['basic']['data']['hostname'] = old_hostname
        print('[%s]POST [client info] to server'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        rep = self.post_server_info(server_dict)
        # 查询server端返回结果是否有任务要执行
        task_list = rep.get('task',None)
        if task_list:
            self.post_task_res(task_list)



    def post_task_res(self,task_list):
        from src.plugins import nvme_ssd
        from multiprocessing import Pool
        import os

        ssd_obj = nvme_ssd.Nvme_ssd()
        # post_res_list = []
        # res_list = []
        p = Pool(processes=4)
        for t in  task_list:
            task_func = getattr(ssd_obj,t.get('task_content',None))
            if task_func:
                res = p.apply_async(task_func,args=(t['ssd_node'],t['task_id'],),callback=self.task_res_handler)
                # res_list.append({'task_id':t.get('task_id'),'task_res':res})
        p.close()
        # for r in res_list:
        #     r['task_res'] = r['task_res'].get()
        #     post_res_list.append(r)

                # #客户端执行任务函数
                # task_res = task_func(task['ssd_node'])
                # # 构成任务执行结果的列表
                # post_res_list.append({'task_id':task.get('task_id'),
                #                        'task_res':task_res})
        # if post_res_list:
        #     # 将任务执行结果发送给服务端
        #     print('[%s]POST [client task_res] to server'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        #     response = requests.post(self.task_api, json=post_res_list)
    
    def task_res_handler(self,task_res):

        print('[{0}]POST [client task_res: {1}] to server'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                                  task_res))
        response = requests.post(self.task_api,json=task_res,headers={'auth-api':self.auth_header_val})
        
    
class SaltSshClient(BaseClient):
    pass
    # def task(self,host):
    #     obj = PluginManager(host)
    #     server_dict = obj.exec_plugin()
    #     self.post_server_info(server_dict)
    # 
    # def get_host_list(self):
    #     response = requests.get(self.api)
    #     # print(response.text) # [{"hostname": "c1.com"}]
    #     return json.loads(response.text)
    # 
    # def exec(self):
    #     pool = ThreadPoolExecutor(10)
    # 
    #     host_list = self.get_host_list()
    #     for host in host_list:
    #         pool.submit(self.task,host['hostname'])
