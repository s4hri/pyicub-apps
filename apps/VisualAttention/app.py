import yarp
import sys
from pyicub.controllers.gaze import GazeController
from pyicub.core.logger import YarpLogger
from pyicub.modules.attention import VisualAttention

VOCAB_QUIT = yarp.createVocab32("q", "u", "i", "t")

class VisualAttentionModule(yarp.RFModule):

    def __init__(self):
        super().__init__()
        self.period = 0.1
        self.logs = YarpLogger.getLogger()
        self.gazectrl = GazeController('icubSim', self.logs)
        self.attention = VisualAttention(self.gazectrl)
        self.cmd_port = yarp.Port()
        self.track_robot_xyz_port = yarp.BufferedPortBottle()
        self.track_camera_uv_port = yarp.BufferedPortBottle()
        self.tracking_robot_active = False
        self.tracking_camera_active = False
        self.tracking_camera = None
        self.tracking_z = None

    def configure(self, rf):
        self.logs.info("[%s] Configuring module..." % self.getName())
        self.period = rf.check("period") and rf.find("period").asFloat64() or 0.1
        self.gazectrl.init()

        self.cmd_port.open("/%s/cmd:rpc" % self.getName())
        self.track_robot_xyz_port.open("/%s/track_robot_xyz:i" % self.getName())
        self.track_camera_uv_port.open("/%s/track_camera_uv:i" % self.getName())
        self.attach(self.cmd_port)

        self.logs.info("[%s] Module configured successfully." % self.getName())
        return True

    def getName(self):
        return self.__class__.__name__

    def getPeriod(self):
        return self.period

    def updateModule(self):
        if self.tracking_robot_active:
            bottle = self.track_robot_xyz_port.read(False)
            if bottle and bottle.size() == 3:
                    x = bottle.get(0).asFloat64()
                    y = bottle.get(1).asFloat64()
                    z = bottle.get(2).asFloat64()
                    self.attention.observe_points([(x, y, z)], fixation_time=0.1)
        elif self.tracking_camera_active:
            bottle = self.track_camera_uv_port.read(False)
            if bottle and bottle.size() == 2:
                u = bottle.get(0).asInt32()
                v = bottle.get(1).asInt32()
                pixel_vector = yarp.Vector(2)
                pixel_vector[0] = u
                pixel_vector[1] = v
                point = yarp.Vector(3)
                self.gazectrl.IGazeControl.get3DPoint(self.tracking_camera, pixel_vector, self.tracking_z, point)
                self.attention.observe_points([(point[0], point[1], point[2])], fixation_time=0.1)
                #print(self.tracking_camera, pixel_vector[0], pixel_vector[1], self.tracking_z)
                #self.gazectrl.IGazeControl.lookAtMonoPixel(self.tracking_camera, pixel_vector, self.tracking_z)
        return True

    def respond(self, command, reply):
        self.logs.info("[%s] Received command: %s" % (self.getName(), command.toString()))

        try:
            if command.get(0).asString() == "start_robot_tracking":
                self.tracking_robot_active = True
                reply.addString("robot_tracking_started")
                return True

            elif command.get(0).asString() == "stop_robot_tracking":
                self.tracking_robot_active = False
                reply.addString("robot_tracking_stopped")
                return True

            elif command.get(0).asString() == "stop_camera_tracking":
                self.tracking_camera_active = False
                reply.addString("camera_tracking_stopped")
                return True
                
            # Cmd example: start_camera_tracking (camera 0) (z 0.5)
            elif command.check("start_camera_tracking"):
                self.tracking_camera_active = True
                self.tracking_camera = command.find("camera").asInt32()
                self.tracking_z = command.find("z").asFloat64()
                reply.addString("camera_tracking_started")
                return True

            # Cmd example: observe_scene (center (-1.0 0.0 0.5)) (width 0.5) (height 0.5)
            elif command.check("observe_scene"):
                center = tuple(map(float, command.find("center").toString().split()))
                width = command.find("width").asFloat64()
                height = command.find("height").asFloat64()
                self.attention.observe_scene(center, width, height)
                reply.addString("ack")
                return True

            elif command.check("observe_workspace"):
                center = tuple(map(float, command.find("center").toString().split()))
                width = command.find("width").asFloat64()
                depth = command.find("depth").asFloat64()
                self.attention.observe_workspace(center, width, depth)
                reply.addString("ack")
                return True

            elif command.get(0).asVocab() == VOCAB_QUIT:
                reply.addString("bye")
                return False

            else:
                reply.addString("nack")
                reply.addString("unknown command")
                return True

        except Exception as e:
            self.logs.error("Error executing command: %s" % str(e))
            reply.addString("nack")
            reply.addString("error executing command")
            return True

    def interruptModule(self):
        self.logs.info("[%s] Interrupting module..." % self.getName())
        self.cmd_port.interrupt()
        self.track_robot_xyz_port.interrupt()
        self.track_camera_uv_port.interrupt()
        return True

    def close(self):
        self.logs.info("[%s] Closing module..." % self.getName())
        self.cmd_port.close()
        self.track_robot_xyz_port.close()
        self.track_camera_uv_port.close()
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
