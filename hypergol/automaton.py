#!/usr/bin/env python3

import re
import random
import types
import enum

from hypertiling import HyperbolicTiling
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
    class States(enum.Enum):
        ALIVE = enum.auto()
        DEAD = enum.auto()

    def __init__(self, rule_str, *args):
        self.tiling = HyperbolicTiling(*args, kernel='SRG')
        self.tiling.translate = types.MethodType(fixed_translate, self.tiling)

        self.center = self.tiling.get_center(0)

        self.states = [self.States.DEAD] * len(self.tiling)

        self.set_rule(rule_str)

    def get_rule(self):
        return ' '.join((
            'b',
            ' '.join(str(i) for i in self._born),
            's',
            ' '.join(str(i) for i in self._survive)
        ))

    def set_rule(self, rule_str):
        rule_str = rule_str.replace('_', ' ')
        matches = re.fullmatch(r'b([0-9 ]*)s([0-9 ]*)', rule_str)

        if not matches:
            raise RuntimeError('invalid rule str')

        born_str = matches[1]
        survive_str = matches[2]

        self._born = set(map(int, born_str.split()))
        self._survive = set(map(int, survive_str.split()))

    def set(self, index, alive=True):
        self.states[index] = self.States.ALIVE if alive else self.States.DEAD

    def toggle(self, index):
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

    def step(self):
        new_states = [self.States.DEAD] * len(self.tiling)

        for i in self.tiling.polygons:
            neighbors = self.tiling.get_nbrs(i)

            nbrs_alive = sum(int(self.states[neighbor] == self.States.ALIVE) for neighbor in neighbors)

            if ((self.states[i] == self.States.ALIVE and nbrs_alive in self._survive)
                    or (self.states[i] == self.States.DEAD and nbrs_alive in self._born)):
                new_states[i] = self.States.ALIVE

        self.states = new_states

    def randomize(self, p_alive):
        self.states = random.choices(list(self.States), weights=(1 - p_alive, p_alive), k=len(self.tiling))
