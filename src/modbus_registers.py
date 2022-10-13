import time
from datetime import datetime

from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ExceptionResponse
import json
from  pymodbus.payload import BinaryPayloadDecoder, Endian, BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient


class ModbusRequest:
    def __init__(self, fc, start=0, stop=0, uid=0, value=0, registers=None):
        self.fc = fc
        self.start = start
        self.stop = stop
        self.uid = uid
        self.value = value
        self.registers = registers

    @classmethod
    def create_read_hold_regs_req(cls, start, count, uid):
        return ModbusRequest(3, start, count, uid)

    @classmethod
    def create_read_input_regs_req(cls, start, count, uid):
        return ModbusRequest(4, start, count, uid)

    @classmethod
    def create_write_register_req(cls, address, value, uid):
        return ModbusRequest(fc=6, start=address, value=value, uid=uid)

    @classmethod
    def create_write_registers_request(cls, start, registers, uid):
        return ModbusRequest(10, start, uid, registers=registers)

    def execute(self, client):
        if self.fc == 3:
            response = client.read_holding_registers(self.start, self.stop, unit=self.uid)
        if self.fc == 4:
            response = client.read_input_registers(self.start, self.stop, unit=self.uid)
        if self.fc == 6:
            response = client.write_register(unit=self.uid, address=self.start, value=int(self.value))
        if self.fc == 10:
            assert isinstance(client, ModbusSerialClient)
            response = client.write_registers(self.start, self.registers)

        if isinstance(response, ExceptionResponse) or isinstance(response, ModbusIOException):
            raise BaseException(str(response))

        if self.fc == 6 or self.fc == 10:
            return "write_ok"

        return response.registers

