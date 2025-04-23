#!/usr/bin/python3

# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# Copyright (C) 2006-2010 RobotCub Consortium
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.
import yarp
import sys
from pyicub.core.logger import YarpLogger
from utilities.GazeFollower import gazeFollower


class faceFollower(gazeFollower):
    def __init__(self, srcPort):
        gazeFollower.__init__(self, "faceFollower")
        self.srcPort = srcPort
        # custom for faceFollower
        self.indexFace  = 0
        self.indexPixel = 27  # center eyes
        
    def getPixelTarget(self, bot):
        pixel  = yarp.Vector(2)
        pixel[0] = bot.get(self.indexFace).asList().get(self.indexPixel).asList().get(0).asInt32()
        pixel[1] = bot.get(self.indexFace).asList().get(self.indexPixel).asList().get(1).asInt32()
        return pixel


if __name__ == '__main__':
    
    yarp.Network.init()
    
    logs = YarpLogger.getLogger()

    face = faceFollower("/faceLandmarks/landmarks:o")
    rf = yarp.ResourceFinder()
    rf.configure(sys.argv)
    face.configure(rf)
    logs.info("Start " + face.name + "...")
    face.runModule()
    logs.info("Main returning...")