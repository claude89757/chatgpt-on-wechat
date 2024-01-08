#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@File:     tencent_docs.py
@Time:     2022/7/12 17:34
@Author:   claude
@Software: PyCharm
"""
import os
import requests
import json


COLUMN = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
          'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO',
          'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD', 'BE', 'BF', 'BG',
          'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 'BX', 'BY',
          'BZ', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CI', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CO', 'CP', 'CQ',
          'CR', 'CS', 'CT', 'CU', 'CV', 'CW']


# 存储token到本地文件
def save_token(token):
    with open('/root/TENCENT_DOCS_TOKEN', 'w') as f:
        f.write(token)


# 从本地文件读取token
def load_token():
    with open('/root/TENCENT_DOCS_TOKEN', 'r') as f:
        token = f.read()
    return token


def get_docs_operator():
    """
    获取腾讯文档的操作对象
    :return:
    """
    # 获取腾讯文档鉴权
    try:
        tencent_docs_token = load_token()
        docs = TencentDocs(token=tencent_docs_token)
    except Exception as error:  # pylint: disable=broad-except
        print(f"{error}， token无效，重新获取...")
        docs = TencentDocs()
    save_token(docs.token)
    return docs


class TencentDocs(object):
    """
    获取控制器注册的专区、设备、设备组和资源组相关数据的类（运维相关）
    """

    def __init__(self, token: str = None):
        self.headers = {"Content-Type": "application/json"}
        # 授权码，有效时间为5分钟，且只能使用一次
        client_id = '62daceac49b5443ca98e27dd0f5fb464'
        client_secret = os.environ.get('TENCENT_DOCS_SECRET')
        refresh_token = os.environ.get('TENCENT_DOCS_REFRESH_TOKEN')
        if not token:
            token = TencentDocs.get_refresh_token(client_id, client_secret, refresh_token)
        else:
            pass
        # 验证token
        user_info = TencentDocs.get_user_info(token)
        if not user_info.get('data'):
            raise Exception(str(user_info))
        self.token = token
        self.headers['Access-Token'] = token
        self.headers['Client-Id'] = client_id
        self.headers['Open-Id'] = user_info['data']['openID']

    @staticmethod
    def _oauth_request(url_path: str):
        """
        授权接口调用
        """
        url = f"https://docs.qq.com{url_path}"
        print(f"GET {url} ")
        response = requests.get(url)
        if response.status_code == 200:
            rev_data = response.json()
            print(f"Response: {rev_data}")
            return rev_data
        else:
            raise Exception(f"{url} failed: {str(response.content)}")

    def _request(self, url_path: str, payload: dict = None, request_type: str = "GET"):
        """
        调用腾讯文档API的公共方法
        :return:
        """
        url = f"https://docs.qq.com{url_path}"
        print(f"{request_type} {url} {payload}")
        if request_type.upper() == 'GET':
            response = requests.get(url, headers=self.headers, params=json.dumps(payload))
        elif request_type.upper() == 'POST':
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        elif request_type.upper() == 'PUT':
            response = requests.put(url, headers=self.headers, data=json.dumps(payload))
        elif request_type.upper() == 'DELETE':
            response = requests.delete(url, headers=self.headers, data=json.dumps(payload))
        elif request_type.upper() == 'PATCH':
            response = requests.patch(url, headers=self.headers, data=json.dumps(payload))
        else:
            raise NotImplementedError(f"Unknown request type: {request_type}")
        if response.status_code == 200:
            rev_data = response.json()
            print(f"header: {response.headers}")
            print(f"Response: {rev_data}")
            return rev_data
        else:
            raise Exception(f"{url} failed: {str(response.content)}")

    @staticmethod
    def get_token(client_id: str, client_secret: str, code: str):
        """
        本接口用于通过授权码获取 Access Token 和 Refresh Token。(需要提前手动收取获取code后才能执行)
        :return:
        """
        return TencentDocs._oauth_request(f"/oauth/v2/token?client_id={client_id}&client_secret={client_secret}"
                                          f"&redirect_uri=https%3a%2f%2ftest.airflow.noc.woa.com"
                                          f"&grant_type=authorization_code&code={code}")

    @staticmethod
    def get_user_info(token: str):
        """
        本接口用于获取用户信息，同时也可以用来校验AccessToken的有效性。
        :return:
        """
        return TencentDocs._oauth_request(f"/oauth/v2/userinfo?access_token={token}")

    @staticmethod
    def get_refresh_token(client_id: str, client_secret: str, refresh_token: str):
        """
        本接口用于刷新 Access Token（30天内必须刷新一次）
        :return:
        """
        return TencentDocs._oauth_request(f"/oauth/v2/token?client_id={client_id}&client_secret={client_secret}"
                                          f"&grant_type=refresh_token&refresh_token={refresh_token}")['access_token']

    def get_row_data(self, file_id: str, sheet_id: str, rows: str):
        """
        获取在线表格内工作表中指定行中的单元格文本内容，可批量获取多行的内容
        :param file_id:
        :param sheet_id:
        :param rows: 想要获取指定行的行号，使用逗号进行分割，A-B表示从第A行到第B行
        如5,7-10表示获取第5、7、8、9、10这五行中的单元格的内容
        :return:
        """
        return self._request(f"/openapi/sheetbook/v2/{file_id}/sheets/{sheet_id}"
                             f"?request=GetRows&rows={rows}")['data']['rows']

    def get_today_court_msg(self):
        """
        从在线表格中获取今天的网球场信息文本
        """
        time_slots = ['21-22',
                      '20-21',
                      '19-20',
                      '18-19',
                      '17-18',
                      '16-17',
                      '15-16',
                      '14-15',
                      '13-14',
                      '12-13',
                      '11-12',
                      '10-11',
                      '09-10',
                      '08-09',
                      '07-08']

        data_list = self.get_row_data("300000000$NLrsOYBdnaed", "BB08J2", "1-16")
        print(data_list)
        update_time = str(data_list[0]['textValues'][0]).split()[-1]
        # date_str = str(data_list[1][1]).split()[0]
        weekday = str(data_list[0]['textValues'][1]).split()[-1]
        msg_list = [f"【{weekday} 网球场\U0001F3BE动态】 @{update_time}"]
        for data in reversed(data_list):
            if data['row'] >= 2:
                cell_data = data['textValues'][1]
                time_slot = time_slots[data['row']-2]
                if "已过期" in cell_data:
                    pass
                else:
                    court_name_list = []
                    for line in str(cell_data).splitlines():
                        court_name_list.append(line.split()[0])

                    if len(court_name_list) > 3 and data['row'] > 5:
                        court_name_msg = ",".join(court_name_list[:2]) + ",..."
                    else:
                        court_name_msg = ",".join(court_name_list)
                    msg_list.append(f"{time_slot}:　{court_name_msg}")
            else:
                pass
            # 获取明天的网球场动态

        weekday = str(data_list[0]['textValues'][2]).split()[-1]
        msg_list.append("----------")
        msg_list.append(f"【{weekday} 网球场\U0001F3BE动态】 @{update_time}")
        for data in reversed(data_list):
            if data['row'] >= 2:
                cell_data = data['textValues'][2]
                time_slot = time_slots[data['row'] - 2]
                if "已过期" in cell_data:
                    pass
                else:
                    court_name_list = []
                    for line in str(cell_data).splitlines():
                        court_name_list.append(line.split()[0])

                    if len(court_name_list) > 3 and data['row'] > 5:
                        court_name_msg = ",".join(court_name_list[:2]) + ",..."
                    else:
                        court_name_msg = ",".join(court_name_list)
                    msg_list.append(f"{time_slot}:　{court_name_msg}")
            else:
                pass
        msg = "\n".join(msg_list)
        return msg

    def get_up_for_send_msg_list(self):
        """
        从在线表格中，获取待发送的信息列表
        """
        time_slots = [['21:00', '22:00'],
                      ['20:00', '21:00'],
                      ['19:00', '20:00'],
                      ['18:00', '19:00'],
                      ['17:00', '18:00'],
                      ['16:00', '17:00'],
                      ['15:00', '16:00'],
                      ['14:00', '15:00'],
                      ['13:00', '14:00'],
                      ['12:00', '13:00'],
                      ['11:00', '12:00'],
                      ['10:00', '11:00'],
                      ['09:00', '10:00'],
                      ['08:00', '09:00'],
                      ['07:00', '08:00'], ]

        data_list = self.get_row_data("300000000$NLrsOYBdnaed", "BB08J2", "1-5")
        print(data_list)
        # 获取今天的网球场动态
        weekday = str(data_list[0]['textValues'][1]).split()[-1]
        date_str = str(data_list[0]['textValues'][1]).split()[0]
        court_free_time_infos = {}
        for data in data_list:
            if data['row'] >= 2:
                cell_data = data['textValues'][1]
                time_slot = time_slots[data['row'] - 2]
                if "已过期" in cell_data:
                    pass
                else:
                    court_name_list = []
                    for line in str(cell_data).splitlines():
                        if "香蜜体育 (6)" in line:
                            court_name_list.append("香蜜电话")
                        else:
                            court_name_list.append(line.split()[0])

                    for court_name in court_name_list:
                        if court_name in ["大沙河", "金地威新", "香蜜体育", "香蜜电话", "深圳湾"]:
                            court_key = f"【{court_name}】{weekday}({date_str})空场"
                            if court_free_time_infos.get(court_key):
                                court_free_time_infos[court_key].append(time_slot)
                            else:
                                court_free_time_infos[court_key] = [time_slot]
                        else:
                            pass
            else:
                pass

        # 获取明天的网球场动态
        weekday = str(data_list[0]['textValues'][2]).split()[-1]
        date_str = str(data_list[0]['textValues'][2]).split()[0]
        for data in data_list:
            if data['row'] >= 2:
                cell_data = data['textValues'][2]
                time_slot = time_slots[data['row'] - 2]
                if "已过期" in cell_data:
                    pass
                else:
                    court_name_list = []
                    for line in str(cell_data).splitlines():
                        if "香蜜体育 (6)" in line:
                            court_name_list.append("香蜜电话")
                        else:
                            court_name_list.append(line.split()[0])

                    for court_name in court_name_list:
                        if court_name in ["大沙河", "金地威新", "香蜜体育", "香蜜电话", "深圳湾"]:
                            court_key = f"【{court_name}】{weekday}({date_str})空场"
                            if court_free_time_infos.get(court_key):
                                court_free_time_infos[court_key].append(time_slot)
                            else:
                                court_free_time_infos[court_key] = [time_slot]
                        else:
                            pass
            else:
                pass

        up_for_send_msg_list = []
        for court_name, time_slot_list in court_free_time_infos.items():
            merged_time_slot_list = merge_time_ranges(time_slot_list)
            slot_msg_list = []
            for slot in merged_time_slot_list:
                slot_msg_list.append(f"{slot[0]}-{slot[1]}")
            slot_msg = "|".join(slot_msg_list)
            msg = f"{court_name}: {slot_msg}"
            up_for_send_msg_list.append(msg)
        return up_for_send_msg_list


def merge_time_ranges(data):
    """
    将时间段合并

    Args:
        data: 包含多个时间段的列表，每个时间段由开始时间和结束时间组成，格式为[['07:00', '08:00'], ['07:00', '09:00'], ...]

    Returns:
        合并后的时间段列表，每个时间段由开始时间和结束时间组成，格式为[['07:00', '09:00'], ['09:00', '16:00'], ...]
    """
    if not data:
        return data
    else:
        pass
    print(f"merging {data}")
    # 将时间段转换为分钟数，并按照开始时间排序
    data_in_minutes = sorted([(int(start[:2]) * 60 + int(start[3:]), int(end[:2]) * 60 + int(end[3:]))
                              for start, end in data])

    # 合并重叠的时间段
    merged_data = []
    start, end = data_in_minutes[0]
    for i in range(1, len(data_in_minutes)):
        next_start, next_end = data_in_minutes[i]
        if next_start <= end:
            end = max(end, next_end)
        else:
            merged_data.append((start, end))
            start, end = next_start, next_end
    merged_data.append((start, end))

    # 将分钟数转换为时间段
    result = [[f'{start // 60:02d}:{start % 60:02d}', f'{end // 60:02d}:{end % 60:02d}'] for start, end in merged_data]
    print(f"merged {result}")
    return result


# Testing
if __name__ == '__main__':
    docs = TencentDocs(token="")
