class MemoryWrite:
    def _write(self, address, data):
        raise NotImplementedError()

    def write_byte(self, address, data):
        return self._write(address, data)

    def write_word(self, address, data):
        low = data & 0xFF
        high = (data >> 8) & 0xFF
        self.write_byte(address, low)
        self.write_byte(address+1, high)
