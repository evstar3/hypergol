#!/usr/bin/env python3

from hypertiling import HyperbolicTiling
from hypertiling.graphics.plot import plot_tiling
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class HyperbolicAutomaton():
    ALIVE = mcolors.to_rgba('blue')
    DEAD = mcolors.to_rgba('white')

    def __init__(self, *args, **kwargs):
        self.tiling = HyperbolicTiling(*args, **kwargs)

        self.ax = plot_tiling(self.tiling)
        self.fig = self.ax.get_figure()

        self.collection = self.ax.collections[0]

        self.facecolors = [self.DEAD] * self.num_cells()

        for i in range(len(self.tiling)):
            z = self.tiling.get_center(i)
            l = self.tiling.get_layer(i)
            t = plt.text(z.real, z.imag, str(i), fontsize=15-4*l, ha="center", va="center")

        self.alive = set(range(self.num_cells()))
        self.dead  = set()

    def num_cells(self):
        return len(self.collection.get_paths())

    def toggle(self, index):
        if index in self.alive:
            self.alive.remove(index)
            self.dead.add(index)
            self.facecolors[index] = DEAD
        else:
            self.dead.remove(index)
            self.alive.add(index)
            self.facecolors[index] = ALIVE

    def update(self, index):
        self.collection.set_facecolor(self.facecolors)
        self.fig.draw()
        self.fig.flush_events()
