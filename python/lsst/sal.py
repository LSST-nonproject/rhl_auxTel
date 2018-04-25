"""
Fake enough of SAL to let my write a notebook illustrating auxTel scripting
"""

__all__ = ["Command", "camera_command_turnOnLaserC", "camera_command_setFilterC"]

import asyncio
import logging
import sys
import time

class Command():
    ACK        = 300
    INPROGRESS = 301
    STALLED    = 302
    COMPLETE   = 303
    NOPERM     = -300
    NOACK      = -301
    FAILED     = -302
    ABORTED    = -303
    TIMEOUT    = -304
    
    def __init__(self, cmdName):
        self._cmdName = cmdName

class SAL_camera():
    __cmdId = -1
    
    def __init__(self):
        self._commands = dict()
        self._pending = dict()

    def salShutdown(self):
        pass

    def __getCmdId(self, cmdName):
        if not cmdName in self._commands:
            raise NameError("Unknown SAL command \"%s\"" % cmdName)

        self.__cmdId += 1
        return self.__cmdId

    def salCommand(self, cmdName):
        self._commands[cmdName] = Command(cmdName)

    def salEvent(self, name):
        pass
    #
    # Commands
    #
    def issueCommand_setFilter(self, data):
        cmdId = self.__getCmdId(data.cmdName)
        self._pending[cmdId] = data

        print("%s Setting %s" % (time.asctime(), self._pending[cmdId].filterName), file=sys.stderr)
        sys.stderr.flush()

        return cmdId

    def waitForCompletion_setFilter(self, cmdId, timeout=0):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        time.sleep(1.5)
        print("%s Set filter to %s" % (time.asctime(), self._pending[cmdId].filterName), file=sys.stderr)
        sys.stderr.flush()
        del self._pending[cmdId]

        return Command.COMPLETE
    
    async def awaitForCompletion_setFilter(self, cmdId, timeout=0):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        await asyncio.sleep(1.5)

        print("%s Set filter to %s" % (time.asctime(), self._pending[cmdId].filterName), file=sys.stderr)
        sys.stderr.flush()
        del self._pending[cmdId]

        return Command.COMPLETE
    
    def issueCommand_turnOnLaser(self, data):
        cmdId = self.__getCmdId(data.cmdName)
        self._pending[cmdId] = data

        print("%s turning laser on" % (time.asctime()), file=sys.stderr)
        sys.stderr.flush()

        return cmdId

    def waitForCompletion_turnOnLaser(self, cmdId, timeout=0):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        time.sleep(2)
        print("%s laser is warm" % (time.asctime()), file=sys.stderr)
        sys.stderr.flush()
        del self._pending[cmdId]

        return Command.COMPLETE

    async def awaitForCompletion_turnOnLaser(self, cmdId, timeout=0):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        await asyncio.sleep(2)
        
        print("%s laser is warm" % (time.asctime()), file=sys.stderr)
        sys.stderr.flush()
        del self._pending[cmdId]

        return Command.COMPLETE

    def issueCommand_cameraIntegrate(self, data):
        cmdId = self.__getCmdId(data.cmdName)
        self._pending[cmdId] = data

        print("%s opening shutter" % (time.asctime()), file=sys.stderr)
        sys.stderr.flush()

        return cmdId

    def getResponse_cameraIntegrate(self, cmdId, timeout=0):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        data = self._pending[cmdId]

        if time.time() < data.time0 + data.expTime:
            return Command.INPROGRESS

        print("%s Shutter closed" % (time.asctime()), file=sys.stderr)
        sys.stderr.flush()

        del self._pending[cmdId]

        Event.getEvent("exposureId").done = True # exposure ID is available

        return Command.COMPLETE

    async def waitForCompletion_cameraIntegrate(self, cmdId, timeout=0, pollTime=0.1):
        if not cmdId in self._pending:
            raise NameError("Command %d not found" % cmdId)

        while True:
            status = self.getResponse_cameraIntegrate(cmdId)
            
            if status == Command.COMPLETE:
                return status

            if timeout > 0 and time.time() > data.time0 + timeout:
                return Command.TIMEOUT

            await asyncio.sleep(pollTime)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    def getEvent_SummaryState(self, event):
        return 0 if event.done else 1

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    
class Data():
    """Base class for all data objects"""

    def __init__(self, cmdName):
        self.cmdName = cmdName
        if cmdName is not None:
            self.log = logging.getLogger(cmdName)
        self.time0 = time.time()

class camera_command_setFilterC(Data): 
    def __init__(self, filterName):
        super().__init__("setFilter")
        self.filterName = filterName
        
class camera_command_turnOnLaserC(Data): 
    def __init__(self):
        super().__init__("turnOnLaser")
        
class camera_command_cameraIntegrateC(Data): 
    def __init__(self, expTime):
        super().__init__("cameraIntegrate")
        self.expTime = expTime

class Event():
    """Base class for all events"""

    _events = {}

    @classmethod
    def getEvent(cls, name):
        return cls._events[name]

    def __init__(self, name):
        self.name = name
        type(self)._events[name] = self

class camera_logevent_exposureIdC(Event):
    nextVisit = 0

    def __init__(self):
        super().__init__("exposureId")
        self.visit = type(self).nextVisit
        self.done = False
        type(self).nextVisit += 1
