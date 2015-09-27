#!/usr/bin/env python

from krpc_utils import Vessel, connect

conn = connect()

v = Vessel(num_stages=2, conn=conn)
v.launch(init_speed_max=100, termv_accel=1.01, termv_decel=0.995, termv_min_throttle=0.4, alt_max=30000)
