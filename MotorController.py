from MCTicT825 import *
import threading
import time

class MotorController(object):
    
    def __init__(self, keep_alive=False):
        MC_i2c_addr = 0x0e
        self.dir_factor = {'down': 1, 'up': -1}
        try:
            self.ticT825 = MCTicT825(MC_i2c_addr)
            self.velocity = 0
            self.direction = 'down'
            self.keep_alive = keep_alive
            # run thread that prevent cmd timeout error
            self.keepAliveThread = None
            if keep_alive:
                self.keepAliveThread = myThread(self.ticT825, (self.ticT825.MC_CMD_TIMEOUT/4.0))
                self.keepAliveThread.start()
        except IOError as e:
            self.ticT825 = None
            raise
    
    @classmethod
    def create_MC(cls, keep_alive=False):
        try:
            return cls(keep_alive)
        except IOError as e:
            return None
        
    def energizeMotor(self):
        self.ticT825.exitSafeStart()
        self.ticT825.energize()
        
    def deenergizeMotor(self):
        self.ticT825.deenergize()
        
    def setTargetMotorVelo(self, velocity):
        self.velocity = velocity
        self.ticT825.setTargetVelocity(self.dir_factor[self.direction]*self.velocity)
    
    def updateMotorDirection(self, dir):
        self.direction = dir
        self.ticT825.setTargetVelocity(self.dir_factor[self.direction]*self.velocity)
    
    def shutdown(self):
        if self.keepAliveThread:
            self.keepAliveThread.stop()
            self.keepAliveThread.join()
        
        self.setTargetMotorVelo(0)
        self.updateMotorDirection('down')
        self.deenergizeMotor()
        self.ticT825.close()   
         

class myThread (threading.Thread):
    def __init__(self, contr, delay=0.5, debug=False):
        threading.Thread.__init__(self)
        self.controller = contr
        self.delay = delay
        self.thread_active = True
        self.debug = debug
     
    def keepAlive(self):
        while self.thread_active:
            if self.debug:
                print "%s" % (time.ctime(time.time()))
            try:
                self.controller.resetCommandTimeout()
            except IOError as e:
                # in case of controller command error, ignore it
                pass
            time.sleep(self.delay)
    
    def stop(self):
        self.thread_active = False
        
    def run(self):
        self.keepAlive()
