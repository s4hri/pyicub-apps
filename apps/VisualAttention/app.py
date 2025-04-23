"""
BSD 2-Clause License

Copyright (c) 2025, Social Cognition in Human-Robot Interaction,
                    Istituto Italiano di Tecnologia, Genova

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Author:
    - Davide De Tommaso (davide.detommaso@iit.it)
"""

import yarp
import sys
from pyicub.controllers.gaze import GazeController
from pyicub.core.logger import YarpLogger
from pyicub.modules.attention import VisualAttention
from pyicub.core.logger import YarpLogger

VOCAB_QUIT = yarp.createVocab32("q", "u", "i", "t")

class VisualAttentionModule(yarp.RFModule):

    def __init__(self):
        super().__init__()
        self.period = 0.1
        self.logs = YarpLogger.getLogger()
        self.gazectrl = GazeController('icubSim',self.logs)
        self.attention = VisualAttention(self.gazectrl)
        self.cmd_port = yarp.Port()

    def configure(self, rf):
        self.logs.info("[%s] Configuring module..." % self.getName())
        self.period = rf.check("period") and rf.find("period").asFloat64() or 0.1
        self.gazectrl.init()

        self.cmd_port.open("/%s/cmd:rpc" % self.getName())
        self.attach(self.cmd_port)

        self.logs.info("[%s] Module configured successfully." % self.getName())
        return True

    def getName(self):
        return self.__class__.__name__

    def getPeriod(self):
        return self.period

    def updateModule(self):
        # Placeholder for periodic updates, if required
        return True

    def respond(self, command, reply):
        self.logs.info("[%s] Received command: %s" % (self.getName(), command.toString()))

        # Cmd example: observe_scene (center (-1.0 0.0 0.5)) (width 0.5) (height 0.5)
        if command.check("observe_scene"):
            center = tuple(map(float, command.find("center").toString().split()))
            width = command.find("width").asFloat64()
            height = command.find("height").asFloat64()
            try:
                self.attention.observe_scene(center, width, height)
            except Exception as e:
                self.logs.error("Error in observe_scene: %s" % str(e))
                reply.addString("nack")
                reply.addString("error in observe_scene")
                return True
            reply.addString("ack")
            return True

        elif command.get(0).asVocab() == VOCAB_QUIT:
            reply.addString("bye")
            return False

        else:
            reply.addString("nack")
            reply.addString("unknown command")
            return True

    def interruptModule(self):
        self.logs.info("[%s] Interrupting module..." % self.getName())
        self.cmd_port.interrupt()
        return True

    def close(self):
        self.logs.info("[%s] Closing module..." % self.getName())
        self.cmd_port.close()
        return True


if __name__ == "__main__":
    yarp.Network.init()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.setDefaultContext("VisualAttentionModule")
    rf.setDefaultConfigFile("config.ini")
    rf.configure(sys.argv)

    module = VisualAttentionModule()
    module.runModule(rf)
