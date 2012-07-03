#!/usr/bin/env python

import logging, os

# homing procedure
# home modes should be
# OM3 for all linear axes
# OM3 for w-axis
# be sure that all cables are free from obstruction
# be sure the tip will not contact anything
# homing velocities should be (set on front panel):
#  X : +1 mm/s
#  Y : -1 mm/s
#  Z : -1 mm/s
# first, start homing and trigger switch by hand to verfiy that the axis stops
# then home with front panel
# reset all home velocities to 0 mm/s with front panel
#
# max travel (setup as of 2011-03-17)
# X -352 mm
# Y +105 mm
# Z +77 mm

# ----- CNC settings ------
cncLinearAxesIP = "169.254.0.9"
cncLinearAxesPort = 8003
cncLinearAxes = {'x':1, 'y':2, 'z':3}
cncHeadAxesIP = "169.254.0.9"
cncHeadAxesPort = 8004
cncHeadAxes = {'b':1, 'w':2}

serialConnectionTimeout = 4.0

cncArmLength = 212.331

cncRegDeltaAngle = 2.0 # in degrees

# -- X --
xInc = 1.27
xPosLimit = 12.70
xNegLimit = -12.70
# QM: motor type (3: step motor)
# QI: motor current (amps)
# QV: motor voltage (volts)
# SN: displacement units (2: millimeter)
# FR: full step resolution
# QS: microstep factor
# TJ: trajectory mode (1: trapezoidal)
# FE: max following error threshold (25.3999)???
# OH: home high speed
# OL: home low speed
# OM: home search mode (2: home switch)
# JH: jog high speed
# JW: jog low speed
# VU: max velocity
# VA: actual velocity ????
# VB: base velocity (to overcome static friction)
# AU: max accel/decel
# AC: accel
# AG: decel
# ZA: amplifier I/O (0011 0010 0011:)
#  0 (0) : disable amp fault input checking
#  1 (0) : do not disable motor on amp fault event
#  2 (1) : abort motion on amp fault event
#  3 (1) : reserved
#  4 (0) : reserved
#  5 (0) : amp fault input active low
#  6 (1) : config step motor control outputs for +STEP/-STEP
#  7 (0) : configure step output as active low
#  8 (0) : configure direction output as active low
#  9 (0) : do not invert servo DAC output polarity
# 10 (1) : amp enable output active high
# 11 (1) : stepper motor winding is half
# ZB: feedback config (0000 0000 0000: no feedback)
# ZE: e-stop config (0011:)
#  0 (0) : disable e-stop checking
#  1 (0) : do not disable motor power on e-stop event
#  2 (1) : abort motion on e-stop event
#  3 (1) : reserved
# ZF: following-error config (0010:)
#  0 (0) : disable following error checking
#  1 (0) : do not disable motor power on following error
#  2 (1) : abort motion on following error
#  3 (0) : reserved
# ZH: hardware limit config (0010 0100:)
#  0 (0) : disable hw limit checking
#  1 (0) : do not disable motor power on hw limit
#  2 (1) : abort motion on hw limit
#  3 (0) : reserved
#  4 (0) : reserved
#  5 (1) : hw limit active high
#  6 (0) : reserved
#  7 (0) : reserved
# ZS: software limit config (0010:)
#  0 (0) : disable sw limit checking
#  1 (0) : do not disable motor on sw limit
#  2 (1) : abort motion on sw limit
#  3 (0) : reserved
# QD: update motor settings
xAxisConfig="""QM3
    QI2.0
    QV30.0
    SN2
    FR0.0127
    QS1000
    TJ1
    OH0.0
    OL0.0
    OM3
    JH6.35
    JW3.175
    VU6.35
    VA3.175
    VB0.5
    AU3.175
    AC3.175
    AG3.175
    ZA323H
    ZB0H
    ZE3H
    ZF2H
    ZH24H
    ZS2H
    QD"""

# -- Y --
yInc = 1.27
yPosLimit = 12.70
yNegLimit = -12.70
yAxisConfig="""QM3
    QI2.0
    QV30.0
    SN2
    FR0.0127
    QS1000
    TJ1
    OH0.0
    OL0.0
    OM3
    JH6.35
    JW3.175
    VU6.35
    VA3.175
    VB0.5
    AU3.175
    AC3.175
    AG3.175
    ZA323H
    ZB0H
    ZE3H
    ZF2H
    ZH24H
    ZS2H
    QD"""

# -- Z --
zInc = 1.27
zPosLimit = 12.70
zNegLimit = -12.70
zAxisConfig="""QM3
    QI2.0
    QV30.0
    SN2
    FR0.0127
    QS1000
    TJ1
    OH0.0
    OL0.0
    OM3
    JH6.35
    JW3.175
    VU6.35
    VA3.175
    VB0.5
    AU3.175
    AC3.175
    AG3.175
    ZA323H
    ZB0H
    ZE3H
    ZF2H
    ZH24H
    ZS2H
    QD"""

# -- B --
bInc = 1.0

# -- W --
wInc = 0.5
wDirection = 1.0 # for flipping the w-axis
# Thorlabs stage specs:
# 0.05 um minimal achievable incremental motion
# 0.8 um minimal repeatable incremental motion
wAxisConfig = """QM1
	SN2
	SU0.000029
	FR1.000000
	QS10
	QV12.0
	QI0.500
	QG14.0000
	QT0.00
	SL-50.00000
	SR0.00000
	TJ1
	OM3
	VU1.00000
	VA0.500000
	JH0.060000
	JW0.010000
	OH0.500000
	VB0.000000
	AU2.00000
	AC0.5000
	AG0.5000
	AE1000000
	JK0.1000
	KP600.000
	KI0.00
	KD600.0000
	VF75.0000
	AF0.000000
	KS300.0
	FE1.00000
	DB0
	CL1
	QR1000, 50.0000
	SS2
	GR1.000000
	SI10
	SK0.000000, 0.000000
	BA0.00000
	CO0.000000
	TA0
	CA100
	FQ50
	ZA327H
	ZB307H
	ZE7H
	ZF7H
	ZH7H
	ZS6H
	QD"""