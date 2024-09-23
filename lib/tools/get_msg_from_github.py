#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/9/21 22:13
@Author  : claude
@File    : get_msg_from_github.py
@Software: PyCharm
"""

import requests
import json
from datetime import datetime, timedelta


def get_data_from_url(url):
    response = requests.get(url)
    data_text = response.text
    data = json.loads(data_text)
    return data


def parse_time(time_str):
    return datetime.strptime(time_str, '%H:%M')


def parse_time_range(time_range):
    start_str, end_str = time_range.split('-')
    start_time = parse_time(start_str)
    end_time = parse_time(end_str)
    # 处理跨午夜的时间段
    if end_time <= start_time:
        end_time += timedelta(days=1)
    return start_time, end_time


def check_criteria(time_range, status):
    if '可预订' == status:
        start_time, end_time = parse_time_range(time_range)
        if start_time.hour >= 18:
            return True
    return False


def check_criteria_for_weekend(time_range, status):
    if '可预订' == status:
        start_time, end_time = parse_time_range(time_range)
        if start_time.hour >= 15:
            return True
    return False


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


def is_time_difference_greater_than_one_hour(time_intervals):
    for interval in time_intervals:
        start_time_str, end_time_str = interval
        start_time = datetime.strptime(start_time_str, '%H:%M')
        end_time = datetime.strptime(end_time_str, '%H:%M')

        # 计算时间差
        time_difference = end_time - start_time

        # 将时间差转换为秒，再转换为小时
        time_difference_in_hours = time_difference.total_seconds() / 3600

        # 判断时间差是否大于等于1小时
        if time_difference_in_hours >= 1:
            return True
    return False


def filter_slots(data):
    notifications = []
    for location in data:
        for date in data[location]:
            for court in data[location][date]:
                if "墙" in court:
                    continue
                print(court)
                slot_list = []
                for slot in data[location][date][court]:
                    time_range = slot['time']
                    status = slot['status']
                    if "星期六" in date or "星期日" in date:
                        if check_criteria_for_weekend(time_range, status):
                            slot_list.append([str(time_range).split('-')[0], str(time_range).split('-')[1]])
                    else:
                        if check_criteria(time_range, status):
                            slot_list.append([str(time_range).split('-')[0], str(time_range).split('-')[1]])

                if slot_list:
                    merged_slot_list = merge_time_ranges(slot_list)
                    if is_time_difference_greater_than_one_hour(merged_slot_list):
                        for merged_slot in merged_slot_list:
                            if merged_slot[0] != "22:00":
                                merged_slot_str = "-".join(merged_slot)
                                notification = f"【{location}-{court.replace('网球场', '')}】{date}空场: {merged_slot_str}"
                                notifications.append(notification)
                            else:
                                pass
                    else:
                        pass
    return list(set(notifications))


def get_push_msg_from_git():
    try:
        # 从链接读取数据
        url = 'https://raw.githubusercontent.com/claude89757/tennis_helper/refs/heads/main/isz_data_infos.json'
        data = get_data_from_url(url)

        # 过滤并生成通知列表
        notifications = filter_slots(data)

        # 输出结果
        print("data from git================")
        for n in notifications:
            print(n)
        print("data from git================")

        return notifications
    except Exception as error:
        print(error)
        return []
