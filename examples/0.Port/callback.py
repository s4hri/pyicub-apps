import yarp
from pyicub.core.ports import BufferedReadPort
from threading import Thread
from random import randint


class Reader:
    def __init__(self):
        self.port = BufferedReadPort("/reader:i", "/writer:o", callback=self.detectMsg)
    
    def detectMsg(self, bot):
        msg  = "READER receiving : " + bot.toString()
        yarp.Log("",0,"").debug(msg)
        return True


class Writer:
    def __init__(self):
        self.port = yarp.BufferedPortBottle()
        self.port.open("/writer:o")
    
    def sendMsg (self, top):
        for i in range (1, top):
            bot = self.port.prepare()
            bot.clear()
            bot.addString("item ")
            bot.addInt32(i)
            self.port.write()
            yarp.delay(randint(1,5))



if __name__ == '__main__':

    yarp.Network.init()

    writer = Writer()
    yarp.Log("",0,"").debug("init WRITER")
    reader = Reader()
    yarp.Log("",0,"").debug("init READER")

    yarp.Log("",0,"").debug("start writing")
    writing = Thread(target=writer.sendMsg(10))
    writing.start()
    writing.join()
    yarp.Log("",0,"").debug("end writing")

    yarp.Network.fini()