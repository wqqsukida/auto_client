# -*- coding: UTF-8 -*-

import os

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLUGIN_ITEMS = {
    "nic": "src.plugins.nic.Nic",
    "disk": "src.plugins.disk.Disk",
    "memory": "src.plugins.memory.Memory",
    # "cpuinfo": "src.plugins.cpuinfo.Cpuinfo",
    "nvme_ssd": "src.plugins.nvme_ssd.Nvme_ssd",
}

API = "http://10.0.2.17/api/server/"

TEST = False

MODE = "AGENT" # AGENT/SSH/SALT

NVME_TOOL_PATH = "/home/wuyifei/code/s16autohost/s5day91/auto_client/nvme-cli-master"

SSH_USER = "root"
SSH_PORT = 22
SSH_PWD = "sdf"