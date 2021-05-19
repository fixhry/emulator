class MemoryRead:
    def _read(self, address):
        raise NotImplementedError()

    def read_byte(self, address):
        return self._read(address)

    def read_word(self, address):
        # 小端
        low = self._read(address)
        high = self._read(address+1)
        v = (high << 8) + low
        return v

