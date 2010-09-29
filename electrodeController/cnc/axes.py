#!/usr/bin/env python

import logging, time

from IPSerialBridge import IPSerialBridge

# TODO:
# add value decoding to gets (and some sets)

DefaultLinearAxisConfig = """QM3
    QI2.0
    QV30.0
    SN2
    FR0.0127
    QS1000
    SU0.0000127
    TJ1
    OH0.0
    OL0.0
    OM3
    JH6.35
    JW3.175
    VU12.7
    VA3.175
    VB1.27
    AU6.35
    AC3.175
    AG3.175
    FE25.3999
    ZA323H
    ZB0H
    ZE3H
    ZF2H
    ZH24H
    ZS2H
    QD"""

JoystickOn = """BO0
    1BP11,10,12
    2BP9,8,12
    3BP14,13,12
    1BQ1
    2BQ1
    3BQ1
    1TJ3
    2TJ3
    3TJ3"""

JoystickOff = """1BQ0
    2BQ0
    3BQ0
    1TJ1
    2TJ1
    3TJ1"""

class Axes(IPSerialBridge):
    def __init__(self, address, port, axes={'x':1, 'y':2, 'z':3}, timeout=None):
        """
        address: ip-address of the serial bridge
        port: port of the serial bridge with the newport 300
        axes: dictionary of {'name': axis_index} (1-based)
          example:
            axes = {'x': 1, 'y': 2, 'z': 3}
        timeout: seconds to wait for the bridge to connect
        """
        IPSerialBridge.__init__(self, address, port)
        self.connect(timeout=timeout)
        self.axes = axes
        for v in self.axes.values():
            if type(v) != int:
                raise TypeError('Axis indices must be of type int')
            if v < 1 or v > 3:
                raise ValueError('Axis indices must be 0 < v < 4')
        self.disable_motor()
    
    def configure_axis(self, axis, cfgCommand):
        for command in cfgCommand.splitlines():
            self.send("%d%s" % (self.axes[axis], command), 1)
    
    def enable_joystick(self):
        for command in JoystickOn.splitlines():
            self.send(command, 1)
    
    def disable_joystick(self):
        for command in JoystickOff.splitlines():
            self.send(command, 1)
    
    
    # =============== Helper functions ========================
    def send_command(self, command, axis=None, value=""):
        """Send a command to either
        all axes (if axis==None) or
        one axis (defined by axis, a key used with self.axes)"""
        if axis == None:
            for i in self.axes.values():
                self.send("%i%s%s" % (i, command, value), 1)
        else:
            self.send("%i%s%s" % (self.axes[axis], command, value), 1)
    
    def poll_command(self, command, axis=None, value=""):
        """Send a command (and value) and wait for a response"""
        r = {}
        if axis == None:
            for a, i in self.axes.iteritems():
                r[a] = self.send("%i%s%s" % (i, command, value)).rstrip()
        else:
            r[axis] = self.send("%i%s%s" % (self.axes[axis], command, value)).rstrip()
        return r
    
    # ================ Command functions =======================
    def abort_motion(self):
        """This acts just like the e-stop (action defined in ZE)"""
        self.send('AB', 1)
    
    def set_acceleration(self, value, axis=None):
        """Set maximum acceleration of axis/axes"""
        # poll max accel/decel
        m = self.poll_command('AU', axis, "?")
        for (k,v) in m.iteritems():
            if value > v:
                raise ValueError('new accel %.4f exceeds max %.4f for axis %s' % (value, v, k))
        self.send_command('AC', axis, "%.4f" % value)
    
    def get_acceleration(self, axis=None):
        return self.poll_command('AC', axis, '?')
    
    def set_estop_deceleration(self, value, axis=None):
        self.send_command('AE', axis, '%.4f' % value)
    
    def get_estop_deceleration(self, axis=None):
        return self.poll_command('AE', axis, '?')
    
    def set_acceleration_feedforward_gain(self, value, axis=None):
        self.send_command('AF', axis, '%.4f' % value)
    
    def get_acceleration_feedforward_gain(self, axis=None):
        return self.poll_command('AF', axis, '?')
    
    def set_deceleration(self, value, axis=None):
        """Set maximum deceleration of axis/axes"""
        # poll max accel/decel
        m = self.poll_command('AU', axis, "?")
        for (k,v) in m.iteritems():
            if value > v:
                raise ValueError('new decel(%.4f) exceeds max(%.4f) for axis %s' % (value, v, k))
        self.send_command('AG', axis, "%.4f" % value)
    
    def get_deceleration(self, axis=None):
        return self.poll_command('AG', axis, '?')
    
    def abort_program(self):
        self.send('AB', 1)
    
    def set_max_acceleration_and_deceleration(self, value, axis=None):
        self.send_command('AU', axis, "%.4f" % value)
    
    def get_max_acceleration_and_deceleration(self, axis=None):
        return self.poll_command('AU', axis, '?')
    
    def set_backlash_compensation(self, value, axis=None):
        self.send_command('BA', axis, '%.4f' % value)
    
    def get_backlash_compensation(self, axis=None):
        return self.poll_command('BA', axis, '?')
    
    def set_dio_to_program(self, bit, program):
        self.send('%iBG%s' % (bit, program), 1)
    
    def get_dio_to_grogram(self, bit):
        return self.send('%iBG?' % bit)
    
    def set_dio_inhibit_motion(self, axis, bit, level):
        self.send('%iBK%i,%i' % (axis, bit, level), 1)
    
    def get_dio_inhibit_motion(self, axis):
        return self.send('%iBK?' % axis)
    
    def enable_dio_inhibit_motion(self, axis):
        self.send('%iBL1' % axis, 1)
    
    def disable_dio_inhibit_motion(self, axis):
        self.send('%iBL0' % axis, 1)
    
    def can_dio_inhibit_motion(self, axis):
        return self.send('%iBL?' % axis)
    
    def set_dio_notify_motion(self, axis, bit, level):
        self.send('%iBM%i,%i' % (axis, bit, level), 1)
    
    def get_dio_notify_motion(self, axis):
        return self.send('%iBM?' % axis)
    
    def enable_dio_notify_motion(self, axis):
        self.send('%iBN1' % axis, 1)
    
    def disable_dio_notify_motion(self, axis):
        self.send('%iBN0' % axis, 1)
    
    def can_dio_notify_motion(self, axis):
        return self.send('%iBN?' % axis)
    
    def set_dio_port_direction(self, value):
        self.send('BO%s' % value, 1)
    
    def get_dio_port_direction(self):
        return self.send('BO?')
    
    def set_dio_jog_mode(self, axis, negBit, posBit):
        self.send('%iBP%i,%i' % (axis, negBit, posBit), 1)
    
    def get_dio_jog_mode(self, axis):
        return self.send('%iBP?' % axis)
    
    def enable_dio_jog_mode(self, axis):
        self.send('%iBQ1' % axis, 1)
    
    def disable_dio_jog_mode(self, axis):
        self.send('%iBQ0' % axis, 1)
    
    def can_dio_jog_mode(self, axis):
        return self.send('%iBQ?' % axis)
    
    def set_closed_loop_interval(self, value, axis=None):
        self.send_command('CL', axis, '%i' % value)
    
    def get_closed_loop_interval(self, axis=None):
        return self.poll_command('CL', axis, '?')
    
    def set_linear_compensation(self, value, axis=None):
        self.send_command('CO', axis, '%f' % value)
    
    def get_linear_compensation(self, axis=None):
        return self.poll_command('CO', axis, '?')
    
    def set_deadband(self, value, axis=None):
        self.send_command('DB', axis, '%i' % value)
    
    def get_deadband(self, axis=None):
        return self.poll_command('DB', axis, '?')
    
    # 'DC' setup data acquisition
    # 'DD' get data acquisition status
    # 'DE' enable/disable data acquisition
    # 'DF' get data acquisition sample count
    # 'DG' get acquisition data
    
    def define_home(self, axis=None, value=0):
        """Define a software home"""
        self.send_command('DH', axis, "%.4f" % value)
    
    # def define_label(self, label):
    #     if label < 1 or label > 100:
    #         raise ValueError('Label(%i) must be 1 to 100' % label)
    #     self.send_command('%iDL', 1)
    
    def set_dac_offset(self, channel, offset):
        self.send('%iDO%f' % (channel, offset), 1)
    
    def get_dac_offset(self, channel):
        return self.send('%iDO?'% channel)
    
    def get_desired_position(self, axis=None):
        return self.poll_command('DP', axis, '?')
    
    def get_desired_velocity(self, axis=None):
        return self.poll_command('DV', axis, '?')
    
    # 'EO' automatic execution on power on
    # 'EP' enter program mode
    # 'EX' execute program
    
    def set_following_error_threshold(self, value, axis=None):
        self.send_command('FE', axis, '%f' % value)
    
    def get_following_error_threshold(self, axis=None):
        return self.poll_command('FE', axis, '?')
    
    def set_position_display_resolution(self, resolution, axis=None):
        if resolution < 0 or resolution > 7:
            raise ValueError('Resolution(%i) must be 0 to 7' % value)
        self.send_command('FP', axis, '%i' % resolution)
    
    def get_position_display_resolution(self, axis=None):
        return self.poll_command('FP', axis, '?')
    
    def set_full_step_resolution(self, resolution, axis=None):
        self.send_command('FR', axis, '%f' % resolution)
    
    def get_full_step_resolution(self, axis=None):
        return self.poll_command('FR', axis, '?')
    
    # 'GR' set master-slave reduction ratio
    # 'HA' set group acceleration
    # 'HB' read list of groups
    # 'HC' move group along arc
    # 'HD' set group decel
    # 'HE' set group estop decel
    # 'HF' group off
    # 'HJ' set group jerk
    # 'HL' move group along a line
    # 'HN' create new group
    # 'HO' group on
    # 'HP read group position
    # 'HQ' wait for group command buffer level
    # 'HS' stop group motion
    # 'HV' set group velocity
    # 'HX' delete group
    
    def get_stage_model(self, axis=None):
        return self.poll_command('ID', axis, '?')
    
    def set_jog_high_speed(self, value, axis=None):
        self.send_command('JH', axis, '%.4f' % value)
    
    def get_jog_high_speed(self, axis=None):
        return self.poll_command('JH', axis, '?')
    
    def set_jerk_rate(self, value, axis=None):
        self.send_command('JK', axis, '%.4f' % value)
    
    def get_jerk_rate(self, axis=None):
        return self.poll_command('JK', axis, '?')
    
    # 'JL' jump to label
    
    def set_jog_low_speed(self, value, axis=None):
        self.send_command('JW', axis, '%.4f' % value)
    
    def get_jog_low_speed(self, axis=None):
        return self.poll_command('JW', axis, '?')
    
    # 'KD' set derivative gain
    # 'KI' set integral gain
    # 'KP' set proportional gain
    # 'KS' set saturation level of integration
    
    def set_keyboard_lock(self, value):
        """
        0 : unlock
        1 : lock all but motor on/off
        2 : lock all
        """
        if not (value in (0,1,2)):
            raise ValueError('Keyboard lock value(%i) must be 0/1/2' % value)
        self.send('LC%i' % value, 1)
    
    def get_keyboard_lock(self):
        return self.send('LC?')
    
    # 'LP' list program
    
    def motion_done(self, axis=None):
        """Check if all axes (if axis==None) or a single axis is stationary"""
        return self.poll_command('MD', axis, '?')
    
    def disable_motor(self, axis=None):
        """Turn off power to motors"""
        self.send_command('MF', axis)
        
    def enable_motor(self, axis=None):
        """Turn on power to motors"""
        self.send_command('MO', axis)
    
    def get_motor_status(self, axis=None):
        return self.poll_command('MO?', axis)
    
    def move_to_hardware_limit(self, direction, axis=None):
        if not (direction in ('+','-')):
            raise ValueError('Direction(%s) must be + or -' % direction)
        self.send_command('MT', axis, direction)
    
    def move_indefinitely(self, direction, axis=None):
        if not (direction in ('+','-')):
            raise ValueError('Direction(%s) must be + or -' % direction)
        self.send_command('MV', axis, direction)
    
    def move_to_nearest_index(self, direction, axis=None):
        if not (direction in ('+','-')):
            raise ValueError('Direction(%s) must be + or -' % direction)
        self.send_command('MZ', axis, direction)
    
    def set_home_high_speed(self, value, axis=None):
        self.send_command('OH', axis, '%.4f' % value)
    
    def get_home_high_speed(self, axis=None):
        return self.poll_command('OH', axis, '?')
    
    def set_home_low_speed(self, value, axis=None):
        self.send_command('OL', axis, '%.4f' % value)
    
    def get_home_low_speed(self, axis=None):
        return self.poll_command('OL', axis, '?')
    
    def set_home_mode(self, mode, axis=None):
        if mode < 0 or mode > 6:
            raise ValueError('Home mode(%i) must be in 0 to 6' % mode)
        self.send_command('OM', axis, '%i' % mode)
    
    def get_home_mode(self, axis=None):
        return self.poll_command('OM', axis, '?')
    
    def home(self, mode, axis=None):
        if mode < 0 or mode > 6:
            raise ValueError('Home mode(%i) must be in 0 to 6' % mode)
        self.send_command('OR', axis, '%i' % mode)
    
    def move_absolute(self, value, axis=None):
        self.send_command('PA', axis, '%.4f' % value)
    
    def get_hardware_status(self):
        return self.send('PH')
    
    def move_relative(self, value, axis=None):
        self.send_command('PR', axis, '%.4f' % value)
    
    def update_motor_settings(self, axis=None):
        self.send_command('QD', axis, '')
    
    # 'QG' set gear constant
    
    def set_max_motor_current(self, current, axis=None):
        self.send_command('QI', axis, '%.4f' % current)
    
    def get_max_motor_current(self, axis=None):
        return self.poll_command('QI', axis, '?')
    
    def set_motor_type(self, value, axis=None):
        if value < 0 or value > 4:
            return ValueError('Motor type(%i) must be in 0 to 4' % value)
        self.send_command('QM', axis, '%i' % value)
    
    def get_motor_type(self, axis=None):
        return self.poll_command('QM', axis, '?')
    
    # 'QP' quit program mode
    
    def set_reduce_torque(self, delay, percent, axis=None):
        self.send_command('QR', axis, '%i,%i' % (delay, percent))
    
    def get_reduce_torque(self, axis=None):
        return self.poll_command('QR', axis, '?')
    
    def set_microstep_factor(self, factor, axis=None):
        self.send_command('QS', axis, '%i' % factor)
    
    def get_microstep_factor(self, axis=None):
        return self.poll_command('QS', axis, '?')
    
    # 'QT' set tachometer gain
    
    def set_avg_motor_voltage(self, voltage, axis=None):
        self.send_command('QV', axis, '%.4f' % voltage)
    
    def get_avg_motor_voltage(self, axis=None):
        return self.poll_command('QV', axis, '?')
    
    def reset(self):
        self.send('RS', 1)
    
    # 'SA' set device address
    def set_dio_status(self, status):
        self.send('SB%s' % status, 1)
    
    def get_dio_status(self):
        return self.send('SB?')
    
    def set_home_position(self, position, axis=None):
        self.send_command('SH', axis, '%.4f' % position)
    
    def get_home_position(self, axis=None):
        return self.poll_command('SH', axis, '?')
    
    def set_ms_jog_velocity_update_interval(self, ms):
        if ms < 1 or ms > 1000:
            raise ValueError('Interval(%i) must be in 1 to 1000' % ms)
        self.send('SI%i' % ms, 1)
    
    def get_ms_jog_velocity_update_interval(self):
        return self.send('SI?')
    
    def set_ms_jog_velocity_scaling(self, a, b):
        self.send('SK%f,%f' % (a,b), 1)
    
    def get_ms_jog_velocity_scaling(self):
        return self.send('SK?')
    
    def set_left_software_limit(self, posLimit, axis=None):
        self.send_command('SL', axis, '%.4f' % posLimit)
    
    def get_left_software_limit(self, axis=None):
        return self.poll_command('SL', axis, '?')
    
    def save_settings_to_controller(self):
        """Save current controller settings to non-volitile memory on the ESP300"""
        self.send("SM",1)
    
    def set_units(self, unit, axis=None):
        if unit < 0 or unit > 11:
            raise ValueError('Unit(%i) must be in 0 to 11' % unit)
        self.send_command('SN', axis, '%i' % unit)
    
    def get_units(self, axis=None):
        return self.poll_command('SN', axis, '?')
    
    def set_right_software_limit(self, negLimit, axis=None):
        self.send_command('SR', axis, '%.4f' % negLimit)
    
    def get_right_software_limit(self, axis=None):
        return self.poll_command('SR', axis, '?')
    
    def set_slave_master(self, slave, master):
        self.send('%iSS%i' % (slave, master), 1)
    
    def get_master(self, axis):
        return self.send('%iSS?' % axis)
    
    def stop_motion(self, axis=None):
        self.send_command('ST', axis)
    
    def set_encoder_resolution(self, resolution, axis=None):
        self.send_command('SU', axis, '%f' % resolution)
    
    def get_encoder_resolution(self, axis=None):
        self.poll_command('SU', axis, '?')
    
    def read_error_message(self):
        return self.read('TB?')
    
    def read_error_code(self):
        return self.read('TE?')
    
    def set_trajectory_mode(self, mode, axis=None):
        if mode < 1 or mode > 6:
            raise ValueError('Mode(%i) must be in 1 to 6' % mode)
        self.send_command('TJ', axis, '%i' % mode)
    
    def get_position(self, axis=None):
        return self.poll_command('TP', axis)
    
    def get_controller_status(self):
        return self.send('TS')
    
    def get_current_velocity(self, axis=None):
        """Get the current actual velocity"""
        return self.poll_command('TV', axis)
    
    def get_controller_activity(self):
        return self.send('TX')
    
    # 'UF' update servo filter
    
    def wait_for_dio_high(self, bit):
        self.send('%iUH' % bit, 1)
    
    def wait_for_dio_low(self, bit):
        self.send('%iUL' % bit, 1)
    
    def set_velocity(self, value, axis=None):
        # poll max velocity
        m = self.get_max_velocity()
        for (k,v) in m.iteritems():
            if value > v:
                raise ValueError('new vel %.4f exceeds max %.4f for axis %s' % (value, v, k))
        self.send_command('VA', axis, '%.4f' % value)
    
    def get_velocity(self, axis=None):
        return self.poll_command('VA', axis, '?')
    
    def set_base_velocity(self, value, axis=None):
        """used only for step motors"""
        # poll max velocity
        m = self.get_max_velocity(axis)
        for (k,v) in m.iteritems():
            if value > v:
                raise ValueError('new vel %.4f exceeds max %.4f for axis %s' % (value, v, k))
        self.send_command('VB', axis, '%.4f' % value)
    
    def get_base_velocity(self, axis=None):
        return self.poll_command('VB', axis, '?')
    
    def get_firmware_version(self):
        return self.send('VE?')
    
    def set_velocity_feedforward_gain(self, value, axis=None):
        self.send_command('VF', axis, '%f' % value)
    
    def get_velocity_feedforward_gain(self, axis=None):
        return self.poll_command('VF', axis, '?')
    
    def set_max_velocity(self, value, axis=None):
        self.send_command('VU', axis, '%.4f' % value)
    
    def get_max_velocity(self, axis=None):
        return self.poll_command('VU', axis, '?')
    
    def wait_for_position(self, value, axis=None):
        self.send_command('WP', axis, '%f' % value)
    
    def wait_for_stop(self, ms, axis=None):
        self.send_command('WS', axis, '%i' % ms)
    
    def wait(self, ms):
        self.send('WT%i' % ms, 1)
    
    def get_available_memory(self):
        return self.send('XM')
    
    # 'XX' erase program
    
    def set_amp_io_config(self, config, axis=None):
        self.send_command('ZA', axis, config)
    
    def get_amp_io_config(self, axis=None):
        return self.poll_command('ZA', axis, '?')
    
    def set_feedback_config(self, config, axis=None):
        self.send_command('ZB', axis, config)
    
    def get_feedback_config(self, axis=None):
        return self.poll_command('ZB', axis, '?')
    
    def set_estop_config(self, config, axis=None):
        self.send_command('ZE', axis, config)
    
    def get_estop_config(self, axis=None):
        return self.poll_command('ZE', axis, '?')
    
    def set_following_error_config(self, config, axis=None):
        self.send_command('ZF', axis, config)
    
    def get_following_error_config(self, axis=None):
        return self.poll_command('ZF', axis, '?')
    
    def set_hardware_limit_config(self, config, axis=None):
        self.send_command('ZH', axis, config)
    
    def get_hardware_limit_config(self, axis=None):
        return self.poll_command('ZH', axis, '?')
    
    def set_software_limit_config(self, config, axis=None):
        self.send_command('ZS', axis, config)
    
    def get_software_limit_config(self, axis=None):
        return self.poll_command('ZS', axis, '?')
    
    def get_esp_config(self):
        return self.send('ZU')
    
    def set_system_config(self, config):
        self.send('ZZ%s' % config, 1)
    
    def get_system_config(self):
        return self.send('ZZ?')

