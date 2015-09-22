#!/usr/bin/env python
''' 
Vessel wrapper

Reference:
http://djungelorm.github.io/krpc/docs/tutorials/launch-into-orbit.html
https://www.reddit.com/r/KerbalAcademy/comments/3lmc75/most_efficient_launch_profile_to_reach_orbit
'''

import os
import sys
import time
import krpc

class Vessel(object):

    def __init__(self, conn=None, vessel=None, num_stages=1):
        self.conn = conn
        self.last_turn_offset = 0
        self.stage = 0
        self.num_stages = num_stages
        if vessel:
            self.vessel = vessel
        elif conn:
            self.vessel = self.conn.space_center.active_vessel
        else:
            self.vessel = None
        if self.vessel:
            self.initialize_vessel()
        else:
            self.stream = None
            self.rframe = None
            self.stages = None

    def initialize_vessel(self):
        self.stages = [
            self.vessel.resources_in_decouple_stage(stage=x, cumulative=False)
            for x in range(0, self.num_stages)
        ]
        self.rframe = self.vessel.orbit.body.reference_frame
        self.stream = {
            'ut': self.conn.add_stream(
                getattr, self.conn.space_center, 'ut'),
            'alt': self.conn.add_stream(
                getattr, self.vessel.flight(self.rframe), 'surface_altitude'),
            'speed': self.conn.add_stream(
                getattr, self.vessel.flight(self.rframe), 'speed'),
            'vspeed': self.conn.add_stream(
                getattr, self.vessel.flight(self.rframe), 'vertical_speed'),
            'hspeed': self.conn.add_stream(
                getattr, self.vessel.flight(self.rframe), 'horizontal_speed'),
            'termv': self.conn.add_stream(
                getattr, self.vessel.flight(self.rframe), 'terminal_velocity'),
            'apo': self.conn.add_stream(
                getattr, self.vessel.orbit, 'apoapsis_altitude'),
            'apo_time': self.conn.add_stream(
                getattr, self.vessel.orbit, 'time_to_apoapsis'),
            'peri': self.conn.add_stream(
                getattr, self.vessel.orbit, 'periapsis_altitude'),
            'peri_time': self.conn.add_stream(
                getattr, self.vessel.orbit, 'time_to_periapsis'),
            'ecc': self.conn.add_stream(
                getattr, self.vessel.orbit, 'eccentricity'),
            'liquid': [
                self.conn.add_stream(self.stages[i].amount, 'LiquidFuel')
                for i in range(0, self.num_stages)
            ][::-1],
            'solid': [
                self.conn.add_stream(self.stages[i].amount, 'SolidFuel')
                for i in range(0, self.num_stages)
            ][::-1],
        }
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.target_pitch_and_heading(90, 90)
        self.vessel.auto_pilot.sas = True

    def __getattr__(self, attr):
        if attr in self.stream:
            return self.stream[attr]

    def stage_liquid(self):
        return self.liquid[self.stage]()

    def stage_solid(self):
        return self.solid[self.stage]()

    def stage_fuel(self):
        return self.stage_liquid() + self.stage_solid()

    def throttle(self, t=None):
        if t is None:
            return self.vessel.control.throttle
        self.vessel.control.throttle = min(max(t, 0.0), 1.0)

    def turn(self, turn_offset):
        if abs(turn_offset - self.last_turn_offset) > 0.5:
            self.last_turn_offset = turn_offset
            self.vessel.auto_pilot.target_pitch_and_heading(
                90 - turn_offset, 90)

    def run_behavior(self, turn_f=None, throttle_f=None, **kwargs):
        limits = {}
        for kwarg, func in kwargs.items():
            if not kwarg.endswith('_min') and not kwarg.endswith('_max'):
                limits[kwarg] = [func]
        for kwarg in limits:
            limits[kwarg] += [
                (kwargs.get(kwarg + '_min'),
                kwargs.get(kwarg + '_max'))
            ]
        while True:
            if turn_f is not None:
                turn_f(self)
            if throttle_f is not None:
                throttle_f(self)
            done = False
            for kwarg, vals in limits.items():
                func, lminmax = vals
                lmin, lmax = lminmax
                if lmin is not None and func() < lmin:
                    done = True
                    break
                if lmax is not None and func() > lmax:
                    done = True
                    break
            if done:
                break

    def spacebar(self):
        self.stage += 1
        self.vessel.control.activate_next_stage()

    @classmethod
    def static_angle_func(cls, val):
        def angle0(vessel):
            vessel.turn(val)
        return angle0

    def gradual_turn_func(self, alt_max=30000, turn_max=90):
        init_alt = self.alt()
        alt_diff = float(alt_max - init_alt)
        def turn_f(vessel):
            ratio = (vessel.alt() - init_alt) / alt_diff
            vessel.turn(turn_max * ratio)
        return turn_f

    def termv_thrust_func(self,
            accel=1.02, decel=0.99, min_throttle=0.1, autostage=True):
        def throttle_f(vessel):
            # keep throttle below terminal velocity
            if autostage:
                vessel.check_autostage()
            if vessel.speed() < vessel.termv():
                vessel.throttle(vessel.throttle() * accel)
            else:
                vessel.throttle(max(vessel.throttle() * decel, min_throttle))
        return throttle_f

    def check_autostage(self):
        if self.stage_fuel() < 0.01:
            self.spacebar()

    def follow_apoapsis_func(self, max_dist=12000, min_dist=1000,
            static_dist=None, apo_target=75000, autostage=True):
        ''' Either a linear decrease of distance maintained between vessel and
        its apoapsis, or a static distance.
        '''
        init_alt = self.alt()
        if static_dist is None:
            final_alt = apo_target - min_dist
            diff_alt = final_alt - init_alt
        def throttle_f(vessel):
            if autostage:
                vessel.check_autostage()
            apo = vessel.apo()
            alt = vessel.alt()
            if static_dist is None:
                ratio_alt = float(alt - init_alt) / float(final_alt - init_alt)
                dist = (max_dist - ((max_dist - min_dist) * ratio_alt))
            else:
                dist = static_dist
            throttle_amount = 1 if alt + dist > apo else 0
            vessel.throttle(throttle_amount)
            #if alt + (dist / 2.0) < apo and alt + dist > apo:
        return throttle_f

    def thrust_on_apo_func(self, seconds_behind=8, autostage=True):
        def throttle_f(vessel):
            if autostage:
                vessel.check_autostage()
            apo_time = vessel.apo_time()
            if apo_time > seconds_behind:
                vessel.throttle(0)
            else:
                vessel.throttle(1)
        return throttle_f

    def launch(self, 
            alt_max=30000, apo_max=75000, turn_max=90, init_speed_max=100,
            termv_accel=1.02, termv_decel=0.99, termv_min_throttle=0.1,
            follow_apo_min_dist=1000, follow_apo_max_dist=12000,
            follow_apo_dist=None, circularize_seconds=8,
            autostage=True):
        self.throttle(1)
        self.spacebar()

        print('Full throttle until 100 m/s')
        # Burn until you hit 100 m/s
        self.run_behavior(
            turn_f=self.static_angle_func(0),
            vspeed=self.vspeed,
            vspeed_max=init_speed_max)

        print('Gravity turn with terminal velocity maintenance')
        # start to tip gradually up to alt_max and turn_max
        turn_f = self.gradual_turn_func(
            alt_max=alt_max, turn_max=turn_max)
        throttle_f = self.termv_thrust_func(
            accel=termv_accel, decel=termv_decel,
            min_throttle=termv_min_throttle, autostage=autostage)
        self.run_behavior(turn_f=turn_f, throttle_f=throttle_f,
            alt=self.alt, alt_max=alt_max)

        print('Follow apoapsis')
        # Now we're at `alt_max` and `turn_max` degrees AoA
        turn_f = self.static_angle_func(90)
        throttle_f = self.follow_apoapsis_func(
            max_dist=follow_apo_max_dist, min_dist=follow_apo_min_dist,
            static_dist=follow_apo_dist, apo_target = apo_max,
            autostage=autostage)
        self.run_behavior(
            turn_f=turn_f, throttle_f=throttle_f, apo=self.apo,
            apo_max=apo_max)

        print('Circularize')
        # Now circularize, because we're `follow_apo_dist` away from the 
        # apoapsis
        throttle_f = self.thrust_on_apo_func(
            seconds_behind=circularize_seconds, autostage=autostage)
        turn_f = self.static_angle_func(90)
        self.run_behavior(turn_f=turn_f, throttle_f=throttle_f,
            peri=self.peri, peri_max=self.apo())
        self.throttle(0)
        print('Orbiting!')
