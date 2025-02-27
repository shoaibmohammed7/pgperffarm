import csv
import os
import psycopg2
import psycopg2.extras
import sys
import shutil

import folders
from utils.logging import log


class PostgresCollector(object):
    """
    collects basic PostgreSQL-level statistics (bgwriter, databases, tables,
    indexes)
    """

    def __init__(self, outdir, dbname):
        self._outdir = outdir
        self._dbname = dbname

    def start(self):
        log("saving postgres settings")
        try:

            conn = psycopg2.connect('host=%s dbname=%s' % (folders.SOCKET_PATH, self._dbname))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                'SELECT name, setting, source '
                'FROM pg_settings ORDER BY lower(name)'
            )

            fields = [desc[0] for desc in cur.description]

            with open(folders.LOG_PATH + '/postgres_settings.csv', 'w+') as file:

                r = csv.DictWriter(file, fields)
                r.writeheader()
                r.writerows(cur.fetchall())

            cur.execute('SELECT version()')

            with open(folders.LOG_PATH + '/compiler.txt', 'w+') as file:
                row = cur.fetchone()
                file.write(row['version'])

            conn.close()


        except Exception as e:
            with open(folders.LOG_PATH + '/pg_settings_log.txt', 'a+') as file:
                    file.write(str(e))
                    log("Error while extracting Postgres configuration, check logs.")
                    log("Removing data directory, please try again running the script.")

                    # remove datadir
                    if os.path.exists(folders.DATADIR_PATH):
                        shutil.rmtree(folders.DATADIR_PATH)
                        
                    sys.exit()

    def stop(self):
        pass

    def result(self):
        return {}
