from datetime import datetime, timedelta
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


class ControllerValue:
    def __init__(self, tag, eng_units="", value=0, threshold=0.001):
        self.tag = tag
        self.eng_units = eng_units
        self.value = value
        self.timestamp = datetime.now()
        self.threshold = threshold

    def update_value(self, new_value):
        if abs(new_value - self.value) > self.threshold\
                or datetime.now() - self.timestamp >= timedelta(hours=1):
            #print("Update {} {}->{} {}".format(self.tag,self.value,new_value,datetime.now()))
            self.value = new_value
            self.timestamp = datetime.now()

    def __str__(self):
        return "{}:{} = {} {}".format(self.tag, self.value, self.eng_units, self. timestamp)

    @classmethod
    def from_modbus_device_value(cls, meter_register):
        assert isinstance(meter_register, ModbusDeviceFloat32Value)
        return ControllerValue(meter_register.tag, meter_register.eng_units)


class ModbusDeviceValue:

    register_types = {
        "HOLDING": 3,
        "INPUT": 4
    }

    def __init__(self, tag, address, eng_units="", value=0, read_conversion=None, write_conversion=None):
        self.tag = tag
        self.eng_units = eng_units
        self.address = address
        self.value = value
        self.read_conversion = read_conversion

    def get_value_from_modbus_registers(self, registers):
        if self.read_conversion:
            return self.read_conversion(registers)
        else:
            return registers[0]


class ModbusDeviceFloat32Value(ModbusDeviceValue):
    def __init__(self, tag, address, eng_units="", value=0):
        self.tag = tag
        self.eng_units = eng_units
        self.address = address
        self.value = value

        def read_conversion(registers):
            decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=Endian.Big)
            return decoder.decode_32bit_float()

        self.read_conversion = read_conversion

    def __str__(self):
        return "{}:{}={} {}".format(self.address, self.tag, self.value, self.eng_units)