class FakeAxes(Axes):
    def __init__(self, address, port, axes={}, timeout=None):
        logging.debug('Constructing cnc.FakeAxes for %s:%i' % (address, port))
        logging.debug('cnc.FakeAxes with axes' + str(axes))
        self.axes = axes.copy()
        for v in self.axes.values():
            if type(v) != int:
                raise TypeError('Axis indices must be of type int')
            if v < 1 or v > 3:
                raise ValueError('Axis indices must be 0 < v < 4')
        
        self.pos = axes.copy()
        for k in self.pos:
            self.pos[k] = 0.0
    
    def __del__(self):
        pass
    
    def send(self, message, noresponse = 0):
        logging.debug('sending: %s' % message)
        if noresponse == 0:
            return message
    
    # ======== Functions to main internal 'fake' variables ============    
    def set_acceleration(self, value, axis=None):
        self.send_command('AC', axis, "%.4f" % value)
    
    def set_deceleration(self, value, axis=None):
        self.send_command('AG', axis, "%.4f" % value)
    
    def define_home(self, axis=None, value=0):
        """Define a software home"""
        self.send_command('DH', axis, "%.4f" % value)
        if axis == None:
            for k in self.pos:
                self.pos[k] = value
        else:
            self.pos[axis] = value
    
    def get_desired_position(self, axis=None):
        self.poll_command('DP', axis, '?')
        if axis == None:
            return self.pos
        else:
            return self.pos[axis]
    
    def get_desired_velocity(self, axis=None):
        self.poll_command('DV', axis, '?')
        if axis == None:
            r = self.pos.copy()
            for k in r:
                r[k] = 0.
            return r
        else:
            return {axis: 0.}
    
    def motion_done(self, axis=None):
        self.poll_command('MD', axis, '?')
        if axis == None:
            r = self.pos.copy()
            for k in r:
                r[k] = 1
            return r
        else:
            return {axis: 1}
    
    def move_absolute(self, value, axis=None):
        self.send_command('PA', axis, '%.4f' % value)
        if axis == None:
            for a in self.axes:
                self.pos[a] = value
        else:
            self.pos[axis] = value
    
    def move_relative(self, value, axis=None):
        #self.send_command('PR', axis, '%.4f' % value)
        if axis == None:
            for a in self.axes:
                self.pos[a] += value
        else:
            self.pos[axis] += value
    
    def get_velocity(self, axis=None):
        if axis == None:
            d = {}
            for a in axis:
                d[a] = 0.0
            return d
        else:
            return {axis: 0.0}
    
    def get_position(self, axis=None):
        #self.poll_command('TP', axis)
        if axis == None:
            return self.pos
        else:
            return {axis: self.pos[axis]}
    
    def get_current_velocity(self, axis=None):
        self.poll_command('TV', axis)
        if axis == None:
            r = self.pos.copy()
            for k in r:
                r[k] = 0.
            return r
        else:
            return {axis: 0.0}
    
    def set_velocity(self, value, axis=None):
        self.send_command('VA', axis, '%.4f' % value)
    
    def set_base_velocity(self, value, axis=None):
        self.send_command('VB', axis, '%.4f' % value)


