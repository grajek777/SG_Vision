# This file provides functionalities for Motor Controller Tic T825
# Restrictions are set for the following motor:
# Emis Stepmotor E547-52500 SM 42051
# Voltage: 12 V
# Stop momentum: 0.25 Nm
# Phase current: 0.6 A
# Commands for Tic T825: https://www.pololu.com/docs/0J71/8

import smbus2
import time

class ConstTicT825(object):
    SET_TARGET_POSTION=0xE0
    SET_TARGET_VELOCITY=0xE3
    HALT_AND_SET_POSITION=0xEC
    HALT_AND_HOLD=0x89
    RESET_CMD_TIMEOUT=0x8C
    DE_ENERGIZE=0x86
    ENERGIZE=0x85
    EXIT_SAFE_START=0x83
    ENTER_SAFE_START=0x8F
    RESET=0xB0
    CLEAR_DRIVER_ERROR=0x8A
    SET_MAX_SPEED=0xE6
    SET_STARTING_SPEED=0xE5
    SET_MAX_ACCELERATION=0xEA
    SET_MAX_DECELERATION=0xE9
    SET_STEP_MODE=0x94
    SET_CURRENT_LIMIT=0x91
    SET_DECAY_MODE=0x92
    GET_VARIABLE=0xA1
    GET_VARIABLE_AND_CLR_ERRORS=0xA2
    GET_SETTING=0xA8
    # motor parameters
    MAX_SPEED=2000000
    MAX_ACC=40000
    MAX_CURRENT=14
    MC_CMD_TIMEOUT=1.0

class MCTicT825(ConstTicT825):
    
    def __init__(self, addr):
        self.i2c_addr = addr
        self.mc = smbus2.SMBus(3)
        
        # set motor restrictions. The following commands will overwrite the data
        # kept in non-volatile memory to make sure that they are correct.
        self.setStepMode('Full')
        self.setMaxSpeed(self.MAX_SPEED) # microsteps per 10,000 s
        self.setStartingSpeed(0)
        self.setMaxAcceleration(self.MAX_ACC) # microsteps per 100 s^2
        self.setMaxDeceleration(self.MAX_ACC)
        self.setCurrentLimit(self.MAX_CURRENT) # units of 32 milliamps
        self.setDecayMode('Mixed')
        
    
    def close(self):
        self.mc.close()
        
    def reverseByteOrder(self, data):
        "Reverses the byte order of an int (16-bit) or long (32-bit) value"
        # Courtesy Vishal Sapre
        byteCount = len(hex(data)[2:].replace('L','')[::2])
        val       = 0
        for i in range(byteCount):
          val    = (val << 8) | (data & 0xff)
          data >>= 8
        return val
    
    def wordToList(self, data):
        dstr = hex(data)[2:].replace('L','')
        byteCount = len(dstr[::2])
        list = []
        for i, n in enumerate(range(byteCount)):
            d = data & 0xFF
            list.append(d)
            data >>= 8
        for j in range(int((byteCount+4)/4)*4-byteCount):
            if data >= 0:
                list.append(0x00)
            else:
                list.append(0xFF)
        return list
        
    def write32Bit(self, cmd, word):
        list = self.wordToList(word)
        self.mc.write_i2c_block_data(self.i2c_addr, cmd, list)
    
    def setTargetPosition(self, position):
        self.write32Bit(self.SET_TARGET_POSTION, position)

    def setTargetVelocity(self, velocity):
        self.write32Bit(self.SET_TARGET_VELOCITY, velocity)

    def haltAndSetPosition(self, position):
        self.write32Bit(self.HALT_AND_SET_POSITION, position)
    
    def haltAndHold(self):
        self.mc.write_byte(self.i2c_addr, self.HALT_AND_HOLD)

    def resetCommandTimeout(self):
        self.mc.write_byte(self.i2c_addr, self.RESET_CMD_TIMEOUT)
    
    def energize(self):
        self.mc.write_byte(self.i2c_addr, self.ENERGIZE)
            
    def deenergize(self):
        self.mc.write_byte(self.i2c_addr, self.DE_ENERGIZE)

    def enterSafeStart(self):
        self.mc.write_byte(self.i2c_addr, self.ENTER_SAFE_START)

    def exitSafeStart(self):
        self.mc.write_byte(self.i2c_addr, self.EXIT_SAFE_START)
    
    def reset(self):
        self.mc.write_byte(self.i2c_addr, self.RESET)
    
    def clearDriverError(self):
        self.mc.write_byte(self.i2c_addr, self.CLEAR_DRIVER_ERROR)
    
    def setMaxSpeed(self, speed):
        self.write32Bit(self.SET_MAX_SPEED, speed)
        
    def setStartingSpeed(self, speed):
        self.write32Bit(self.SET_STARTING_SPEED, speed)
        
    def setMaxAcceleration(self, acceleration):
        self.write32Bit(self.SET_MAX_ACCELERATION, acceleration)
        
    def setMaxDeceleration(self, deceleration):
        self.write32Bit(self.SET_MAX_DECELERATION, deceleration)
    
    def setStepMode(self, mode):
        dict = {'Full': 0, '1/2': 1, '1/4': 2, '1/8': 3, '1/16': 4, '1/32': 5}
        self.mc.write_byte_data(self.i2c_addr, self.SET_STEP_MODE, dict[mode])
    
    def setCurrentLimit(self, limit):
        self.mc.write_byte_data(self.i2c_addr, self.SET_CURRENT_LIMIT, limit)
    
    def setDecayMode(self, mode):
        dict = {'Mixed': 0, 'Slow': 1, 'Fast': 2}
        self.mc.write_byte_data(self.i2c_addr, self.SET_DECAY_MODE, dict[mode])

    
    # reading varibales according to https://www.pololu.com/docs/0J71/12.9
    # The below methods use smbus2 library and its repeated start transaction
    def getVariables(self, offset, length):
        write = smbus2.i2c_msg.write(self.i2c_addr, [0xA1, offset])
        read = smbus2.i2c_msg.read(self.i2c_addr, length)
        self.mc.i2c_rdwr(write, read)
        return list(read)
        
    def getCurrentPosition(self):
        b = self.getVariables(0x22, 4)
        position = b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
        if position >= (1 << 31):
          position -= (1 << 32)
        return position
    
    def getCurrentVelocity(self):
        b = self.getVariables(0x26, 4)
        velocity = b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
        if velocity >= (1 << 31):
          velocity -= (1 << 32)
        return velocity
    
    def getTargetPosition(self):
        b = self.getVariables(0x0A, 4)
        position = b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
        if position >= (1 << 31):
          position -= (1 << 32)
        return position
    
    def getTargetVelocity(self):
        b = self.getVariables(0x0E, 4)
        velocity = b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
        if velocity >= (1 << 31):
          velocity -= (1 << 32)
        return velocity
    
    def getPlanningMode(self):
        b = self.getVariables(0x09, 1)
        return b