wattson_registers_map = {
    "INPUT": {},
    "HOLDING": {
        768 : ModbusDeviceFloat32Value("Total_Energy_Consumption",768,"kWh"),
        770 : ModbusDeviceFloat32Value("Total_Real_Power",770,"kW"),
        772 : ModbusDeviceFloat32Value("Total_Reactive_Power",772,"kVAR"),
        774 : ModbusDeviceFloat32Value("Total_Apparent_Power",774,"kVA"),
        776 : ModbusDeviceFloat32Value("Average_Voltage_(L-N)",776,"V"),
        778 : ModbusDeviceFloat32Value("Average_Voltage_(L-L)",778,"V"),
        780 : ModbusDeviceFloat32Value("Average_Current",780,"A"),
        782 : ModbusDeviceFloat32Value("Total_(System)_Power_Factor",782,""),
        784 : ModbusDeviceFloat32Value("Frequency",784,"Hz"),
        786 : ModbusDeviceFloat32Value("Sliding_Window_Real_Power_Demand_(Total_of_phases)",786,"kW"),
        788 : ModbusDeviceFloat32Value("Voltage_A-N",788,"V"),
        790 : ModbusDeviceFloat32Value("Voltage_B-N",790,"V"),
        792 : ModbusDeviceFloat32Value("Voltage_C-N",792,"V"),
        794 : ModbusDeviceFloat32Value("Voltage_A-B",794,"V"),
        796 : ModbusDeviceFloat32Value("Voltage_B-C",796,"V"),
        798 : ModbusDeviceFloat32Value("Voltage_A-C",798,"V"),
        800 : ModbusDeviceFloat32Value("Current_A",800,"A"),
        802 : ModbusDeviceFloat32Value("Current_B",802,"A"),
        804 : ModbusDeviceFloat32Value("Current_C",804,"A"),
        806 : ModbusDeviceFloat32Value("Real_Power_A",806,"kW"),
        808 : ModbusDeviceFloat32Value("Real_Power_B",808,"kW"),
        810 : ModbusDeviceFloat32Value("Real_Power_C",810,"kW"),
        812 : ModbusDeviceFloat32Value("Reactive_Power_A",812,"kVAR"),
        814 : ModbusDeviceFloat32Value("Reactive_Power_B",814,"kVAR"),
        816 : ModbusDeviceFloat32Value("Reactive_Power_C",816,"kVAR"),
        818 : ModbusDeviceFloat32Value("Apparent_Power_A",818,"kVA"),
        820 : ModbusDeviceFloat32Value("Apparent_Power_B",820,"kVA"),
        822 : ModbusDeviceFloat32Value("Apparent_Power_C",822,"kVA"),
        824 : ModbusDeviceFloat32Value("Power_Factor_A",824,""),
        826 : ModbusDeviceFloat32Value("Power_Factor_B",826,""),
        828 : ModbusDeviceFloat32Value("Power_Factor_C",828,""),
        830 : ModbusDeviceFloat32Value("Software_Version",830,"Fixed"),
        832 : ModbusDeviceFloat32Value("Import_Energy_(+)_A",832,"KWh"),
        834 : ModbusDeviceFloat32Value("Import_Energy_(+)_B",834,"KWh"),
        836 : ModbusDeviceFloat32Value("Import_Energy_(+)_C",836,"KWh"),
        838 : ModbusDeviceFloat32Value("Total_Import_Energy_(+)_A+B+C",838,"KWh"),
        840 : ModbusDeviceFloat32Value("Export_Energy_(-)_A",840,"KWh"),
        842 : ModbusDeviceFloat32Value("Export_Energy_(-)_B",842,"KWh"),
        844 : ModbusDeviceFloat32Value("Export_Energy_(-)_C",844,"KWh"),
        846 : ModbusDeviceFloat32Value("Total_Export_Energy_(-)_A+B+C",846,"KWh"),
        848 : ModbusDeviceFloat32Value("Net_Total_Energy_(+/-)_A",848,"KWh"),
        850 : ModbusDeviceFloat32Value("Net_Total_Energy_(+/-)_B",850,"KWh"),
        852 : ModbusDeviceFloat32Value("Net_Total_Energy_(+/-)_C",852,"KWh"),
        854 : ModbusDeviceFloat32Value("Net_Total_Energy_(+/-)_A+B+C_(Same_As_0x300)",854,"KWh"),
        856 : ModbusDeviceFloat32Value("Inductive_Energy_(+)_A",856,"kVARh"),
        858 : ModbusDeviceFloat32Value("Inductive_Energy_(+)_B",858,"KVARh"),
        860 : ModbusDeviceFloat32Value("Inductive_Energy_(+)_C",860,"KVARh"),
        862 : ModbusDeviceFloat32Value("Total_Inductive_Energy_(+)_A+B+C",862,"KVARh"),
        864 : ModbusDeviceFloat32Value("Capacitive_Energy_(-)_A",864,"KVARh"),
        866 : ModbusDeviceFloat32Value("Capacitive_Energy_(-)_B",866,"KVARh"),
        868 : ModbusDeviceFloat32Value("Capacitive_Energy_(-)_C",868,"KVARh"),
        870 : ModbusDeviceFloat32Value("Total_Capacitive_Energy_(-)_A+B+C",870,"KVARh"),
        872 : ModbusDeviceFloat32Value("Net_Total_VARh_(+/-)_A",872,"KVARh"),
        874 : ModbusDeviceFloat32Value("Net_Total_VARh_(+/-)_B",874,"KVARh"),
        876 : ModbusDeviceFloat32Value("Net_Total_VARh_(+/-)_C",876,"KVARh"),
        878 : ModbusDeviceFloat32Value("Net_Total_VARh_(+/-)_A+B+C",878,"KVARh"),
        880 : ModbusDeviceFloat32Value("Total_VAh_A",880,"KVAh"),
        882 : ModbusDeviceFloat32Value("Total_VAh_B",882,"KVAh"),
        884 : ModbusDeviceFloat32Value("Total_VAh_C",884,"KVAh"),
        886 : ModbusDeviceFloat32Value("Total_VAh_(A+B+C)",886,"KVAh"),
        }

}
