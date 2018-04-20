#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_module_jq.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from wishbone.event import Event, Metric
from wishbone_decode_checkresults import CheckResults
from wishbone.actor import ActorConfig
from wishbone.utils.test import getter
import re
from gevent import sleep

host_checkresult = '''
type=passive
host_name=host-10-67-15-190.net-10-67-0-0.tt3.com
core_start_time=1523547320.0
start_time=1523547260.962571
finish_time=1523547260.965425
return_code=0
exited_ok=1
source=Mod-Gearman Worker @ worker-ams3z1-1.umi.tt3.com
output=OK - 10.67.15.190: rta 0.178ms, lost 0%|rta=0.178ms;3000.000;5000.000;0; pl=0%;80;100;; \n
'''

service_checkresult = '''
type=passive
host_name=prod-motown2-traffic-104.traffic.tt3.com
core_start_time=1523547484.0
start_time=1523547184.983180
finish_time=1523547185.367062
return_code=0
exited_ok=1
source=Mod-Gearman Worker @ worker-ams3z1-2.umi.tt3.com
service_description=CPU Load
output=OK - load average: 10.82, 10.28, 10.70|load1=10.820;30.000;45.000;0; load5=10.280;30.000;45.000;0; load15=10.700;30.000;45.000;0; \n
'''


def test_module_decode_host_checkresult():

    data =  re.sub(' {2,4}', "\t", host_checkresult)
    actor_config = ActorConfig('pd', 100, 1, {}, "")
    pd = CheckResult(actor_config)

    pd.pool.queue.inbox.disableFallThrough()
    pd.pool.queue.outbox.disableFallThrough()
    pd.start()

    e = Event(data)

    pd.pool.queue.inbox.put(e)
    sleep(1)
    assert pd.pool.queue.outbox.size() == 2

    one = getter(pd.pool.queue.outbox).get()
    assert isinstance(one, Metric)
    assert one.name == 'hostcheck.rta'
    assert one.value == '0.751'

    two = getter(pd.pool.queue.outbox).get()
    assert isinstance(two, Metric)
    assert two.name == 'hostcheck.pl'
    assert two.value == '0'


def test_module_decode_service_checkresult():

    data =  re.sub(' {2,4}', "\t", service_checkresult)
    actor_config = ActorConfig('pd', 100, 1, {}, "")
    pd = CheckResult(actor_config)

    pd.pool.queue.inbox.disableFallThrough()
    pd.pool.queue.outbox.disableFallThrough()
    pd.start()

    e = Event(data)

    pd.pool.queue.inbox.put(e)
    sleep(1)
    assert pd.pool.queue.outbox.size() == 8

    one = getter(pd.pool.queue.outbox).get()
    assert isinstance(one, Metric)
    assert one.name == 'service1.time'
    assert one.value == '0.02'

    two = getter(pd.pool.queue.outbox).get()
    assert isinstance(two, Metric)
    assert two.name == 'service1.cat'
    assert two.value == '20'
