import os
from pyicub.controllers.gaze import GazeController

##------ UTILITES METHODS
def getRobotName(log):
    res = None
    SIMULATION = os.getenv('ICUB_SIMULATION')
    if SIMULATION == 'true':
        res = "icubSim"
    else:
        res = "icub"
    log.info("Robot Name: " + res)
    return res


def getGazeController(robotName, log):
    gaze = GazeController(robotName, log)
    if gaze.isValid():
        gaze.init()
    return gaze
