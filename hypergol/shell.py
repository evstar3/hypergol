#!/usr/bin/env python3

import cmd

class HypergolShell(cmd.Cmd):
    prompt = '(hypergol) '

    def __init__(self, automaton):
        super().__init__()
        self.automaton = automaton

    def do_set(self, arg):
        '''Set any number of cells by index:   set 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.set(cell)

        self.automaton.draw_barrier.wait()

    def do_kill(self, arg):
        '''Kill any number of cells by index:   kill 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.set(cell, alive=False)

        self.automaton.draw_barrier.wait()

    def do_toggle(self, arg):
        '''Toggle any number of cells by index:   toggle 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.toggle(cell)

        self.automaton.draw_barrier.wait()

    def do_rule(self, arg):
        '''Update the automaton rule:   rule b3/s23'''
        self.automaton.set_rule(arg)

    def do_step(self, arg):
        '''Update the cellular auomaton by running the rule on every cell once:   step'''
        self.automaton.step()
        self.automaton.draw_barrier.wait()

    def do_run(self, arg):
        '''Step the cellular automaton at regular intervals, as specified by rate:   run'''
        self.automaton.start()

    def do_stop(self, arg):
        '''Stop the cellular automaton from running:   stop'''
        self.automaton.stop()

    def do_rate(self, arg):
        '''Set the rate at which the cellular automaton steps while running:   rate 0.5'''
        rate = float(arg)
        self.automaton.set_rate(rate)

    def do_exit(self, arg):
        self.automaton.draw_barrier.abort()
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)
