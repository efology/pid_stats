from influxdb import InfluxDBClient
from datetime import datetime
from os import environ as env
import gevent
import socket
import configparser
import psstats as ps
from gevent import monkey; monkey.patch_all()

class Reporter():

    def __init__(self, configfile):
        print("reporter!")
        conf = configparser.ConfigParser()
        conf.read(configfile)
        self._client = InfluxDBClient(
            conf.get('influxdb', 'host'),
            conf.getint('influxdb', 'port'),
            conf.get('influxdb', 'username'),
            conf.get('influxdb', 'password'),
            conf.get('influxdb', 'db'))  # yapf: disable
        self._client.create_database(conf.get('influxdb', 'db'))
        self._hostname = socket.gethostname()
        self._running = True
        self._last_timestamp = 0.0
        self._write_period = conf.getfloat('influxdb', 'write_period_s')
        self._user_count = 0
        self._ps = ps.PSStats()
        print("constructor before run")
        self._background = gevent.spawn(self._run)
        print("constructor after run")
        

    def _run(self):
        print("reporter run()")
        while self._running:
            self._write_stats()
            gevent.sleep(self._write_period)


    def _write_stats(self):
        print("reporter write stats")
        influx_points = []
        influx_points.extend(self._ps_to_points())
        if not self._client.write_points(influx_points):
            print(f"could not write stats: {influx_points}")


    def _ps_to_points(self):
        points = []
        cpu = self._point_template("pid_cpu")
        cpu["fields"].update({"value": self._ps.get_cpu_percent()})
        points.append(cpu)

        mem = self._point_template("pid_memory")
        mtuple = self._ps.get_memory_usage()
        for k, v in mtuple._asdict().items():
            mem["fields"].update({k: v})
        points.append(mem)

        mem_percentage = self._point_template("pid_memory_percentage")
        mem_percentage["fields"].update({"value": self._ps.get_memory_percentage()})
        points.append(mem_percentage)

        iodict = self._ps.get_net_io_counters()
        for k, v in iodict.items():
            io = self._point_template("pid_io")
            io["tags"].update({"interface": k})
            for field, value in v.items():
                io["fields"].update({field: value})
            points.append(io)
        return points


    def _point_template(self, measurement):
        p = {
            "measurement": measurement,
            "tags": {
                "host": self._hostname,
                "pid": self._ps.get_pid()
            },
            "time": datetime.utcnow().isoformat(),
            "fields": {}
        }
        return p


    # maybe use this dunno
    def quitting(self):
        print("stopping")
        self._running = False
