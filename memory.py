class Memory:
    def __init__(self):
        self._data = [0] * 65536

    def read_byte(self, address):
        return self._data[address]

    def read_word(self, address):
        # 小端
        low = self._data[address]
        high = self._data[address + 1]
        v = (high << 8) + low
        return v

    def write_byte(self, address, value):
        self._data[address] = value
