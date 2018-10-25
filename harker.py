# -*- coding: UTF-8 -*-

import requests
import time
import hashlib



response = requests.post('http://10.0.2.17/api/test/',
                        headers={'auth-token':'5e86f2cbb181696820aea27eddfd51b2|1540200262.76'})
print(response.text)