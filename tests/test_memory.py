from memory import *


def test_ram():
    m = RAM(200)
    v1 = m.read_byte(0)
    v2 = 2
    a = 30
    m.write_byte(a, v2)
    v3 = m.read_byte(a)
    assert v1 == 0, v1
    assert v3 == v2, v3


# def test_read_word():
#     low = 0x34
#     high = 0x12
#     a = 100
#     m.write_byte(a, low)
#     m.write_byte(a+1, high)
#     v = m.read_word(a)
#     assert v == 0x1234, v
#
#
# def test_write_world():
#     v1 = 0x1234
#     a = 110
#     m.write_word(a, v1)
#     v2 = m.read_word(a)
#     assert v1 == v2, v2
