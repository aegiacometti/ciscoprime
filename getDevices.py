#!/usr/bin/env python3

# Script to connect to a Cisco Prime Infrastructre and extract invetory.
# Complete your server and user credentials in credentials.py file
# 1.- to screen AEPg, EPG, provider/consumer, contract
# 2.- to screen Contract, Subject, Filter, Filter Name, ports, etc
# 3.- export to excel format the full combination of: AEPg, EPG, provider/consumer,
#     contract, subject, filter and filter name, ports, etc

import requests
from requests.auth import HTTPBasicAuth
import json
from credentials import *
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pprint import pprint


def query_devices_print(first_result):
    devices_ok_count = 0
    devices_fail_count = 0

    url = "https://" + URL + "/webacs/api/v3/data/Devices.json?.full=true&.sort=deviceName&.firstResult=" +\
          str(first_result)

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload, verify=False,
                                auth=HTTPBasicAuth(USERID, PASSWORD))

    # print(response.text.encode('utf8'))
    devices = json.loads(response.text)

    for device in devices['queryResponse']['entity']:
        if device['devicesDTO']['adminStatus'] == 'Un-Managed':
            device_name = 'Un-Managed'
            device_type = 'Un-Managed'
            product_family = 'Un-Managed'
            devices_fail_count += 1
        else:
            device_name = device['devicesDTO']['deviceName'].lower()
            device_type = device['devicesDTO']['deviceType']
            product_family = device['devicesDTO']['productFamily']
            devices_ok_count += 1

        if 'Nexus' in device_type:
            software_type = 'NXOS'
        elif 'ASA' in device_type:
            software_type = 'ASA'
        elif 'Routers' in product_family:
            software_type = 'IOS'
        elif 'Unsupported' in product_family:
            software_type = 'Unsupported'
        elif 'Catalyst' in device_type:
            software_type = 'IOS'
        elif 'Wireless' in product_family:
            software_type = 'AIREOS'
        elif 'Un-Managed' in device_name:
            software_type = 'Un-Managed'
        elif 'softwareType' in device['devicesDTO']:
            software_type = device['devicesDTO']['softwareType']
        elif 'softwareVersion' in device['devicesDTO']:
            software_type = device['devicesDTO']['softwareVersion']
        elif 'softwareVersion' in device['devicesDTO']:
            software_type = 'Unknown'

        ip_address = device['devicesDTO']['ipAddress']
        reachability = device['devicesDTO']['reachability']
        admin_status = device['devicesDTO']['adminStatus']
        management_status = device['devicesDTO']['managementStatus']

        print(f'{device_name} - {ip_address} - {reachability} - {admin_status} - {software_type}')
        print(f'{product_family} - {device_type} - {management_status}')
        print('============================================================')

    return devices_ok_count, devices_fail_count