# ===========================================================
#                         Tests
# ===========================================================

def test_joystick(ipAddress, port, axes):
    print "Constructing"
    f = Axes(ipAddress, port, axes)
    print "Configuring"
    for a in axes.keys():
        f.configure_axis(a, DefaultLinearAxisConfig)
    print "Enabling joystick control"
    f.enable_joystick()
    print "Press Enter to enable motors"
    raw_input()
    f.enable_motor()
    print "Press Enter to quit"
    raw_input()
    print "Disabling Motor"
    f.disable_motor()
    print "Disabling Joystick"
    f.disable_joystick()

def test_configure_home(ipAddress, port, axes):
    print "Constructing"
    f = Axes(ipAddress, port, axes)
    print "Configuring"
    for a in axes.keys():
        f.configure_axis(a, DefaultLinearAxisConfig)
    print "Disabling motors"
    f.disable_motor()
    print "Do remaining steps with front panel (press enter after each step)"
    raw_input(" set x home velocity (+3.175)")
    raw_input(" make sure x axis can safely move to it's limit switch")
    raw_input(" enable x axis motor")
    raw_input(" double check clearance")
    raw_input(" home x-axis")
    raw_input(" disable x-axis motor")
    print
    raw_input(" set y home velocity (-3.175)")
    raw_input(" make sure y axis can safely move to it's limit switch")
    raw_input(" enable y axis motor")
    raw_input(" double check clearance")
    raw_input(" home y-axis")
    raw_input(" disable y-axis motor")
    print
    raw_input(" set z home velocity (-3.175)")
    raw_input(" make sure z axis can safely move to it's limit switch")
    raw_input(" enable z axis motor")
    raw_input(" double check clearance")
    raw_input(" home z-axis")
    raw_input(" disable z-axis motor")
    

