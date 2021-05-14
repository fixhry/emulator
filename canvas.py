import pygame
import math
from random import random


class Canvas:
    def __init__(self):
        self.size = (256, 240)
        self._canvas = pygame.display.set_mode(self.size)
        self.running = True
        r1 = math.floor(random() * 255)
        r2 = math.floor(random() * 255)
        r3 = math.floor(random() * 255)

        pixels = [(r1, r2, r3)] * 256 * 240
        self.pixels = pixels

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

    def update_frame(self, buffer):
        self.pixels = buffer

    def _update_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pass
                # self.update(1, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                pass
                # self.update(0, event.pos)

    def update(self):
        pygame.display.flip()
        self._update_events()

    def clear(self):
        pass

    def draw(self):
        w, h = self.size
        i = 0
        while i < w:
            j = 0
            while j < h:
                pixel = self.pixels[i + (j * w)]
                self.draw_point(i, j, pixel)
                j += 1
            i += 1

