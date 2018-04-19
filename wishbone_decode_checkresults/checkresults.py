#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       perfdata.py
#
#       Copyright 2018 Marco Musso <github@marcomusso.it>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

from wishbone import Actor
from wishbone.event import Metric
import re
import sys


class CheckResults(Actor):

    '''**Converts Nagios check_results to the internal metric format.**

    Converts the Nagios check_results into the internal Wishbone metric
    format.


    Parameters:

        - sanitize_hostname(bool)(False)
           |  If True converts "." to "_".
           |  Might be practical when FQDN hostnames mess up the namespace
           |  such as Graphite.

        - source(str)("@data")
           |  The field containing the perdata.

        - destination(str)("@data")
           |  The field to store the Metric data.


    Queues:

        - inbox:    Incoming events

        - outbox:   Outgoing events
    '''

    def __init__(self, actor_config, sanitize_hostname=False, source="@data", destination="@data"):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")
        self.registerConsumer(self.consume, "inbox")

        self.regex = re.compile('(.*?)(\D+)$')

    def preHook(self):
        if self.kwargs.sanitize_hostname:
            self.replacePeriod = self.__doReplacePeriod
        else:
            self.replacePeriod = self.__doNoReplacePeriod

    def consume(self, event):
        try:
            for metric in self.decodeMetrics(event.get(self.kwargs.source)):
                e = event.clone()
                e.set(metric, self.kwargs.destination)
                self.submit(e, self.pool.queue.outbox)
        except Exception as err:
            raise Exception('Malformatted checkresults data received. Reason: %s Line: %s' % (err, sys.exc_traceback.tb_lineno))

    def decodeMetrics(self, data):

        d = self.__chopStringDict(data)

        for metric in re.findall('(\w*?\'*=\d*(?:\.\d*)?(?:s|us|ms|%|B|MB|KB|TB|c)?)', d["perfdata"]):
            # name and value
            (metric_name, metric_value) = metric.split('=')
            metric_name = self.__filter(metric_name)
            # metric time
            metric_timet = d["timet"]

            # metric unit
            re_unit = re.search("\D+$", metric_value)
            if re_unit is None:
                metric_unit = ''
            else:
                metric_unit = re_unit.group(0)
            metric_value = metric_value.rstrip(metric_unit)

            # tags
            tags = [d["type"], d["checkcommand"]]

            yield Metric(metric_timet, "nagios", d["hostname"], "%s.%s" % (d["name"], metric_name), metric_value, metric_unit, tuple(tags))

    def __chopStringDict(self, data):
        '''Returns a dictionary of the provided raw service/host check string.'''

        r = {}
        d = data.split('\t')

        for item in d:
            item_parts = item.split('::')
            if len(item_parts) == 2:
                (name, value) = item_parts
            else:
                name = item_parts[0]
                value = item_parts[1]

            name = self.__filter(name)
            r[name] = value

        if "hostperfdata" in r:
            r["type"] = "hostcheck"
            r["perfdata"] = r["hostperfdata"]
            r["checkcommand"] = re.search("(.*?)!\(?.*", r["hostcheckcommand"]).group(1)
            r["name"] = "hostcheck"
        else:
            r["type"] = "servicecheck"
            r["perfdata"] = r["serviceperfdata"]
            r["checkcommand"] = re.search("((.*)(?=\!)|(.*))", r["servicecheckcommand"]).group(1)
            r["name"] = self.__filter(r["servicedesc"])

        r["hostname"] = self.replacePeriod(self.__filter(r["hostname"]))

        return r

    def __filter(self, name):
        '''Filter out problematic characters.

        This should become a separate module allowing the user to define filter rules
        from a bootstrap file and most likely become a separate module.
        '''

        name = name.replace("'", '')
        name = name.replace('"', '')
        name = name.replace('!(null)', '')
        name = name.replace(" ", "_")
        name = name.replace("/", "_")
        name = name.replace(".", "_")
        return name.lower()

    def __doReplacePeriod(self, data):
        return data.replace(".", "_")

    def __doNoReplacePeriod(self, data):
        return data
