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

        yield Metric(d["start_time"], "nagios", d["host_name"], "%s.%s" % (d["service_description"], 'return_code'), d["return_code"], '', tuple([]))

    def __chopStringDict(self, data):
        '''Returns a dictionary of the provided raw service/host check string.'''

        r = {}
        d = data.split('\n')

        for item in d:
            item_parts = item.split('=')
            if len(item_parts) == 2:
                (name, value) = item_parts
            else:
                name = item_parts[0]
                value = item_parts[1]

            name = self.__filter(name)
            r[name] = value

        # if service_description is present then it's a service result otherwise host result
        if "service_description" in r:
            r["service_description"] = self.replacePeriod(self.__filter(r["service_description"]))
        r["host_name"] = self.replacePeriod(self.__filter(r["host_name"]))

        return r

    def __filter(self, name):
        '''Filter out problematic characters and turn it to lowercase.'''

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
