#!/usr/bin/env python3

import cmd
import threading
import math
import time

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from hypertiling.graphics.plot import plot_tiling, convert_polygons_to_patches

class HypergolShell(cmd.Cmd):
    prompt = '(hypergol) '

    def __init__(self, automaton):
        super().__init__()
        self.automaton = automaton
        self.automaton_lock = threading.Lock()

        self.draw_indices = True

        self.ax = plot_tiling(self.automaton.tiling, dpi=250)
        self.fig = self.ax.get_figure()
        self.texts = []

        self.dead = threading.Event()
        self.dead.set()
        self.running = threading.Event()

        colors = [mcolors.to_rgba('blue'), mcolors.to_rgba('white')]
        self.color_map = {state: color for state, color in zip(self.automaton.States, colors)}

        self.draw_barrier = threading.Barrier(2)

        self.rate = 1

    def __enter__(self):
        self.run_thread = threading.Thread(target=self._run)
        self.dead.clear()
        self.run_thread.start()

        return self

    def __exit__(self, *args):
        self.run_thread.join()
        self.draw_barrier.abort()

    def draw(self):
        self.ax.collections[0].remove()
        for txt in self.texts:
            txt.remove()
        self.texts.clear()

        with self.automaton_lock:
            pgons = convert_polygons_to_patches(self.automaton.tiling)
            self.ax.add_collection(pgons)

            if self.draw_indices:
                for i in self.automaton.tiling.polygons:
                    z = self.automaton.tiling.get_center(i)
                    dist = math.dist((0,0), (z.real, z.imag))
                    self.texts.append(plt.text(z.real, z.imag, str(i), fontsize=15-13*dist, ha="center", va="center"))

            self.ax.collections[-1].set_facecolor([self.color_map[state] for state in self.automaton.states])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def do_number(self, arg):
        '''Set numbering on / off:   number off'''
        if arg == 'on':
            self.draw_indices = True
        elif arg == 'off':
            self.draw_indices = False
        else:
            print(f'unrecognized option: {arg}')
        self.draw_barrier.wait()

    def do_set(self, arg):
        '''Set any number of cells by index:   set 2 3 5'''
        cells = map(int, arg.split())
        with self.automaton_lock:
            for cell in cells:
                self.automaton.set(cell)
        self.draw_barrier.wait()

    def do_kill(self, arg):
        '''Kill any number of cells by index:   kill 2 3 5'''
        cells = map(int, arg.split())
        with self.automaton_lock:
            for cell in cells:
                self.automaton.set(cell, alive=False)
        self.draw_barrier.wait()

    def do_clear(self, arg):
        '''Kill all cells:   clear'''
        with self.automaton_lock:
            for cell in self.automaton.tiling.polygons:
                self.automaton.set(cell, alive=False)
        self.draw_barrier.wait()

    def do_toggle(self, arg):
        '''Toggle any number of cells by index:   toggle 2 3 5'''
        cells = map(int, arg.split())
        with self.automaton_lock:
            for cell in cells:
                self.automaton.toggle(cell)
        self.draw_barrier.wait()

    def do_rule(self, arg):
        '''Show current rule:   rule\nUpdate the automaton rule:   rule b 2 s 2 3'''
        if arg:
            with self.automaton_lock:
                self.automaton.set_rule(arg)
        else:
            print(self.automaton.get_rule())

    def do_step(self, arg):
        '''Update the cellular auomaton by running the rule on every cell once:   step\nStep multiple times:   step 5'''
        if arg:
            try:
                steps = int(arg.split()[0])
            except ValueError:
                print(f'invalid number of steps: {arg}')
                return
        else:
            steps = 1

        for _ in range(steps):
            with self.automaton_lock:
                self.automaton.step()
        self.draw_barrier.wait()

    def do_run(self, arg):
        '''Step the cellular automaton at regular intervals, as specified by rate:   run'''
        self.running.set()

    def do_stop(self, arg):
        '''Stop the cellular automaton from running:   stop'''
        self.running.clear()

    def do_rate(self, arg):
        '''Print the current rate:   rate\nSet the rate at which the cellular automaton steps while running:   rate 0.5'''
        if arg:
            rate_str = arg.split()[0]
            try:
                rate = float(rate_str)
                assert rate >= 0
                self.rate = rate
            except (ValueError, AssertionError):
                print(f'invalid rate: {rate_str}')
                return
        else:
            print(self.rate)

    def do_randomize(self, arg):
        '''Randomize all cells with equal state probability:   randomize
Randomize all cells and set probability of being alive:   randomize 0.2
Randomize cells 0 (inclusive) through 20 (exclusive) with probability of being alive:   randomize 0.5 20'''

        args = arg.split()

        if args:
            try:
                p_alive = float(args.pop(0))
                if not 0 <= p_alive <= 1:
                    raise ValueError
            except ValueError:
                print('invalid probability')
                return
        else:
            p_alive = 0.5

        if args:
            try:
                limit = int(args.pop(0))
                if not limit > 0:
                    raise ValueError
            except ValueError:
                print('invalid limit')
                return
        else:
            limit = None

        with self.automaton_lock:
            self.automaton.randomize(p_alive, limit=limit)
        self.draw_barrier.wait()

    def do_move(self, arg):
        '''Center the display over the cell with given index:   move 7'''
        index = next(map(int, arg.split()))
        with self.automaton_lock:
            self.automaton.translate(index)
        self.draw_barrier.wait()

    def do_exit(self, arg):
        self.dead.set()
        self.running.clear()
        print('exiting')
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)

    def _run(self):
        while not self.dead.is_set():
            if not self.running.wait(1):
                continue

            if self.draw_barrier.broken:
                continue

            start = time.time()
            with self.automaton_lock:
                self.automaton.step()

            try:
                self.draw_barrier.wait()
            except threading.BrokenBarrierError:
                continue

            end = time.time()

            remaining = self.rate - (end - start)
            if remaining > 0:
                self.dead.wait(remaining)
