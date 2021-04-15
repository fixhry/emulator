from memory import *
from cpu import *
from utils import *

m = Memory()
cpu = CPU(m)


def test_exec():
    cpu.run()

