# -*- coding: UTF-8 -*-

import datetime
import requests
from src.plugins import PluginManager
from lib.config import settings
# from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process,Pool
import json
import os
import copy_reg
import types
import hashlib
import time
import datetime
import uuid
import subprocess
import copy
import importlib

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
        self.stask_api = settings.STASK_API
        self.file_api = settings.FILE_API
        self.api_token = settings.API_TOKEN
        self.task_res_path = os.path.join(settings.BASEDIR,'task_handler/res/res.json')
        # 获取主机名
        cert_path = os.path.join(settings.BASEDIR, 'conf', 'cert.txt')
        f = open(cert_path, mode='r')
        hostname = f.read()
        f.close()
        self.hostname = hostname

    def post_server_info(self,server_dict):
        # requests.post(self.api,data=server_dict) # 1. k=v&k=v,   2.  content-type:   application/x-www-form-urlencoded
        try:
            response = requests.post(self.api,json=server_dict,headers={'auth-token':self.auth_header_val})
            # 1. 字典序列化；2. 带请求头 content-type:   application/json
            rep = json.loads(response.text)
            return rep
        except requests.ConnectionError,e :
            rep = { 'code': 3, 'msg':str(e)}
            print rep
            return rep
        except ValueError,e :
            rep = { 'code': 3, 'msg':str(e)}
            print rep
            return rep

    def post_res_json(self):
        '''
        每次循环检查res.json是否有完成的任务结果
        :return:{'stask': {'args_str': '', 'stask_id': 805, 'script_name': 'dd.sh'}} or {}
        '''
        with open(self.task_res_path, 'rb') as f:
            res_json = json.load(f)
        # if res_json:
        res_json_copy = copy.deepcopy(res_json)  # copy一份原list来解决for循环索引串位问题
        try:
            stask_res = {"hostname":self.hostname,"res":[]}
            for task_res in res_json:
                '''1:新任务 2:执行完成 3:执行失败 4:执行暂停 5:执行中'''
                if task_res["status_code"] == 2 or task_res["status_code"] == 3:
                    finish_task = res_json_copy.pop(res_json.index(task_res))
                    stask_res["res"].append(finish_task)
                    # print(res_json_copy)
                    json.dump(res_json_copy, open(self.task_res_path, 'wb'))
            print('[%s]POST Task_res:%s to server' %(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),stask_res))
            response = requests.post(self.stask_api, json=stask_res, headers={'auth-token': self.auth_header_val})
            rep = json.loads(response.text)
            return rep
        except requests.ConnectionError, e:
            rep = {'code': 3, 'msg': str(e)}
            print rep
        except ValueError, e:
            rep = {'code': 3, 'msg': str(e)}
            print rep
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
        # 将client端信息发送给server
        rep = self.post_server_info(server_dict)
        # 查询server端返回结果是否有ssd任务要执行
        task_list = rep.get('task',None)
        if task_list:
            self.post_task_res(task_list)

    def check_task(self):
        rep = self.post_res_json()
        # 查询server端返回结果是否有主机任务要执行
        stask = rep.get('stask')
        if stask:
            '''
            {'args_str': '', 'stask_id': 805, 'script_name': 'dd.sh'}
            '''
            from task_handler.do_task import Do_task
            dt_obj = Do_task(stask['stask_id'],stask['script_name'],stask['args_str'])
            p = Process(target=dt_obj.stask_process)
            p.start()
        # 
        # dt_obj.post_res_json()
    """    
    def post_res_json(self):
        '''
        每次循环上报任务结果
        :return:
        '''
        with open(self.task_res_path,'rb') as f:
            res_json = json.load(f)
        if res_json:
            res_json_copy = copy.deepcopy(res_json) #copy一份原list来解决for循环索引串位问题
            try:
                for task_res in res_json:
                    '''1:新任务 2:执行完成 3:执行失败 4:执行暂停 5:执行中'''
                    if task_res[ "status_code" ] == 2 or task_res[ "status_code" ] == 3:
                        requests.post(self.stask_api, json=task_res, headers={'auth-token': self.auth_header_val})
                        print('[{0}]POST [client stask_res: {1}] to server'.format(
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),task_res))
                        res_json_copy.remove(task_res)
                        # print(res_json_copy)
                        json.dump(res_json_copy,open(self.task_res_path,'wb'))
            except requests.ConnectionError, e:
                rep = {'code': 3, 'msg': str(e)}
                print rep

    def do_stask(self,server_task_list):
        '''
        开启进程池执行任务列表
        :param server_task_list:
        :return:
        '''
        if not os.path.exists(self.task_res_path):
            json.dump({},open(self.task_res_path,'wb'))
        p = Pool()
        for st in server_task_list:
            res = p.apply(func=self.stask_process,
                                args=(st['stask_id'],st['script_name'],st['args_str']),
                                )
        p.close()
        # for st in server_task_list:
        #     stask_res = self.stask_process(st['stask_id'],st['script_name'],st['args_str'])
        #     self.res_callback(stask_res)
            
    def stask_process(self,stask_id,script_name,args_str=''):
        '''
        单个任务进程执行函数
        :param stask_id:
        :param script_name:
        :param args_str:
        :return:
        '''
        script_file = os.path.join(settings.BASEDIR,'task_handler/script','%s.sh'%script_name)
        # res_file = os.path.join(settings.BASEDIR,'task_handler/res/task_file_%s')%stask_id
        
        stask_res = {"stask_id": stask_id, "status_code": 5, "run_time": "",
                     "message": "", "data": { script_name: "" } }

        if os.path.exists(script_file): # 开始执行任务脚本
            # stask_res['start_time'] = time.time()
            start_time = datetime.datetime.now()
            try:
                res = subprocess.Popen('sudo sh {script} {args}'.format(script=script_file,args=args_str),
                                       shell=True, stdout=subprocess.PIPE)
                res.wait()
                # 将任务生成文件重新命名
                if os.path.exists("/tmp/task_file"):
                    os.rename("/tmp/task_file", "{0}_{1}".format("/tmp/task_file", stask_id))
                # stask_res["end_time"] = time.time()
                end_time = datetime.datetime.now()
                run_time = end_time - start_time
                stask_res["run_time"] = str(run_time)
                stask_res["status_code"] = 2
                stask_res["data"][script_name] = res.stdout.read()  
            except Exception as e:
                # stask_res["end_time"] = time.time()
                end_time = datetime.datetime.now()
                run_time = end_time - start_time
                stask_res["run_time"] = str(run_time)
                stask_res["status_code"] = 3
                stask_res["data"][script_name] = str(e)
                stask_res["message"] = str(e)
        
        self.res_callback(stask_res)
        # return stask_res

    def res_callback(self,stask_res):
        # 添加任务结果至res.json
        with open(self.task_res_path,'rb') as f:
            res_json = json.load(f)
        res_json.append(stask_res)
        # print(res_json)
        json.dump(res_json, open(self.task_res_path, 'wb'))
        # 上传任务文件
        # res_file = os.path.join(settings.BASEDIR, 'task_handler/res/task_file_%s') % stask_res['stask_id']
        res_file = "/tmp/task_file_%s"%stask_res['stask_id']
        if os.path.exists(res_file):
            # 获取主机名
            cert_path = os.path.join(settings.BASEDIR, 'conf', 'cert.txt')
            f = open(cert_path, mode='r')
            hostname = f.read()
            f.close()
            # task_file发送至server
            try:
                requests.post(self.file_api, data={'hostname': hostname, 'stask_id': stask_res['stask_id']},
                              headers={'auth-token': self.auth_header_val},
                              files={'task_file': open(res_file, 'rb')},
                              )
                print('[{0}]POST [task_file: {1}] to server'.format(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), res_file))
            except requests.ConnectionError, e:
                rep = {'code': 3, 'msg': str(e)}
                print rep
    """          
    # def do_stask(self,content,stask_id,hasfile,file_url):                                                4
    #     '''执行主机任务'''
    #     import subprocess
    #     res = subprocess.Popen(content,shell=True, stdout=subprocess.PIPE)
    #     res.wait()
    #
    #     return {'stask_id':stask_id,'stask_res':{content:res.stdout.read()},
    #             'hasfile':hasfile,'file_url':file_url}

    # def stask_res_handler(self,stask_res):
    #     ''''''
    #     try:
    #         if stask_res.get('hasfile'):
    #             # 拼接该任务唯一文件名
    #             fn = stask_res['file_url'].rsplit('/',1)[-1]
    #             file_name = '{0}_{1}'.format(fn,uuid.uuid1())
    #             # 获取主机名
    #             cert_path = os.path.join(settings.BASEDIR, 'conf', 'cert.txt')
    #             f = open(cert_path, mode='r')
    #             hostname  = f.read()
    #             f.close()
    #             # 以生成的唯一文件名发送至server
    #             requests.post(self.file_api,data={'hostname':hostname,'stask_id':stask_res['stask_id']},
    #                           headers={'auth-token': self.auth_header_val},
    #                           files={'task_file': (file_name, open(stask_res['file_url'], 'rb'))})
    #
    #         print('[{0}]POST [client stask_res: {1}] to server'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #                                                                   stask_res))
    #         response = requests.post(self.stask_api, json=stask_res, headers={'auth-token': self.auth_header_val})
    #
    #     except requests.ConnectionError,e:
    #         rep = {'code':3,'msg':str(e)}
    #         print rep
    #     except Exception ,e:
    #         requests.post(self.stask_api,json={'stask_id':stask_res['stask_id'],'error_msg':{'error':str(e)}},
    #                       headers={'auth-token': self.auth_header_val})

    def post_task_res(self,task_list):
        '''
        发送ssd任务结果
        :param task_list:
        :return:
        '''
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
        try:
            print('[{0}]POST [client task_res: {1}] to server'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                                      task_res))
            response = requests.post(self.task_api, json=task_res, headers={'auth-token': self.auth_header_val})
        except requests.ConnectionError,e:
            rep = {'code':3,'msg':str(e)}
            print rep

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
