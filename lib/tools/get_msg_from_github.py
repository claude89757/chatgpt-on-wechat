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
    # Handle time ranges that cross midnight
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
    Merge overlapping time ranges.

    Args:
        data: A list of time ranges, each represented as [start_time, end_time] strings.

    Returns:
        A list of merged time ranges, each represented as [start_time, end_time] strings.
    """
    if not data:
        return data
    # Convert time ranges to minutes and sort by start time
    data_in_minutes = sorted([(int(start[:2]) * 60 + int(start[3:]), int(end[:2]) * 60 + int(end[3:]))
                              for start, end in data])

    # Merge overlapping time ranges
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

    # Convert minutes back to time strings
    result = [[f'{start // 60:02d}:{start % 60:02d}', f'{end // 60:02d}:{end % 60:02d}'] for start, end in merged_data]
    return result


def filter_intervals_shorter_than_one_hour(time_intervals):
    """
    Filter out time intervals shorter than 1 hour.

    Args:
        time_intervals: A list of time intervals, each represented as [start_time_str, end_time_str].

    Returns:
        A list of time intervals that are at least 1 hour long.
    """
    filtered_intervals = []
    for interval in time_intervals:
        start_time_str, end_time_str = interval
        start_time = datetime.strptime(start_time_str, '%H:%M')
        end_time = datetime.strptime(end_time_str, '%H:%M')
        if end_time < start_time:
            end_time += timedelta(days=1)
        time_difference = end_time - start_time
        time_difference_in_hours = time_difference.total_seconds() / 3600
        if time_difference_in_hours >= 1:
            filtered_intervals.append(interval)
    return filtered_intervals


def filter_slots(data):
    notifications = []
    for location in data:
        location_url = data[location]['url']
        court_infos = data[location]['court_infos']

        messages = []
        for date in sorted(court_infos.keys()):
            court_free_slot_dict = {}  # Court number -> list of time slots
            for court in court_infos[date]:
                if "墙" in court:
                    continue
                slot_list = []
                for slot in court_infos[date][court]:
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
                    merged_slot_list = filter_intervals_shorter_than_one_hour(merged_slot_list)

                    if merged_slot_list:
                        # Collect the time slots per court
                        slot_strings = ['-'.join(slot) for slot in merged_slot_list if slot[0] != "22:00"]
                        if slot_strings:
                            court_number = court.replace('网球场', '').strip()
                            court_free_slot_dict[court_number] = slot_strings

            if court_free_slot_dict:
                # Build the message for this date
                # Format: 【Location】Date CourtNumbers: TimeSlots
                court_numbers = '|'.join(sorted(list(set(court_free_slot_dict.keys()))))
                # Combine all time slots for all courts (union)
                all_time_slots = set()
                for slots in court_free_slot_dict.values():
                    all_time_slots.update(slots)
                time_slots_str = ','.join(sorted(all_time_slots))
                # Build the message line
                message_line = f"【{location}】{date} {court_numbers}: {time_slots_str}"
                messages.append(message_line)

        if messages:
            # Combine messages for the location
            notification = '\n'.join(messages) + f"\n预定链接: {location_url}"
            notifications.append(notification)

    return notifications


def get_push_msg_from_git():
    try:
        # Read data from the URL
        print("start get data from git")
        url = 'https://raw.githubusercontent.com/claude89757/tennis_data/refs/heads/main/isz_data_infos.json'
        data = get_data_from_url(url)

        print("raw data from git================")
        print(len(data))
        print("raw data from git================")

        # Filter and generate notifications
        notifications = filter_slots(data)

        # Output the results
        print("data from git================")
        for n in notifications:
            print(n)
        print("data from git================")

        return notifications
    except Exception as error:
        print(error)
        return []


# testing
if __name__ == '__main__':
    get_push_msg_from_git()
