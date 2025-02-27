import os.path
import psutil
import json
from cpuinfo import get_cpu_info

import folders
from utils.logging import log
from utils.misc import run_cmd


class SystemCollector(object):
	'Collect various Unix-specific statistics (cpuinfo, mounts)'

	def __init__(self, outdir):
		self._outdir = outdir

		# hard code all possible places a packager might install sysctl.
		self._env = os.environ
		self._env['PATH'] = ':'.join(['/usr/sbin/', '/sbin/', self._env['PATH']])

	def start(self):
		pass

	def stop(self):
		pass

	def result(self):
		'build the results'

		r = {}
		self._collect_sysctl()
		r.update(self._collect_system_info())

		return r

	def _collect_sysctl(self):
		'collect kernel configuration'

		log("collecting sysctl")
		r = run_cmd(['sysctl', '-a'], env=self._env)

		sysctl = r[1].splitlines()
		sysctl_json = {}

		uname = os.popen("uname").readlines()[0].split()[0]

		for item in sysctl:
			if ("permission denied" not in item.decode("utf-8")) and ("reading key" not in item.decode("utf-8")):
				if uname == 'Linux':
					key, value = item.decode("utf-8").split('=', 1)
				if uname == 'Darwin':
					key, value = item.decode("utf-8").split(':', 1)
				sysctl_json.update({key.rstrip(): value.rstrip().lstrip()})

		with open(folders.LOG_PATH + '/sysctl_log.json', 'w+') as file:
			file.write(json.dumps(sysctl_json, indent=4))


	def _collect_system_info(self):
		'collect cpuinfo, meminfo, mounts'

		log("Collecting system info")

		system = {}
		system['cpu'] = {}
		system['memory'] = {}
		system['disk'] = {}

		system['cpu']['information'] = get_cpu_info()
		system['cpu']['number'] = psutil.cpu_count()

		system['memory']['virtual'] = psutil.virtual_memory()
		system['memory']['swap'] = psutil.swap_memory()
		system['memory']['mounts'] = psutil.disk_partitions()

		system['disk']['usage'] = psutil.disk_usage('/')

		return system
