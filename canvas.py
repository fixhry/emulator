import pygame
import math
import time
from random import random


from utils import *


class Canvas:
    def __init__(self, size):
        self.size = size
        self._canvas = pygame.display.set_mode(self.size)
        self.running = True
        s = self._canvas.get_size()

    def draw_point(self, x, y, color):
        w, h = self.size
        if x < w and y < h:
            self._canvas.set_at((x, y), color)

    def draw_line(self, x, y, length, color):
        i = 0
        while i < length:
            self.draw_point(x, y, color)
            x += 1
            i += 1

    def draw_rect(self, x, y, height, width, color):
        for i in range(height):
            self.draw_line(x, y, width, color)
            y += 1

    def update(self, mouse_down, pos):
        pass

    def clear(self):
        pass

    def draw(self):
        x, y = 50, 50
        r1 = math.floor(random() * 255)
        r2 = math.floor(random() * 255)
        r3 = math.floor(random() * 255)
        color = (r1, r2, r3)
        self.draw_rect(x, y, 100, 100, color)

    def display(self):
        fps = 30
        clock = pygame.time.Clock()

        while self.running:
            pygame.display.flip()
            clock.tick(fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.update(1, event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.update(0, event.pos)

            self.draw()


def main():
    s = (300, 300)
    canvas = Canvas(s)
    canvas.display()


if __name__ == '__main__':
    main()
