from abc import abstractmethod
from threading import Lock
import yarp
from pyicub.core.logger import YarpLogger
from pyicub.core.ports import BufferedReadPort
from utilities.RobotCam import RobotCam
from utilities.common import getGazeController, getRobotName

## ===== UTILITES METHODS =====



class gazeFollower(yarp.RFModule):
    def __init__(self, name):
        yarp.RFModule.__init__(self)
        self.log  = YarpLogger.getLogger()
        self.name      = name
        self.log.info("Init " + str(self.name) + "...")
        #
        self.robotName  = getRobotName(self.log)
        self.gaze       = getGazeController(self.robotName, self.log)        
        self.resolution = RobotCam(self.robotName).getResolution()
        self.period     = 0.1
        self.inPort     = None
        self.srcPort    = None
        self.stop       = False
        self.lock       = Lock()
        #
        self.log.info("Init " + str(self.name) + " done.")

##------ RFMODULE METHODS    
    def configure(self, rf):
        self.log.info("Configure " + self.name + "...")
        # srcPort
        if rf.check("srcPort"):
            self.srcPort = rf.find("srcPort").asString()
        self.inPort  = BufferedReadPort("/" + self.name + ":i", self.srcPort, callback=self.callback)
        # period
        if rf.check("period"):
            self.period = rf.find("period").asFloat64()
        self.log.info("Configure " + self.name + " done.")
        return not self.stop
    
    def getPeriod(self):
        return self.period
    
    def updateModule(self):
        return not self.stop
        
    def interruptModule(self):
        self.log.info("interrupting " + self.name + "...")
        self.stop = True
        self.lock.acquire()
        self.gaze.lookAtAbsAngles(0.0, 0.0, 5.0)
        self.lock.release()
        self.log.info("interrupting " + self.name + " done.")
        return self.stop
    
    def close(self):
        self.log.info("closing " + self.name + "...")
        self.gaze.PolyDriver.close()
        self.log.info("closing " + self.name + " done.")
        return self.stop

##------ PRIVATE METHODS
    def __resizePixel__(sefl, pixel, resolution):
        X_ICUB = 320
        Y_ICUB = 240 
        resizedPixel = yarp.Vector(2)
        resizedPixel.set(0, pixel[0]/(resolution[0]/X_ICUB))
        resizedPixel.set(1, pixel[1]/(resolution[1]/Y_ICUB))
        return resizedPixel

    ## CUSTOMS METHODS
    def lookAtMonoPixel(self, pixel):
        self.lock.acquire()
        if not self.stop:
            self.log.debug("START movement")
            self.gaze.IGazeControl.lookAtMonoPixelSync(0, pixel, 0.8)
            self.gaze.IGazeControl.waitMotionDone()
            self.log.debug("END movement")
        self.lock.release()
        return True

    def callback(self, bot):
        pixelTarget  = self.getPixelTarget(bot)
        resizedPixel = self.__resizePixel__(pixelTarget, self.resolution)
        self.lookAtMonoPixel(resizedPixel)
    
    @abstractmethod
    def getPixelTarget(self, bot):
        pass