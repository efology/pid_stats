import psutil
import time
import numpy


class PSStats:
    def __init__(self):
        self.p = psutil.Process()
        self.net_io_cache = {"timestamp": time.monotonic(), "net_io": psutil.net_io_counters(pernic=True)}

    def get_cpu_percent(self):
        return self.p.cpu_percent(interval=None)

    def get_memory_usage(self):
        return self.p.memory_full_info()

    def get_memory_percentage(self):
        return self.p.memory_percent()

    def get_net_io_counters(self):
        result = {}
        current_timestamp = time.monotonic()
        interval_length = current_timestamp - self.net_io_cache["timestamp"]
        net_io_current = psutil.net_io_counters(pernic=True)
        for key, tup in net_io_current.items():
            result_if = {key: self._diff_tuples(interval_length, tup, self.net_io_cache["net_io"][key])}
            result.update(result_if)
        self.net_io_cache["timestamp"] = current_timestamp
        self.net_io_cache["net_io"] = net_io_current
        return result

    @staticmethod
    def _diff_tuples(interval, latest, old):
        diff_array = (numpy.array(latest) - numpy.array(old))
        diff = {}
        for index, value in enumerate(diff_array):
            diff.update({old._fields[index]: int(value / interval)})
        return diff

    def get_pid(self):
        return self.p.pid
