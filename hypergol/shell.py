#!/usr/bin/env python3

import cmd

class HypergolShell(cmd.Cmd):
    prompt = '(hypergol) '

    def __init__(self, automaton):
        super().__init__()
        self.automaton = automaton

    def draw(self):
        self.automaton.draw_done.clear()
        self.automaton.draw_barrier.wait()
        self.automaton.draw_done.wait()

    def do_number(self, arg):
        '''Set numbering on / off:   number off'''
        if arg == 'on':
            self.automaton.set_draw_indices(True)
        elif arg == 'off':
            self.automaton.set_draw_indices(False)
        else:
            print(f'unrecognized option: {arg}')

        self.draw()

    def do_set(self, arg):
        '''Set any number of cells by index:   set 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.set(cell)

        self.draw()

    def do_kill(self, arg):
        '''Kill any number of cells by index:   kill 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.set(cell, alive=False)

        self.draw()

    def do_clear(self, arg):
        '''Kill all cells:   clear'''
        for cell in self.automaton.tiling.polygons:
            self.automaton.set(cell, alive=False)

        self.draw()

    def do_toggle(self, arg):
        '''Toggle any number of cells by index:   toggle 2 3 5'''
        cells = map(int, arg.split())

        for cell in cells:
            self.automaton.toggle(cell)

        self.draw()

    def do_rule(self, arg):
        '''Show current rule:   rule\nUpdate the automaton rule:   rule b 2 s 2 3'''
        if arg:
            self.automaton.set_rule(arg)
        else:
            print(self.automaton.get_rule())

    def do_step(self, arg):
        '''Update the cellular auomaton by running the rule on every cell once:   step'''
        self.automaton.step()
        self.draw()

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

    def do_randomize(self, arg):
        '''Randomize all cells with equal probabilities:   randomize\nRandomize all cells with probability of being alive:   randomize 0.2'''
        self.automaton.randomize(p_alive=float(arg))
        self.draw()

    def do_move(self, arg):
        '''Center the display over the cell with given index:   move 7'''
        index = next(map(int, arg.split()))

        self.automaton.translate(index)
        self.draw()

    def do_exit(self, arg):
        print('exiting')
        self.do_stop(None)
        self.automaton.draw_barrier.abort()
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)
