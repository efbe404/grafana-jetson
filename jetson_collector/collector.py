#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2021 Stefan von Cavallar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import atexit
import argparse
from jtop import jtop, JtopException
from prometheus_client.core import InfoMetricFamily, GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server


class CustomCollector(object):
    def __init__(self):
        atexit.register(self.cleanup)
        self._jetson = jtop()
        self._jetson.start()

    def cleanup(self):
        print("Closing jetson-stats connection...")
        self._jetson.close()

    def collect(self):
        if self._jetson.ok():
            # print('emc: ', self._jetson.emc)
            # print('iram: ', self._jetson.iram)
            # print('mts: ', self._jetson.mts)
            # print(self._jetson.json())
            # print(self._jetson.board)
            print('gpu: ', self._jetson.gpu['gpu']['type'])
            data = self._jetson.json()
            #
            # Board info 
            #
            i = InfoMetricFamily('jetson_info_board', 'Board sys info', labels=['board_info'])
            i.add_metric(['info'], {
                'machine': self._jetson.board['platform']['Machine'], 
                'jetpack': self._jetson.board['hardware']['Jetpack'], 
                'l4t': self._jetson.board['hardware']['L4T']
                })
            yield i
            i = InfoMetricFamily('jetson_info_hardware', 'Board hardware info', labels=['board_hw'])                    
            i.add_metric(['hardware'], {
                'type': self._jetson.gpu['gpu']['type'],
                'codename': self._jetson.board['hardware'].get('Codename', 'Unknown'),
                'soc': self._jetson.board['hardware'].get('SoC', 'Unknown'),
                'module': self._jetson.board['hardware'].get('Module', 'Unknown'),
                'model': self._jetson.board['hardware'].get('Model', 'Unknown'),
                'p_number': self._jetson.board['hardware'].get('P-Number', 'Unknown'),
                'board_id': self._jetson.board['hardware'].get('BoardIDs', 'Unknown'),
                'cuda_arch_bin': self._jetson.board['hardware'].get('CUDA Arch BIN', 'Unknown'),
                'serial_number': self._jetson.board['hardware'].get('Serial Number', 'Unknown'),
                })
            yield i

            #
            # NV power mode
            #
            i = InfoMetricFamily('jetson_nvpmode', 'NV power mode', labels=['nvpmode'])
            i.add_metric(['mode'], {'mode': self._jetson.nvpmodel.name})
            yield i

            #
            # System uptime 
            #
            g = GaugeMetricFamily('jetson_uptime', 'System uptime', labels=['uptime'])
            days = self._jetson.uptime.days
            seconds = self._jetson.uptime.seconds
            hours = seconds//3600
            minutes = (seconds//60) % 60
            g.add_metric(['days'], days)
            g.add_metric(['hours'], hours)
            g.add_metric(['minutes'], minutes)
            yield g

            #
            # CPU usage 
            #

            print('cpu: ', self._jetson.cpu)

            g = GaugeMetricFamily(
                'jetson_usage_cpu',
                'CPU usage percentage',
                labels=['cpu']
            )

            cpu_list = self._jetson.cpu.get('cpu', [])

            for i, cpu in enumerate(cpu_list, start=1):
                usage = (
                    cpu.get('user', 0) +
                    cpu.get('nice', 0) +
                    cpu.get('system', 0)
                )

                g.add_metric(
                    [f'cpu_{i}'],
                    usage
            )

            yield g
            # 
            # GPU usage
            #
            g = GaugeMetricFamily('jetson_usage_gpu', 'GPU % schedutil', labels=['gpu'])
            print('gpu: ', self._jetson.gpu['gpu'])
            g.add_metric(['val'], self._jetson.gpu['gpu']['status']['load'])
            # g.add_metric(['frq'], self._jetson.gpu['frq'])
            # g.add_metric(['min_freq'], self._jetson.gpu['min_freq'])
            # g.add_metric(['max_freq'], self._jetson.gpu['max_freq'])
            yield g

            # 
            # RAM usage
            #
            print('ram: ', self._jetson.memory)
            g = GaugeMetricFamily('jetson_usage_ram', 'Memory usage', labels=['ram'])
            g.add_metric(['used'], self._jetson.memory['RAM']['used'])
            g.add_metric(['shared'], self._jetson.memory['RAM']['shared'])
            # g.add_metric(['total'], self._jetson.memory['tot'])
            # g.add_metric(['unit'], self._jetson.memory['unit'])
            yield g

            # 
            # Disk usage
            #
            g = GaugeMetricFamily('jetson_usage_disk', 'Disk space usage', labels=['disk'])
            g.add_metric(['used'], self._jetson.disk['used'])
            g.add_metric(['total'], self._jetson.disk['total'])
            g.add_metric(['available'], self._jetson.disk['available'])
            g.add_metric(['available_no_root'], self._jetson.disk['available_no_root'])
            yield g

            # 
            # Fan usage
            #
            print('fan: ', self._jetson.fan)
            g = GaugeMetricFamily('jetson_usage_fan', 'Fan usage', labels=['fan'])
            g.add_metric(['speed'], self._jetson.fan['tegra_pwmfan']['speed'][0])
            # g.add_metric(['speed'], self._jetson.fan['pwmfan']['speed'][0])
            # g.add_metric(['measure'], self._jetson.fan['measure'])
            # g.add_metric(['auto'], self._jetson.fan['auto'])
            # g.add_metric(['rpm'], self._jetson.fan['rpm'])
            # g.add_metric(['mode'], self._jetson.fan['mode'])
            yield g

            # 
            # Swapfile usage
            #
            g = GaugeMetricFamily('jetson_usage_swap', 'Swapfile usage', labels=['swap'])
            
            g.add_metric(['used'], self._jetson.memory["SWAP"]['used'])
            g.add_metric(['total'], self._jetson.memory["SWAP"]['tot'])
            # g.add_metric(['unit'], self._jetson.swap['unit'])
            # g.add_metric(['cached_size'], self._jetson.swap['cached']['size'])
            # g.add_metric(['cached_unit'], self._jetson.swap['cached']['unit'])
            yield g

            # 
            # Sensor temperatures
            #
            g = GaugeMetricFamily('jetson_temperatures', 'Sensor temperatures', labels=['temperature'])
            
            g = GaugeMetricFamily(
                'jetson_temperatures',
                'Sensor temperatures in Celsius',
                labels=['temperature']
            )

            temperature_data = self._jetson.temperature
            
            for sensor_name, sensor_data in temperature_data.items():
                if isinstance(sensor_data, dict):
                   temperature = sensor_data.get('temp', 0)
                else:
                   temperature = sensor_data

                g.add_metric(
                    [sensor_name.lower()],
                    temperature
                )
            yield g

            # 
            # Power
            #
            print('power: ', self._jetson.power)

            g = GaugeMetricFamily(
                'jetson_usage_power',
                'Jetson power consumption in mW',
                labels=['rail']
            )

            power_data = self._jetson.power
            # Individual power rails
            for rail_name, rail in power_data.get('rail', {}).items():
                g.add_metric(
                    [rail_name],
                    rail.get('power', 0)
                )
            # Total power
            total = power_data.get('tot', {})
            g.add_metric(
                ['total'],
                total.get('power', 0)
            )

            yield g


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=3030, help='Metrics collector port number')

    args = parser.parse_args()

    start_http_server(args.port)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
