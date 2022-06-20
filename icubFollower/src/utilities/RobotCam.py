from cgitb import reset
import yarp
from pyicub.core.logger import YarpLogger


class RobotCam:

##------ CONSTRUCTOR
    def __init__(self, robotName, side="right"):
        self.log        = YarpLogger.getLogger()
        self.log.info("Init RobotCam ... ")
        self.robotName  = robotName
        self.portName   = self.__getPortName__(self.robotName, side, self.log)
        self.portNum    = self.__getPortNum__(self.portName, self.log)
        self.resolution = self.__getResolution__(self.portName, self.log)
        self.log.info("Init RobotCam done.")

##------ PRIVATE METHODS
    def __getPortName__(self, robotName, side, log):
        res = None
        if robotName == "icubSim":
           res = "/"+robotName+"/cam/"+side
        elif robotName == "icub":
           res = "/"+robotName+"/camcalib/"+side+"/out"
        log.info("Port Name: " + res)
        return res
        
    def __getPortNum__(self, portName, log):
        res = None
        port = yarp.Network.queryName(portName)
        if port.isValid():
            res = port.getPort()
        log.info("Port Number: " + str(res))
        return res

    def __getResolution__(self, portName, log):
        res = None
        portImg = yarp.BufferedPortImageRgb()
        portImg.open("/read/image:i")
        if yarp.Network.connect(portName, portImg.getName()):
            img = portImg.read()
            res = [img.width(), img.height()]
            yarp.Network.disconnect(portName, portImg.getName())
            portImg.interrupt()
            portImg.close()
        log.info("Resolution: " + str(res))
        return res

##------ PUBLIC METHODS
    def getPortNum(self):
        return self.portNum

    def getResolution(self):
        return self.resolution

