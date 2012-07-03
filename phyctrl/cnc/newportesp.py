#!/usr/bin/env python

import logging

from ..io.ipserial import IPSerialBridge

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


class NewportESP(IPSerialBridge):
    def __init__(self, address, port, timeout=None, naxes=3):
        """
        address: ip-address of the serial bridge
        port: port of the serial bridge with the newport 300
        timeout: seconds to wait for the bridge to connect
        """
        IPSerialBridge.__init__(self, address, port)
        self._axes = range(1, naxes + 1)  # newport uses 1 based indexing
        self._timeout = timeout
        self.connected = False
        self.connect()

    def connect(self):
        self.connected = self.connect(timeout=self._timeout)
        if not self.connected:
            logging.error("NewportESP failed to connect")
        return self.connected

    def configure_axis(self, axis, cfgCommand):
        axis = int(axis)
        for command in cfgCommand.splitlines():
            self.send("%i%s" % (axis, command.strip()), 1)

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
        one axis (of type int)"""
        if axis == None:
            for i in self._axes:
                self.send("%i%s%s" % (i, command, value), 1)
        else:
            axis = int(axis)
            self.send("%i%s%s" % (axis, command, value), 1)

    def poll_command(self, command, axis=None, value=""):
        """Send a command (and value) and wait for a response"""
        if axis == None:
            return [self.send("%i%s%s" % (i, command, value)).rstrip() \
                    for i in self._axes]
        else:
            axis = int(axis)
            return self.send("%i%s%s" % (axis, command, value)).rstrip()

    # ================ Command functions =======================
    def abort_motion(self):
        """This acts just like the e-stop (action defined in ZE)"""
        self.send('AB', 1)

    def set_acceleration(self, value, axis=None):
        """Set maximum acceleration of axis/axes"""
        # poll max accel/decel
        m = self.poll_command('AU', axis, "?")
        for (k, v) in m.iteritems():
            if value > v:
                raise ValueError('new accel %.4f exceeds max %.4f for axis %s'\
                        % (value, v, k))
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
        for (k, v) in m.iteritems():
            if value > v:
                raise ValueError('new decel(%.4f) exceeds max(%.4f)' \
                        'for axis %s' % (value, v, k))
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
        return self.send('%iDO?' % channel)

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
            raise ValueError('Resolution(%i) must be 0 to 7' % resolution)
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
        if not (value in (0, 1, 2)):
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
        if not (direction in ('+', '-')):
            raise ValueError('Direction(%s) must be + or -' % direction)
        self.send_command('MT', axis, direction)

    def move_indefinitely(self, direction, axis=None):
        if not (direction in ('+', '-')):
            raise ValueError('Direction(%s) must be + or -' % direction)
        self.send_command('MV', axis, direction)

    def move_to_nearest_index(self, direction, axis=None):
        if not (direction in ('+', '-')):
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
        self.send_command('QR', axis, '%i,%.3f' % (delay, percent))

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
        self.send('SK%f,%f' % (a, b), 1)

    def get_ms_jog_velocity_scaling(self):
        return self.send('SK?')

    def set_left_software_limit(self, posLimit, axis=None):
        self.send_command('SL', axis, '%.4f' % posLimit)

    def get_left_software_limit(self, axis=None):
        return self.poll_command('SL', axis, '?')

    def save_settings_to_controller(self):
        """
        Save current controller settings to non-volitile memory on the ESP300
        """
        self.send("SM", 1)

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
        for (k, v) in m.iteritems():
            if value > v:
                raise ValueError('new vel %.4f exceeds max %.4f for axis %s' \
                        % (value, v, k))
        self.send_command('VA', axis, '%.4f' % value)

    def get_velocity(self, axis=None):
        return self.poll_command('VA', axis, '?')

    def set_base_velocity(self, value, axis=None):
        """used only for step motors"""
        # poll max velocity
        m = self.get_max_velocity(axis)
        for (k, v) in m.iteritems():
            if value > v:
                raise ValueError('new vel %.4f exceeds max %.4f for axis %s' \
                        % (value, v, k))
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
