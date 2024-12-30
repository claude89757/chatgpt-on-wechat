#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Airflow REST API SDK
提供对 Airflow Variables 的操作接口

Author: Your Name
Date: 2024-03-xx
"""

import os
import json
import requests

from typing import Optional, Dict, List
from urllib.parse import urljoin

class AirflowSDK:
    def __init__(self, base_url: str, username: str, password: str):
        """初始化 Airflow SDK
        
        Args:
            base_url: Airflow 服务器地址
            username: 用户名
            password: 密码
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送 HTTP 请求到 Airflow API
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 请求参数
        """
        url = urljoin(f"{self.base_url}/api/v1/", endpoint)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def get_variable(self, key: str) -> Optional[str]:
        """获取 Airflow 变量值
        
        Args:
            key: 变量名
        
        Returns:
            变量值，如果不存在返回 None
        """
        try:
            response = self._make_request('GET', f'variables/{key}')
            return response.json()['value']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def set_variable(self, key: str, value: str) -> bool:
        """设置 Airflow 变量
        
        Args:
            key: 变量名
            value: 变量值
        
        Returns:
            是否设置成功
        """
        data = {
            'key': key,
            'value': value
        }
        try:
            self._make_request('POST', 'variables', json=data)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # 变量已存在，尝试更新
                self._make_request('PATCH', f'variables/{key}', json={'value': value})
                return True
            raise

    def delete_variable(self, key: str) -> bool:
        """删除 Airflow 变量
        
        Args:
            key: 变量名
        
        Returns:
            是否删除成功
        """
        try:
            self._make_request('DELETE', f'variables/{key}')
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise

    def list_variables(self) -> List[Dict[str, str]]:
        """获取所有 Airflow 变量
        
        Returns:
            变量列表，每个变量包含 key 和 value
        """
        response = self._make_request('GET', 'variables')
        return response.json()['variables']
    

def get_sh_tennis_court_data():
    airflow = AirflowSDK(
        base_url='http://zacks.com.cn',
        username=os.getenv('ZACKS_AIRFLOW_USER'),
        password=os.getenv('ZACKS_AIRFLOW_PWD')
    )
    data_01 = airflow.get_variable('上海青少体育网球场')
    data_02 = airflow.get_variable('上海卢湾网球场')
    data_list = []
    data_01_list = json.loads(data_01)
    data_02_list = json.loads(data_02)
    data_list.extend(data_01_list)
    data_list.extend(data_02_list)
    print(data_list)
    return data_list

# 测试
if __name__ == '__main__':
    get_sh_tennis_court_data()
