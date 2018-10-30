# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 9/25/18 11:24 AM
# FileName: do_task.py
from src import client
from lib.config import settings
from lib.log import logger
from multiprocessing import Pool,Process
import json
import copy
import requests
import datetime
import os
import subprocess
import traceback

class Do_task(client.BaseClient):

    def __init__(self,stask_id,script_name,args_str):
        super(Do_task,self).__init__()
        self.stask_id = stask_id
        self.script_name = script_name
        self.args_str = args_str

        self.script_dir = self.script_name.split('.')[0]
        self.script_file = os.path.join(settings.BASEDIR, 'task_handler/script/%s' % self.script_dir,
                                   '%s' % self.script_name)
        # self.task_res_file = os.path.join(settings.BASEDIR,'task_handler/script/%s/res/res,json'%self.script_dir)

    def stask_process(self):
        '''
        单个任务进程执行函数
        :param stask_id:
        :param script_name:
        :param args_str:
        :return:
        '''
        stask_res = {"stask_id": self.stask_id, "status_code": 5,
                     "run_time": "", "message": "", "data": {self.script_name: ""}}

        if os.path.exists(self.script_file):  # 开始执行任务脚本
            # stask_res['start_time'] = time.time()
            if not os.path.exists(self.task_res_path):
                json.dump([], open(self.task_res_path, 'wb'))
            
            start_time = datetime.datetime.now()
            try:
                res = subprocess.Popen('sudo sh {script} {args}'.format(script=self.script_file, args=self.args_str),
                                       shell=True, stdout=subprocess.PIPE)
                res.wait()
                # 将任务生成文件重新命名
                if os.path.exists("/tmp/task_file"):
                    os.rename("/tmp/task_file", "{0}_{1}".format("/tmp/task_file",self.stask_id))
                # stask_res["end_time"] = time.time()
                end_time = datetime.datetime.now()
                run_time = end_time - start_time
                stask_res["run_time"] = str(run_time)
                stask_res["status_code"] = 2
                stask_res["data"][self.script_name] = res.stdout.read()
            except Exception as e:
                # stask_res["end_time"] = time.time()
                end_time = datetime.datetime.now()
                run_time = end_time - start_time
                stask_res["run_time"] = str(run_time)
                stask_res["status_code"] = 3
                msg = traceback.format_exc()
                stask_res["data"][self.script_name] = msg
                stask_res["message"] = msg
                logger.error(msg)
        else:
            stask_res["status_code"] = 3
            msg = "client can not find task script!"
            stask_res["data"][self.script_name] = msg
            stask_res["data"][self.script_name] = msg
            stask_res["message"] = msg
            logger.error(msg)
        self.res_callback(stask_res)
        self.post_file(stask_res)
        # return stask_res
    
    def res_callback(self, stask_res):
        # rep = requests.post(self.stask_api, json=st_res, headers={'auth-token': self.auth_header_val})
        # print('[{0}]POST [client stask_res: {1}] to server'.format(
        #     datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), st_res))
        # 添加任务结果至res.json
        with open(self.task_res_path, 'rb') as f:
            res_json = json.load(f)
        res_json.append(stask_res)
        # print(res_json)
        json.dump(res_json, open(self.task_res_path, 'wb'))
       ############################
        obj = client.AgentClient()#
        obj.check_task()          #
       ############################
        
    def post_file(self,stask_res):
        # 上传任务文件
        # res_file = os.path.join(settings.BASEDIR, 'task_handler/res/task_file_%s') % stask_res['stask_id']
        res_file = "/tmp/task_file_%s" % stask_res['stask_id']
        if os.path.exists(res_file):
            # task_file发送至server
            try:
                rep = requests.post(self.file_api, data={'hostname': self.hostname, 'stask_id': stask_res['stask_id']},
                              headers={'auth-token': self.auth_header_val},
                              files={'task_file': open(res_file, 'rb')},
                              )
                print_info = '[{0}]POST [task_file: {1}] to server'.format(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), res_file)
                print print_info
                logger.info(print_info)
            except requests.ConnectionError, e:
                msg = traceback.format_exc()
                rep = {'code': 3, 'msg': msg}
                print rep
                logger.error(rep)
        else:
            rep = {}
        
        return rep
        
    
