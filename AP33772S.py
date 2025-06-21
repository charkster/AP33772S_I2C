class AP33772S:

    # Constructor
    def __init__(self, i2c):
        self.i2c      = i2c
        self.slave_id = 0x52

    def write_data(self, address=0x00, data=0x00, num_bytes=0): # write data
        self.i2c.writeto_mem(self.slave_id, address, data.to_bytes(num_bytes, "little")) # MicroPython
#        self.i2c.write_i2c_block_data(self.slave_id, address, list(data.to_bytes(num_bytes,"little"))) # Raspberry Pi

    def read_data(self, address=0x00, num_bytes=1):
        int_read_byte = int.from_bytes(self.i2c.readfrom_mem(self.slave_id, address, num_bytes), "little") # MicroPython
#        int_read_byte = int.from_bytes(bytearray(self.i2c.read_i2c_block_data(self.slave_id, address, num_bytes)), "little") # Raspberry Pi
        return int_read_byte # int value

    _SYSTEM_ADDR    = 0x06
    _VOUT_FORCE_ON  = 0x02
    _VOUT_FORCE_OFF = 0x01
    _VOUT_AUTO      = 0x00
    
    def set_output(self, mode='AUTO'):
        if (mode == 'AUTO'):
            self.write_data(self._SYSTEM_ADDR, self._VOUT_AUTO, 1)
        elif (mode == 'ON'):
            self.write_data(self._SYSTEM_ADDR, self._VOUT_FORCE_ON, 1)
        elif (mode == 'OFF'):
            self.write_data(self._SYSTEM_ADDR, self._VOUT_FORCE_OFF, 1)

    _SRCPDO_ADDR         = 0x20
    _SRCPDO_NUM_PDO      = 13
    _SRCPDO_NUM_BYTES    = 2

    _PDO_TYPE_WIDTH      = 2 # include the detect bit
    _PDO_TYPE_OFFSET     = 14
    _PDO_TYPE_FIXED      = 2
    _PDO_TYPE_PPS        = 3

    _PDO_VOLTAGE_WIDTH   = 8
    _PDO_VOLTAGE_OFFSET  = 0
    _SPR_PDO_VOLTAGE_LSB = 0.1 # 100mV

    _EPR_PDO_VOLTAGE_LSB = 0.2 # 200mV

    _PDO_CURRENT_WIDTH   = 4
    _PDO_CURRENT_OFFSET  = 10
    _PDO_CURRENT_LSB     = 0.25 # 250mA
    _PDO_CURRENT_BASE    = 1.0  # 1.0A

    # a bit field will have an offset and width, and that can be used to extract the bit field value from a larger concatinated value (such as a dword)
    # the offset is the number of single bit shifts, the width can be used to create a bit mask to bitwise-AND with the larger concatinated value, 
    #  to elinimate higher bits which are not part of the bit field. A bit mask is 2 ** width - 1. For example a width of 3 is 2 ** 3 - 1 = 0x07
    def get_pdo(self, num=1):
    
        pdo_word = self.read_data(self._SRCPDO_ADDR+num, num_bytes=self._SRCPDO_NUM_BYTES)
        pdo_type_raw = int((pdo_word >> self._PDO_TYPE_OFFSET) & (2**self._PDO_TYPE_WIDTH-1))
        if (pdo_type_raw == self._PDO_TYPE_FIXED):
            pdo_type = 'FIXED'
        elif(pdo_type_raw == self._PDO_TYPE_PPS and num < 8):
            pdo_type = 'PPS'
        elif(pdo_type_raw == self._PDO_TYPE_PPS):
            pdo_type = 'AVS'
        else:
            pdo_type = 'invalid'
        if (num > 8): # EPR
            voltage = ((pdo_word >> self._PDO_VOLTAGE_OFFSET) & (2**self._PDO_VOLTAGE_WIDTH-1)) * self._EPR_PDO_VOLTAGE_LSB
        else:
            voltage = ((pdo_word >> self._PDO_VOLTAGE_OFFSET) & (2**self._PDO_VOLTAGE_WIDTH-1)) * self._SPR_PDO_VOLTAGE_LSB
        current = ((pdo_word >> self._PDO_CURRENT_OFFSET) & (2**self._PDO_CURRENT_WIDTH-1)) * self._PDO_CURRENT_LSB + self._PDO_CURRENT_BASE
        return [num, pdo_type, voltage, current]
        

    _PDONUM_ADDR = 0x1C
    
    def get_pdo_num(self):
        return self.read_data(address=self._PDONUM_ADDR, num_bytes=1)
    
    _STATUS_ADDR    = 0x01 # ALL BITS ARE CLEARED ON READ
    _MASK_ADDR      = 0x02
    _STATUS_MASK_DR      = 0x80
    _STATUS_MASK_OTP     = 0x40
    _STATUS_MASK_OCP     = 0x20
    _STATUS_MASK_OVP     = 0x10
    _STATUS_MASK_NEWPDO  = 0x04
    _STATUS_MASK_SUCCESS = 0x02
    _STATUS_MASK_READY   = 0x01
    
    def get_pdo_status(self):
        pdo_status = self.read_data(address=self._STATUS_ADDR, num_bytes=1)
        status_list = []
        if (pdo_status & self._STATUS_MASK_READY):
            status_list.append('ready')
        if (pdo_status & self._STATUS_MASK_SUCCESS):
            status_list.append('success')
        if (pdo_status & self._STATUS_MASK_NEWPDO):
            status_list.append('new_pdo')
        if (pdo_status & self._STATUS_MASK_OVP):
            status_list.append('over_voltage')
        if (pdo_status & self._STATUS_MASK_OCP):
            status_list.append('over_current')
        if (pdo_status & self._STATUS_MASK_OTP):
            status_list.append('over_temp')
        if (pdo_status & self._STATUS_MASK_DR):
            status_list.append('derate')
        return status_list

    _VOLTAGE_ADDR = 0x11 # ADC measured VOUT voltage
    _VOLTAGE_LSB  = 0.08 # 80mV
    
    def get_voltage(self):
        return self.read_data(address=self._VOLTAGE_ADDR, num_bytes=1) * self._VOLTAGE_LSB

    _CURRENT_ADDR = 0x12 # ADC measured VBUS current
    _CURRENT_LSB  = 0.024 # 24mA
    
    def get_current(self):
        return self.read_data(address=self._CURRENT_ADDR, num_bytes=1) * self._CURRENT_LSB

    _TEMP_ADDR = 0x13 # NTC Temperature, LSB is 1C

    def get_temp(self):
        return self.read_data(address=self._TEMP_ADDR, num_bytes=1) # LSB is 1C

    _RDO_ADDR      = 0x31 # Requested Data Object
    _RDO_NUM_BYTES = 2
    _RDO_POSITION_WIDTH  = 4 # Not needed as value 1 thru 7 fits into 3bits
    _RDO_POSITION_OFFSET = 12

    _RDO_OP_CURRENT_WIDTH   = 4
    _RDO_OP_CURRENT_OFFSET  = 8
    _RDO_OP_CURRENT_LSB     = 0.25 # 250mA

    _RDO_OP_VOLTAGE_WIDTH   = 8
    _RDO_OP_VOLTAGE_OFFSET  = 0
    _RDO_SPR_OP_VOLTAGE_LSB = 0.1 # 100mV
    _RDO_EPR_OP_VOLTAGE_LSB = 0.2 # 200mV

    _RDO_RESET_ADDR = 0x32
    _RDO_RESET_CMD  = 0x01

    def set_rdo(self, pdo_num=1, voltage=0.0, op_current=0.0):
        rdo_word = 0
        rdo_word = rdo_word + ((pdo_num & (2**self._RDO_POSITION_WIDTH-1)) << self._RDO_POSITION_OFFSET)
        if (pdo_num < 8):
            rdo_word = rdo_word + ((int( voltage/self._RDO_SPR_OP_VOLTAGE_LSB) & (2**self._RDO_OP_VOLTAGE_WIDTH-1)) << self._RDO_OP_VOLTAGE_OFFSET)
        else:
            rdo_word = rdo_word + ((int( voltage/self._RDO_EPR_OP_VOLTAGE_LSB) & (2**self._RDO_OP_VOLTAGE_WIDTH-1)) << self._RDO_OP_VOLTAGE_OFFSET)
        rdo_word = rdo_word + ((int((op_current-1.0)/self._RDO_OP_CURRENT_LSB) & (2**self._RDO_OP_CURRENT_WIDTH-1)) << self._RDO_OP_CURRENT_OFFSET)
        # print("0x{:04x}".format(rdo_word))
        self.write_data(self._RDO_ADDR, rdo_word, self._RDO_NUM_BYTES)

    def set_rdo_reset(self):
        self.write_data(self._RDO_RESET_ADDR, self._RDO_RESET_CMD, 1)