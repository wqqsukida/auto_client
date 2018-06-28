import os

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLUGIN_ITEMS = {
    "nic": "src.plugins.nic.Nic",
    "disk": "src.plugins.disk.Disk",
    "memory": "src.plugins.memory.Memory",
    "cpuinfo": "src.plugins.cpuinfo.Cpuinfo",
    # "nvme_ssd": "src.plugins.nvme_ssd.Nvme_ssd",
}

API = "http://127.0.0.1:8000/api/server/"

TEST = True

MODE = "AGENT" # AGENT/SSH/SALT

SSH_USER = "root"
SSH_PORT = 22
SSH_PWD = "sdf"