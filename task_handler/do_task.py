# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 9/11/18 11:22 AM
# FileName: do_task.py
from src import client
from lib.config import settings
from multiprocessing import Pool
import json
import copy
import requests
import datetime
import os
import subprocess

class Do_task(client.BaseClient):
    def post_res_json(self):
        '''
        每次循环上报任务结果
        :return:
        '''
        with open(self.task_res_path, 'rb') as f:
            res_json = json.load(f)
        if res_json:
            res_json_copy = copy.deepcopy(res_json)  # copy一份原list来解决for循环索引串位问题
            try:
                for task_res in res_json:
                    '''1:新任务 2:执行完成 3:执行失败 4:执行暂停 5:执行中'''
                    if task_res["status_code"] == 2 or task_res["status_code"] == 3:
                        requests.post(self.stask_api, json=task_res, headers={'auth-token': self.auth_header_val})
                        print('[{0}]POST [client stask_res: {1}] to server'.format(
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task_res))
                        res_json_copy.remove(task_res)
                        # print(res_json_copy)
                        json.dump(res_json_copy, open(self.task_res_path, 'wb'))
            except requests.ConnectionError, e:
                rep = {'code': 3, 'msg': str(e)}
                print rep

    def do_stask(self, server_task_list):
        '''
        开启进程池执行任务列表
        :param server_task_list:
        :return:
        '''
        if not os.path.exists(self.task_res_path):
            json.dump({}, open(self.task_res_path, 'wb'))
        p = Pool()
        for st in server_task_list:
            res = p.apply(func=self.stask_process,
                          args=(st['stask_id'], st['script_name'], st['args_str']),
                          )
        p.close()
        # for st in server_task_list:
        #     stask_res = self.stask_process(st['stask_id'],st['script_name'],st['args_str'])
        #     self.res_callback(stask_res)

    def stask_process(self, stask_id, script_name, args_str=''):
        '''
        单个任务进程执行函数
        :param stask_id:
        :param script_name:
        :param args_str:
        :return:
        '''
        script_file = os.path.join(settings.BASEDIR, 'task_handler/script', '%s.sh' % script_name)
        # res_file = os.path.join(settings.BASEDIR,'task_handler/res/task_file_%s')%stask_id

        stask_res = {"stask_id": stask_id, "status_code": 5, "run_time": "",
                     "message": "", "data": {script_name: ""}}

        if os.path.exists(script_file):  # 开始执行任务脚本
            # stask_res['start_time'] = time.time()
            start_time = datetime.datetime.now()
            try:
                res = subprocess.Popen('sudo sh {script} {args}'.format(script=script_file, args=args_str),
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

    def res_callback(self, stask_res):
        # 添加任务结果至res.json
        with open(self.task_res_path, 'rb') as f:
            res_json = json.load(f)
        res_json.append(stask_res)
        # print(res_json)
        json.dump(res_json, open(self.task_res_path, 'wb'))
        # 上传任务文件
        # res_file = os.path.join(settings.BASEDIR, 'task_handler/res/task_file_%s') % stask_res['stask_id']
        res_file = "/tmp/task_file_%s" % stask_res['stask_id']
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