import os
from subprocess import call, STDOUT
from tempfile import TemporaryFile

import folders
from utils.logging import log
from utils.misc import run_cmd


class PgCluster(object):
    'basic manipulation of postgres cluster (init, start, stop, destroy)'

    def __init__(self, outdir, bin_path, data_path):
        self._outdir = outdir
        self._bin = bin_path
        self._data = data_path

        self._env = os.environ
        self._env['PATH'] = ':'.join([bin_path, self._env['PATH']])
 
        self._env['PGDATABASE'] = "postgres"
        self._env["LD_LIBRARY_PATH"] = os.path.join(folders.INSTALL_PATH, 'lib')

        self._options = ""

    def _initdb(self):
        'initialize the data directory'

        with TemporaryFile() as strout:
            log("initializing cluster into '%s'" % (self._data,))
            r = call(['pg_ctl', '-D', self._data, 'init'], env=self._env,
                 stdout=strout, stderr=STDOUT)

    def _configure(self, config):
        'build options list to use with pg_ctl'

        for k in config:
            self._options += ''.join([" -c ", k, "='", str(config[k]), "'"])

    def _destroy(self):
        """
        forced cleanup of possibly existing cluster processes and data
        directory
        """
        with TemporaryFile() as strout:
            log("killing postgres processes")
            try: 
                pidfile = open(''.join([self._outdir, '/postmaster.pid']), 'r')
                pid = pidfile.readline().strip()
                run_cmd(['kill', '-9', pid])
                log("found postmaster.pid")
            except FileNotFoundError:
                log("postmaster.pid not found")


    def start(self, config, destroy=True):
        'init, configure and start the cluster'

        # cleanup any previous cluster running, remove data dir if it exists
        if destroy:
            self._destroy()

        self._initdb()
        self._configure(config)

        # add pg_stat_statements to postgresql.conf
        with open(''.join([self._data, '/postgresql.conf']), 'a') as file:
            file.write("shared_preload_libraries = 'pg_stat_statements'")

        with TemporaryFile() as strout:
            log("starting cluster in '%s' using '%s' binaries" %
                (self._data, self._bin))

            cmd = ['pg_ctl', '-D', self._data, '-l',
                   ''.join([folders.LOG_PATH, '/pg_ctl.log']), '-w']
            if len(self._options) > 0:
                cmd.extend(['-o', self._options])
            cmd.append('start')
            call(cmd, env=self._env, stdout=strout, stderr=STDOUT)

    def stop(self, destroy=True):
        'stop the cluster'

        with TemporaryFile() as strout:
            log("stopping cluster in '%s' using '%s' binaries" %
                (self._data, self._bin))
            call(['pg_ctl', '-D', self._data, '-w', '-t', '60', 'stop'],
                 env=self._env, stdout=strout, stderr=STDOUT)

        # kill any remaining processes, remove the data dir
        if destroy:
            self._destroy()
