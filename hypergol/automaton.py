#!/usr/bin/env python3

import re
import threading
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from hypertiling import HyperbolicTiling
from hypertiling.graphics.plot import plot_tiling, convert_polygons_to_patches
from time import sleep
from matplotlib.collections import PatchCollection

class HyperbolicAutomaton():
    DEAD = mcolors.to_rgba('white')
    ALIVE = mcolors.to_rgba('blue')

    def __init__(self, *args, **kwargs):
        self.tiling = HyperbolicTiling(*args, **kwargs)
        self.center = self.tiling.get_center(0)

        self.ax = plot_tiling(self.tiling, dpi=250)
        self.fig = self.ax.get_figure()
        self.texts = []

        self.color_lock = threading.Lock()
        self.facecolors = [self.DEAD] * self.num_cells()

        self.draw_barrier = threading.Barrier(2)
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

    def num_cells(self):
        return len(self.ax.collections[-1].get_paths())

    def set_rate(self, rate):
        with self.rate_lock:
            self._rate = rate

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

    def draw(self):
        self.ax.collections[0].remove()
        for txt in self.texts:
            txt.remove()
        self.texts.clear()

        pgons = convert_polygons_to_patches(self.tiling)
        self.ax.add_collection(pgons)
        for i in range(self.num_cells()):
            z = self.tiling.get_center(i)
            l = self.tiling.get_layer(i)
            self.texts.append(plt.text(z.real, z.imag, str(i), fontsize=6, ha="center", va="center"))
        with self.color_lock:
            self.ax.collections[-1].set_facecolor(self.facecolors)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def step(self):
        with self.rule_lock:
            new_colors = [self.DEAD] * self.num_cells()

            for i in range(self.num_cells()):
                neighbors = self.tiling.get_nbrs(i)

                nbrs_alive = sum(int(self.facecolors[neighbor] == self.ALIVE) for neighbor in neighbors)

                if ((self.facecolors[i] == self.ALIVE and nbrs_alive in self._survive)
                        or (self.facecolors[i] == self.DEAD and nbrs_alive in self._born)):
                    new_colors[i] = self.ALIVE

            with self.color_lock:
                self.facecolors = new_colors

    def randomize(self):
        with self.color_lock:
            self.facecolors = [random.choice([self.ALIVE, self.DEAD]) for _ in range(self.num_cells())]

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
            sleep(interval)
