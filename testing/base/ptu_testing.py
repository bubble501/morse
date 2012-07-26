#! /usr/bin/env python
"""
This script tests the 'data stream' oriented feature of the socket interface.
"""

from morse.testing.testing import MorseTestCase

try:
    # Include this import to be able to use your test file as a regular 
    # builder script, ie, usable with: 'morse [run|exec] <your test>.py
    from morse.builder.morsebuilder import *
except ImportError:
    pass

import os
import sys
import socket
import math
import json
import time
from pymorse import Morse

def send_angles(s, pan, tilt):
    s.send(json.dumps({'pan' : pan, 'tilt' : tilt}).encode())

class PTUTest(MorseTestCase):

    def setUpEnv(self):
        
        robot = Robot('atrv')
        
        PTU_posture = Sensor('ptu_posture')
        PTU_posture.translate(x=0.2020, z=1.4400)
        robot.append(PTU_posture)
        PTU_posture.configure_mw('socket')

        PTU = Actuator('ptu')
        PTU.configure_mw('socket')
        PTU.configure_service('socket')
        PTU.properties(Speed = 0.5)
        PTU_posture.append(PTU)

        gyro = Sensor('gyroscope')
        gyro.configure_mw('socket')
        PTU.append(gyro)

        env = Environment('indoors-1/indoor-1')
        env.configure_service('socket')

    def test_datastream(self):
        """ Test if we can connect to the pose data stream, and read from it.
        """

        with Morse() as morse:
            gyro_stream = morse.stream('Gyroscope')
            posture_stream = morse.stream('ptu_posture')

            port = morse.get_stream_port('PTU')
            ptu_stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ptu_stream.connect(('localhost', port))

            angles = gyro_stream.get()
            posture = posture_stream.get()

            precision = 0.02
            moving_precision = 0.1

            self.assertAlmostEqual(posture['pan'], 0.0, delta=precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['yaw'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=precision)

            send_angles(ptu_stream, 1.0, 0.0)
            time.sleep(1.0)

            # here at speed of 0.5 rad / sec, we must be at the middle
            # of the trip, check it :)
            angles = gyro_stream.get()
            posture = posture_stream.get()
            self.assertAlmostEqual(posture['pan'], 0.5, delta=moving_precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=moving_precision)
            self.assertAlmostEqual(angles['yaw'], 0.5, delta=moving_precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=moving_precision)

            time.sleep(1.0)
            # now we must have achieve ptu rotation
            angles = gyro_stream.get()
            posture = posture_stream.get()

            self.assertAlmostEqual(posture['pan'], 1.0, delta=precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['yaw'], 1.0, delta=precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=precision)

            send_angles(ptu_stream, 1.0, -1.0)
            time.sleep(2.0)
            angles = gyro_stream.get()
            posture = posture_stream.get()

            self.assertAlmostEqual(posture['pan'], 1.0, delta=precision)
            self.assertAlmostEqual(posture['tilt'], -1.0, delta=precision)
            self.assertAlmostEqual(angles['yaw'], 1.0, delta=precision)
            self.assertAlmostEqual(angles['pitch'], -1.0, delta=precision)

            send_angles(ptu_stream, 0.0, 0.0)
            time.sleep(2.0)
            angles = gyro_stream.get()
            posture = posture_stream.get()

            self.assertAlmostEqual(posture['pan'], 0.0, delta=precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['yaw'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=precision)

    def test_service(self):
        """ Test if we can connect to the pose data stream, and read from it.
        """

        with Morse() as morse:
            gyro_stream = morse.stream('Gyroscope')
            posture_stream = morse.stream('ptu_posture')

            angles = gyro_stream.get()
            posture = posture_stream.get()

            precision = 0.02
            moving_precision = 0.1

            self.assertAlmostEqual(posture['pan'], 0.0, delta=precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['yaw'], 0.0, delta=precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=precision)

            res = morse.call_server('PTU', 'get_pan_tilt')
            self.assertAlmostEqual(res[0], 0.0, delta=precision)
            self.assertAlmostEqual(res[1], 0.0, delta=precision)

            morse.call_server('PTU', 'set_pan_tilt', 1.0, 0.0)

            angles = gyro_stream.get()
            posture = posture_stream.get()
            self.assertAlmostEqual(posture['pan'], 1.0, delta=moving_precision)
            self.assertAlmostEqual(posture['tilt'], 0.0, delta=moving_precision)
            self.assertAlmostEqual(angles['yaw'], 1.0, delta=moving_precision)
            self.assertAlmostEqual(angles['pitch'], 0.0, delta=moving_precision)

            res = morse.call_server('PTU', 'get_pan_tilt')
            self.assertAlmostEqual(res[0], 1.0, delta=precision)
            self.assertAlmostEqual(res[1], 0.0, delta=precision)

########################## Run these tests ##########################
if __name__ == "__main__":
    import unittest
    from morse.testing.testing import MorseTestRunner
    suite = unittest.TestLoader().loadTestsFromTestCase(PTUTest)
    sys.exit(not MorseTestRunner().run(suite).wasSuccessful())

