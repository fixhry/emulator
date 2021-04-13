from memory import *


m = Memory()


def test_read_byte():
    v1 = m.read_byte(0)
    assert v1 == 0


def test_write_byte():
    v1 = 2
    a = 30
    m.write_byte(a, v1)
    v2 = m.read_byte(a)
    assert v2 == v1, v2


def test_read_word():
    low = 0x34
    high = 0x12
    a = 100
    m.write_byte(a, low)
    m.write_byte(a+1, high)
    v = m.read_word(a)
    assert v == 0x1234, v
