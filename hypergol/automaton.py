#!/usr/bin/env python3

import re
import threading
import random
import types
import time
import math
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from enum import Enum

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
    class States(Enum):
        DEAD = mcolors.to_rgba('white')
        ALIVE = mcolors.to_rgba('blue')

    def __init__(self, rule_str, *args):
        self.tiling = HyperbolicTiling(*args, kernel='SRG')
        self.tiling.translate = types.MethodType(fixed_translate, self.tiling)

        self.center = self.tiling.get_center(0)

        self.ax = plot_tiling(self.tiling, dpi=250)
        self.fig = self.ax.get_figure()
        self.texts = []

        self.color_lock = threading.Lock()
        self.states = [self.States.DEAD] * len(self.tiling)

        self.draw_indices_lock = threading.Lock()
        self.draw_indices = True

        self.draw_barrier = threading.Barrier(2)
        self.draw_done = threading.Event()
        self.draw()

        self.rule_lock = threading.Lock()
        self.set_rule(rule_str)

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
            return ' '.join((
                'b',
                ' '.join(str(i) for i in self._born),
                's',
                ' '.join(str(i) for i in self._survive)
            ))

    def set_rule(self, rule_str):
        with self.rule_lock:
            matches = re.fullmatch(r'b([0-9 ]*)s([0-9 ]*)', rule_str)

            if not matches:
                raise RuntimeError('invalid rule str')

            born_str = matches[1]
            survive_str = matches[2]

            self._born = set(map(int, born_str.split()))
            self._survive = set(map(int, survive_str.split()))

    def set(self, index, alive=True):
        with self.color_lock:
            self.states[index] = self.States.ALIVE if alive else self.States.DEAD

    def toggle(self, index):
        with self.color_lock:
            if self.states[index] == self.States.DEAD:
                self.states[index] = self.States.ALIVE
            else:
                self.states[index] = self.States.DEAD

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

        if len(self.tiling.get_nbrs(index)) < len(self.tiling.get_nbrs(0)):
            print('adding layer...')
            self.tiling.add_layer(filter=existing_cell_filter)
            self.states += [self.States.DEAD] * (len(self.tiling) - len(self.states))

    def set_draw_indices(self, val):
        with self.draw_indices_lock:
            self.draw_indices = val

    def draw(self):
        self.ax.collections[0].remove()
        for txt in self.texts:
            txt.remove()
        self.texts.clear()

        pgons = convert_polygons_to_patches(self.tiling)
        self.ax.add_collection(pgons)

        with self.draw_indices_lock:
            if self.draw_indices:
                for i in self.tiling.polygons:
                    z = self.tiling.get_center(i)
                    dist = math.dist((0,0), (z.real, z.imag))
                    self.texts.append(plt.text(z.real, z.imag, str(i), fontsize=15-13*dist, ha="center", va="center"))

        with self.color_lock:
            self.ax.collections[-1].set_facecolor([state.value for state in self.states])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def step(self):
        with self.rule_lock:
            new_states = [self.States.DEAD] * len(self.tiling)

            for i in self.tiling.polygons:
                neighbors = self.tiling.get_nbrs(i)

                nbrs_alive = sum(int(self.states[neighbor] == self.States.ALIVE) for neighbor in neighbors)

                if ((self.states[i] == self.States.ALIVE and nbrs_alive in self._survive)
                        or (self.states[i] == self.States.DEAD and nbrs_alive in self._born)):
                    new_states[i] = self.States.ALIVE

            with self.color_lock:
                self.states = new_states

    def randomize(self, p_alive=0.5):
        with self.color_lock:
            self.states = random.choices(list(self.States), weights=(1 - p_alive, p_alive), k=len(self.tiling))

    def start(self):
        self.running.set()

    def stop(self):
        self.running.clear()

    def _run(self):
        while self.alive.is_set():
            if self.running.wait(1):
                self.step()
                self.draw_barrier.wait()
                with self.rate_lock:
                    interval = self._rate
                time.sleep(interval)
