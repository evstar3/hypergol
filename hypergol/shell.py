#!/usr/bin/env python3

import cmd

class HypergolShell(cmd.Cmd):
    prompt = '(hypergol) '

    def __init__(self, automaton):
        super().__init__()
        self.automaton = automaton

    def do_toggle(self, arg):
        print(arg)

    def do_step(self, arg):
        pass

    def do_run(self, arg):
        pass

    def do_stop(self, arg):
        pass

    def do_rate(self, arg):
        pass

    def do_exit(self, arg):
        return True