def query_devices_json(first_result, devices_list_dict):
    devices_ok_count = 0
    devices_fail_count = 0

    url = "https://" + URL + "/webacs/api/v3/data/Devices.json?.full=true&.sort=deviceName&.firstResult=" +\
          str(first_result)

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload, verify=False,
                                auth=HTTPBasicAuth(USERID, PASSWORD))

    # print(response.text.encode('utf8'))
    devices = json.loads(response.text)
    device_dict = {}

    for device in devices['queryResponse']['entity']:
        device_dict = {}
        if device['devicesDTO']['adminStatus'] == 'Un-Managed':
            device_dict['device_name'] = 'Un-Managed'
            device_dict['device_type'] = 'Un-Managed'
            device_dict['product_family'] = 'Un-Managed'
            devices_fail_count += 1
        else:
            device_dict['device_name'] = device['devicesDTO']['deviceName'].lower()
            device_dict['device_type'] = device['devicesDTO']['deviceType']
            device_dict['product_family'] = device['devicesDTO']['productFamily']
            devices_ok_count += 1

        try:
            if 'Nexus' in device['devicesDTO']['deviceType']:
                device_dict['software_type'] = 'NXOS'
            elif 'ASA' in device['devicesDTO']['deviceType']:
                device_dict['software_type'] = 'ASA'
            elif 'Routers' in device['devicesDTO']['productFamily']:
                device_dict['software_type'] = 'IOS'
            elif 'Unsupported' in device['devicesDTO']['productFamily']:
                device_dict['software_type'] = 'Unsupported'
            elif 'Catalyst' in device['devicesDTO']['deviceType']:
                device_dict['software_type'] = 'IOS'
            elif 'Wireless' in device['devicesDTO']['productFamily']:
                device_dict['software_type'] = 'AIREOS'
            elif 'Un-Managed' in device['devicesDTO']['deviceName']:
                device_dict['software_type'] = 'Un-Managed'
            else:
                device_dict['software_type'] = device['devicesDTO']['softwareType']
        except KeyError:
            device_dict['software_type'] = 'Unknown'

        device_dict['ip_address'] = device['devicesDTO']['ipAddress']
        device_dict['reachability'] = device['devicesDTO']['reachability']
        device_dict['admin_status'] = device['devicesDTO']['adminStatus']
        device_dict['management_status'] = device['devicesDTO']['managementStatus']

        devices_list_dict.append(device_dict)

    return devices_ok_count, devices_fail_count


def get_pages(json_format):
    f_r = 0
    device_count = 100
    total_ok = 0
    total_fail = 0
    devices_list_dict = []
    page_num = 1
    while device_count == 100:
        if json_format:
            print(f'Quering page {page_num}')
            page_num += 1
            to, tf = query_devices_json(f_r, devices_list_dict)
        else:
            to, tf = query_devices_print(f_r)
        total_ok += to
        total_fail += tf
        device_count = to + tf
        f_r = f_r + 100

    if json_format:
        return devices_list_dict, total_ok, total_fail
    else:
        return total_ok, total_fail


def print_devices():
    d_ok, d_fail = get_pages(json_format=False)
    print(f'Total devices: {d_ok + d_fail}\nFailed: {d_fail}')


def get_devices_dict():
    dev_dict_list, d_ok, d_fail = get_pages(json_format=True)
    print(f'Total devices: {d_ok + d_fail}\nFailed: {d_fail}')
    return dev_dict_list, d_ok, d_fail


def print_devices_in_ansible_format():
    device_groups = {'router': [], 'wireless': [], 'switch': [], 'voice': []}

    dev_dict_list, _, _ = get_pages(json_format=True)
    for device in dev_dict_list:
        if device['product_family'] == 'Routers':
            device_groups['router'].append(device)
        elif device['product_family'] == 'Switches and Hubs':
            device_groups['switch'].append(device)
        elif device['product_family'] == 'Wireless Controller' or device['product_family'] == 'Autonomous AP':
            device_groups['wireless'].append(device)
        elif device['product_family'] == 'Voice and Telephony':
            device_groups['voice'].append(device)

    for group in device_groups.keys():
        print(f'\n[{group}]')
        for device in device_groups[group]:
            devicen = device['device_name'].split('.')[0]
            ipa = device['ip_address']
            os = device['software_type'].lower()
            if not os.startswith('un'):
                if os != 'asa':
                    print(f'{devicen} ansible_host={ipa} ansible_network_os={os} platform={os}')
                elif os == 'asa':
                    print(f'{devicen} ansible_host={ipa} ansible_network_os={os} ansible_become=yes ansible_become_method=enable platform={os}')


if __name__ == '__main__':
    option = input('1.- print user friendly format to screen\n'
                   '2.- print dictionary format to screen\n'
                   '3.- print in Ansible format\n'
                   'Select option: ')
    if option == '1':
        print_devices()
    elif option == '2':
        devices_dict, _, _ = get_devices_dict()
        pprint(devices_dict)
    elif option == '3':
        print_devices_in_ansible_format()
    else:
        print('Incorrect option')
