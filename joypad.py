class Key:
    @property
    def status(self):
        return 1 if self._pressed else 0

    def __init__(self, name):
        self.name = name
        self._pressed = False

    def key_down(self):
        self._pressed = True

    def key_up(self):
        self._pressed = False


class Joypad:
    def __init__(self):
        self._strobe = False
        self._index = 0
        self._setup()

    def _setup(self):
        self.a = Key('a')
        self.b = Key('b')
        self.select = Key('select')
        self.start = Key('start')
        self.up = Key('up')
        self.down = Key('down')
        self.left = Key('left')
        self.right = Key('right')
        self._keys = [
            self.a,
            self.b,
            self.select,
            self.start,
            self.up,
            self.down,
            self.left,
            self.right,
        ]

    def read(self):
        if self._index > 7:
            return 1
        if not self._strobe:
            b = self._keys[self._index]
            self._index += 1
            return b.status

    def write(self, data):
        self._strobe = ((data & 1) == 1)
        if self._strobe:
            self._index = 0
