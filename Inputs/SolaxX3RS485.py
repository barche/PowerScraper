from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from twisted.internet import defer, reactor, protocol
from twisted.web.client import Agent, readBody
from pymodbus.constants import Defaults
from twisted.web.http_headers import Headers
from struct import unpack
import os
import time

# import pprint
# pp = pprint.PrettyPrinter(indent=4)

Defaults.UnitId = 1

LOOP_COUNT = 0
ERROR_COUNT = 0

def unsigned16(result, addr):
    return result.getRegister(addr)

def join_msb_lsb(msb, lsb):
    return (msb << 16) | lsb

def read_powerlimit(filename):
    try:
        # Check if the file exists
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"The file {filename} does not exist.")
        
        # Get the current time and file modification time
        current_time = time.time()
        file_mod_time = os.path.getmtime(filename)
        
        # Check if the file is older than an hour
        if (current_time - file_mod_time) > 3600:
            return 100
        
        # Read the number from the file
        with open(filename, 'r') as file:
            number = file.read().strip()
            
            # Convert the number to an integer
            return int(number)
    
    except Exception as e:
        print(f"Error reading power limit: {e}")
        return 100

class SolaxX3RS485(object):

    ##
    # Create a new class to fetch data from the Modbus interface of Solax inverters
    def __init__(self, port, baudrate, parity, stopbits, timeout):
        self.port = port
        self.client = ModbusSerialClient(method="rtu", port=self.port, baudrate=baudrate, parity=parity,
                                         stopbits=stopbits, timeout=timeout, bytesize=8)
        print("Solax setup complete")
        
    def fetch(self, completionCallback):
        
        global LOOP_COUNT
        LOOP_COUNT += 1

        if LOOP_COUNT % 20 == 0:
            plim = read_powerlimit("/tmp/solarpowerlimit.txt")
            wrresult = self.client.write_register(0X600, 6868)
            time.sleep(2)
            wrresult = self.client.write_register(0X60F, plim)
            print("Set power limit with result", wrresult)
            return

        #result2 = self.client.read_holding_registers(0X332, 1)
        #print("result", unsigned16(result2, 0))
        #return

       
        result = self.client.read_input_registers(0X400, 53)
        if isinstance(result, ModbusException):
            print("Exception from SolaxX3RS485: {}".format(result))
            return
        
        self.vals = {}
        self.vals['name'] = 'USB0';
        self.vals['Pv1 input voltage'] = unsigned16(result, 0) / 10
        self.vals['Pv2 input voltage'] = unsigned16(result, 1) / 10
        self.vals['Pv1 input current'] = unsigned16(result, 2) / 10
        self.vals['Pv2 input current'] = unsigned16(result, 3) / 10
        self.vals['Grid Voltage Phase 1'] = unsigned16(result, 4) / 10
        self.vals['Grid Voltage Phase 2'] = unsigned16(result, 5) / 10
        self.vals['Grid Voltage Phase 3'] = unsigned16(result, 6) / 10
        self.vals['Grid Frequency Phase 1'] = unsigned16(result, 7) / 100
        self.vals['Grid Frequency Phase 2'] = unsigned16(result, 8) / 100
        self.vals['Grid Frequency Phase 3'] = unsigned16(result, 9) / 100
        self.vals['Output Current Phase 1'] = unsigned16(result, 10) / 10
        self.vals['Output Current Phase 2'] = unsigned16(result, 11) / 10
        self.vals['Output Current Phase 3'] = unsigned16(result, 12) / 10
        self.vals['Temperature'] = unsigned16(result, 13)
        self.vals['Inverter Power'] = unsigned16(result, 14)
        self.vals['RunMode'] = unsigned16(result, 15)
        self.vals['Output Power Phase 1'] = unsigned16(result, 16)
        self.vals['Output Power Phase 2'] = unsigned16(result, 17)
        self.vals['Output Power Phase 3'] = unsigned16(result, 18)
        self.vals['Total DC Power'] = unsigned16(result, 19)
        self.vals['PV1 DC Power'] = unsigned16(result, 20)
        self.vals['PV2 DC Power'] = unsigned16(result, 21)
        self.vals['Fault value of Phase 1 Voltage'] = unsigned16(result, 22) / 10
        self.vals['Fault value of Phase 2 Voltage'] = unsigned16(result, 23) / 10
        self.vals['Fault value of Phase 3 Voltage'] = unsigned16(result, 24) / 10
        self.vals['Fault value of Phase 1 Frequency'] = unsigned16(result, 25) / 100
        self.vals['Fault value of Phase 2 Frequency'] = unsigned16(result, 26) / 100
        self.vals['Fault value of Phase 3 Frequency'] = unsigned16(result, 27) / 100
        self.vals['Fault value of Phase 1 DCI'] = unsigned16(result, 28) / 1000
        self.vals['Fault value of Phase 2 DCI'] = unsigned16(result, 29) / 1000
        self.vals['Fault value of Phase 3 DCI'] = unsigned16(result, 30) / 1000
        self.vals['Fault value of PV1 Voltage'] = unsigned16(result, 31) / 10
        self.vals['Fault value of PV2 Voltage'] = unsigned16(result, 32) / 10
        self.vals['Fault value of Temperature'] = unsigned16(result, 33)
        self.vals['Fault value of GFCI'] = unsigned16(result, 34) / 1000
        self.vals['Total Yield'] = join_msb_lsb(unsigned16(result, 36), unsigned16(result, 35)) / 1000
        self.vals['Yield Today'] = join_msb_lsb(unsigned16(result, 38), unsigned16(result, 37)) / 1000
        
        completionCallback(self.vals)
