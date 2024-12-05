#!/usr/bin/env python3

import re
import threading
import random
import types
import time
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from hypertiling import HyperbolicTiling
from hypertiling.graphics.plot import plot_tiling, convert_polygons_to_patches
from hypertiling.arraytransformation import morigin
from hypertiling.distance import disk_distance

def fixed_translate(self, z):
    """
    Translates the whole tiling so that the point z lays in the origin.

    Parameters
    ----------
    z: complex
        The point which will be translated to the origin.
    """

    for index, poly in self.polygons.items():
        morigin(self.p, z, poly.get_polygon())

class HyperbolicAutomaton():
    DEAD = mcolors.to_rgba('white')
    ALIVE = mcolors.to_rgba('blue')

    def __init__(self, *args):
        self.tiling = HyperbolicTiling(*args, kernel='SRG')
        self.tiling.translate = types.MethodType(fixed_translate, self.tiling)

        self.center = self.tiling.get_center(0)

        self.ax = plot_tiling(self.tiling, dpi=250)
        self.fig = self.ax.get_figure()
        self.texts = []

        self.color_lock = threading.Lock()
        self.facecolors = [self.DEAD] * len(self.tiling)

        self.draw_barrier = threading.Barrier(2)
        self.draw_done = threading.Event()
        self.draw()

        self.rule_lock = threading.Lock()
        self.set_rule('B3/S23')

        self.alive = threading.Event()

        self.run_thread = threading.Thread(target=self._run)

        self.running = threading.Event()

        self.rate_lock = threading.Lock()
        self._rate = 0.5

    def __enter__(self):
        self.alive.set()
        self.run_thread.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.alive.clear()
        self.run_thread.join()

    def set_rate(self, rate):
        with self.rate_lock:
            self._rate = rate

    def get_rule(self):
        with self.rule_lock:
            return 'b' + ''.join(str(b) for b in self._born) + '/' + 's' + ''.join(str(s) for s in self._survive)

    def set_rule(self, rule_str):
        with self.rule_lock:
            match = re.fullmatch(r'b([0-8]+)/s([0-8]+)', rule_str.lower())
            if not match:
                raise RuntimeError('invalid rule string')

            self._born = set(map(int, match[1]))
            self._survive = set(map(int, match[2]))

    def set(self, index, alive=True):
        with self.color_lock:
            self.facecolors[index] = self.ALIVE if alive else self.DEAD

    def toggle(self, index):
        with self.color_lock:
            if self.facecolors[index] == self.DEAD:
                self.facecolors[index] = self.ALIVE
            else:
                self.facecolors[index] = self.DEAD

    def translate(self, index):
        self.center = self.tiling.get_center(index)
        self.tiling.translate(self.center)

        def existing_cell_filter(z):
            cutoff = 0.05
            for poly in self.tiling.polygons.values():
                center = poly.get_polygon()[-1]
                dist = disk_distance(z, center)
                if dist < cutoff:
                    return False
            return True

        if index in self.tiling.exposed:
            self.tiling.add_layer((index,), filter=existing_cell_filter)

    def draw(self):
        self.ax.collections[0].remove()
        for txt in self.texts:
            txt.remove()
        self.texts.clear()

        pgons = convert_polygons_to_patches(self.tiling)
        self.ax.add_collection(pgons)
        for i in self.tiling.polygons:
            z = self.tiling.get_center(i)
            dist = math.dist((0,0), (z.real, z.imag))
            self.texts.append(plt.text(z.real, z.imag, str(i), fontsize=15-13*dist, ha="center", va="center"))
        with self.color_lock:
            self.ax.collections[-1].set_facecolor(self.facecolors)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def step(self):
        with self.rule_lock:
            new_colors = [self.DEAD] * len(self.tiling)

            for i in self.tiling.polygons:
                neighbors = self.tiling.get_nbrs(i)

                nbrs_alive = sum(int(self.facecolors[neighbor] == self.ALIVE) for neighbor in neighbors)

                if ((self.facecolors[i] == self.ALIVE and nbrs_alive in self._survive)
                        or (self.facecolors[i] == self.DEAD and nbrs_alive in self._born)):
                    new_colors[i] = self.ALIVE

            with self.color_lock:
                self.facecolors = new_colors

    def randomize(self):
        with self.color_lock:
            self.facecolors = [random.choice([self.ALIVE, self.DEAD]) for _ in range(len(self.tiling))]

    def start(self):
        self.running.set()

    def stop(self):
        self.running.clear()

    def _run(self):
        while self.alive.is_set():
            if self.running.is_set():
                self.step()
                self.draw_barrier.wait()
            with self.rate_lock:
                interval = self._rate
            time.sleep(interval)