def test_linear_axis(axisName, axisIndex, ipAddress, port):
    print "Testing Axis: %s index %d" % (axisName, axisIndex)
    f = Axes(ipAddress, port, {axisName: axisIndex})
    print "Configuring..."
    f.configure_axis(axisName, DefaultLinearAxisConfig)
    print "Current Position: %f" % float(f.get_position(axisName)[axisName])
    print "Current Velocity: %f" % float(f.get_current_velocity(axisName)[axisName])
    
    # set test move (+X, then -2X, then +X)
    testDistance = 12.7
    def set_test_distance(testDistance):
        print "Input test move distance (move=+X,-2X,+X)"
        i = raw_input()
        oldDistance = testDistance
        testDistance = float(i)
        print "New Test Distance = %f" % testDistance
        print "Is this ok? [y]/n"
        r = raw_input()
        if r == '' or r[0].lower() == 'y':
            return testDistance
        else:
            print "Resetting Test Distance"
            testDistance = oldDistance
            print "New Test Distance = %f" % testDistance
            return testDistance
    
    def run_test_move(testDistance):
        print "Move +%f" % testDistance
        f.move_relative(testDistance,axisName)
        print "Waiting for motion to complete"
        while f.motion_done(axisName)[axisName] == '0':
            #print "Position: %f" % float(f.get_position(axisName)[axisName]),
            #print "Velocity: %f" % float(f.get_velocity(axisName)[axisName])
            time.sleep(0.1)
        
        time.sleep(0.1)
        print "Move -2*%f" % testDistance
        f.move_relative(-2*testDistance,axisName)
        print "Waiting for motion to complete"
        while f.motion_done(axisName)[axisName] == '0':
            #print "Position: %f" % float(f.get_position(axisName)[axisName]),
            #print "Velocity: %f" % float(f.get_velocity(axisName)[axisName])
            time.sleep(0.1)
        print "Move +%f" % testDistance
        
        time.sleep(0.1)
        f.move_relative(testDistance)
        print "Waiting for motion to complete"
        while f.motion_done(axisName)[axisName] == '0':
            #print "Position: %f" % float(f.get_position(axisName)[axisName]),
            #print "Velocity: %f" % float(f.get_velocity(axisName)[axisName])
            time.sleep(0.1)
        print "Test movement complete"
    
    def print_commands():
        print 
        print "Enter a command"
        print " --"
        print "q: quit"
        print " --"
        print_config()
        print
    
    def run_command(command):
        """return 0 to continue else exit"""
        if command == '':
            return 0
        c = command[0]
        if c == 'q' or c == 'Q':
            return 1
        elif c == 'b':
            # set base base velocity
            print "Current base velocity: %f" % float(f.get_base_velocity(axisName)[axisName])
            print "Enter new base velocity:"
            try:
                nv = float(raw_input())
                f.set_base_velocity(nv, axisName)
                print "New value: %f" % float(f.get_base_velocity(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'v':
            # set velocity
            print "Current velocity: %f" % float(f.get_velocity(axisName)[axisName])
            print "Enter new velocity:"
            try:
                nv = float(raw_input())
                f.set_velocity(nv, axisName)
                print "New value: %f" % float(f.get_velocity(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'V':
            # set max velocity
            print "Current max velocity: %f" % float(f.get_max_velocity(axisName)[axisName])
            print "Enter new max_velocity:"
            try:
                nv = float(raw_input())
                f.set_max_velocity(nv, axisName)
                print "New value: %f" % float(f.get_max_velocity(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'j':
            # set low jog speed
            print "Current jog low speed: %f" % float(f.get_jog_low_speed(axisName)[axisName])
            print "Enter new jog low speed:"
            try:
                nv = float(raw_input())
                f.set_jog_low_speed(nv, axisName)
                print "New value: %f" % float(f.get_jog_low_speed(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'J':
            # set high jog speed
            print "Current jog high speed: %f" % float(f.get_jog_high_speed(axisName)[axisName])
            print "Enter new jog high speed:"
            try:
                nv = float(raw_input())
                f.set_jog_high_speed(nv, axisName)
                print "New value: %f" % float(f.get_jog_high_speed(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'a':
            # set acceleration
            print "Current acceleration: %f" % float(f.get_acceleration(axisName)[axisName])
            print "Enter new accleration:"
            try:
                nv = float(raw_input())
                f.set_acceleration(nv, axisName)
                print "New value: %f" % float(f.get_acceleration(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'A':
            # set max acceleration
            print "Current max acceleration: %f" % float(f.get_max_acceleration_and_deceleration(axisName)[axisName])
            print "Enter new max acceleration:"
            try:
                nv = float(raw_input())
                f.set_max_acceleration_and_deceleration(nv, axisName)
                print "New value: %f" % float(f.get_max_acceleration_and_deceleration(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        elif c == 'd':
            # set deceleration
            print "Current deceleration: %f" % float(f.get_deceleration(axisName)[axisName])
            print "Enter new deceleration:"
            try:
                nv = float(raw_input())
                f.set_deceleration(nv, axisName)
                print "New value: %f" % float(f.get_deceleration(axisName)[axisName])
            except:
                print "Invalid entry, keeping old value"
                return 0
        else:
            print "Invalid command"
            return 0
    
    def print_config():
        print "v: Velocity: %f" % float(f.get_velocity(axisName)[axisName])
        print "V: Max Velocity: %f" % float(f.get_max_velocity(axisName)[axisName])
        print "b: Base Velocity: %f" % float(f.get_base_velocity(axisName)[axisName])
        print "j: Jog Low Speed: %f" % float(f.get_jog_low_speed(axisName)[axisName])
        print "J: Jog High Speed: %f" % float(f.get_jog_high_speed(axisName)[axisName])
        print "a: Acceleration: %f" % float(f.get_acceleration(axisName)[axisName])
        print "A: Max Acceleration: %f" % float(f.get_max_acceleration_and_deceleration(axisName)[axisName])
        print "d: Deceleration: %f" % float(f.get_deceleration(axisName)[axisName])
    
    testDistance = set_test_distance(testDistance)
    
    f.enable_motor(axisName)
    while True:
        # do move?
        print 'Run test movement? [y]/n'
        r = raw_input()
        if r =='' or r[0].lower() == 'y':
            run_test_move(testDistance)
        
        # set parameter/quit
        print_commands()
        r = raw_input()
        if run_command(r):
            break
    
    print_config()
    
    # shutdown
    f.disable_motor(axisName)
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ipAddress = '169.254.0.9'
    port = 8003
    axes = {'x':1, 'y':2, 'z':3}
    print "What test would you like to perform?"
    print " 1: test_linear_axis 1"
    print " 2: test_linear_axis 2"
    print " 3: test_linear_axis 3"
    print " 4: test_joystick"
    print " 5: configure for home"
    testIndex = int(raw_input())
    if testIndex == 1:
        print "Testing linear axis 1"
        test_linear_axis('x', 1, ipAddress, port)
    elif testIndex == 2:
        print "Testing linear axis 2"
        test_linear_axis('y', 2, ipAddress, port)
    elif testIndex == 3:
        print "Testing linear axis 3"
        test_linear_axis('z', 3, ipAddress, port)
    elif testIndex == 4:
        print "Testing joystick"
        test_joystick(ipAddress, port, {'x':1, 'y':2, 'z':3})
    elif testIndex == 5:
        print "Configuring axes to home"
        test_configure_home(ipAddress,port, {'x':1, 'y':2, 'z':3})
    else:
        print "Unknown test, exiting"