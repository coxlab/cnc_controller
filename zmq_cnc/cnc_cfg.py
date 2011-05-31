#!/usr/bin/env python

cfgDict = { 'arm_length' : 212.331,
            'fake' : True,
            'linear_ip' : "169.254.0.9",
            'linear_port' : 8003,
            'linear_axes' : {'x':1, 'y':2, 'z':3},
            'head_ip' : "169.254.0.9",
            'head_port' : 8004,
            'head_axes' : {'b':1, 'w':2},
            'serial_timeout' : 4.0,
            'x_cfg' : """QM3
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
                QD""",
            'y_cfg' : """QM3
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
                QD""",
            'z_cfg' : """QM3
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
                QD""",
            'w_cfg' : """QM1
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
            }