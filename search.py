#!/usr/bin/env python3

import argparse
import random
import time
import json
import sys
import os
import itertools

from collections import defaultdict
from pathlib import Path

from hypergol.automaton import HyperbolicAutomaton

class AutomatonState():
    def __init__(self, state, states_enum):
        self.state = state
        self.state_hash = hash(tuple(self.state))
        self.size = len(state)

        self.states_enum = states_enum

        self.counts = {s: self.state.count(s) for s in self.states_enum}

    def all_equal(self):
        return all(s == self.state[0] for s in self.state)

    def summary(self):
        return ' '.join(f'{count}({count / self.size:0.3f}) {state.name}' for state, count in self.counts.items())

    def __eq__(self, other):
        if type(other) == AutomatonState:
            return self.state_hash == other.state_hash and self.state == other.state
        return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return self.state_hash

class Search():
    def __init__(self, automaton, max_steps, seed=None, file: Path=None):
        self.automaton = automaton
        self.max_steps = max_steps
        self.file = file

        if seed is None:
            self.seed = time.time_ns()
        else:
            self.seed = seed

        random.seed(self.seed)

        self.current_generation = 0

        self.states = []
        self.state_to_generation = {}

        self.automaton.randomize()

    def __enter__(self):
        if self.file:
            self.fp = self.file.open('w')
        else:
            self.fp = sys.stdout

        return self

    def __exit__(self, *args):
        if self.file:
            self.fp.close()

    def print_config(self):
        config_dict = {
            'rule': self.automaton.get_rule(),
            'p': self.automaton.tiling.p,
            'q': self.automaton.tiling.q,
            'layers': self.automaton.tiling.n,
            'max_steps': self.max_steps,
            'seed': self.seed
        }

        print(json.dumps(config_dict), file=self.fp)

    def print_prologue(self, reason):
        print(f'{self.current_generation}: ' + reason, file=self.fp) 

    def state_generator(self):
        while True:
            automaton_state = AutomatonState(self.automaton.states, self.automaton.States)

            if automaton_state.all_equal():
                self.print_prologue(f'ALL STATES EQUAL {automaton_state.state[0].name}')
                break

            if previous_gen := self.state_to_generation.get(automaton_state):
                if previous_gen == self.current_generation - 1:
                    self.print_prologue(f'STATIC. NO CHANGE FROM GENERATION {previous_gen}')
                else:
                    self.print_prologue(f'PERIODIC. REVISITED GENERATION {previous_gen}. PERIOD={self.current_generation - previous_gen}')
                break

            self.states.append(automaton_state)
            self.state_to_generation[automaton_state] = self.current_generation

            if self.current_generation >= self.max_steps:
                self.print_prologue('MAX STEPS REACHED')
                break

            yield automaton_state

            self.automaton.step()
            self.current_generation += 1

    def run(self, steps=None):
        for state in itertools.islice(self.state_generator(), steps):
            print(f'{self.current_generation}: ' + state.summary(), file=self.fp)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('rule', type=str)
    parser.add_argument('p', help='number of sides to a polygon', type=int)
    parser.add_argument('q', help='number of polygons around a vertex', type=int)
    parser.add_argument('-l', '--layers', type=int, default=5)
    parser.add_argument('-n', '--max-steps', type=int, default=4096)
    parser.add_argument('-s', '--seed', type=int)
    parser.add_argument('-o', '--outfile', type=Path)

    args = parser.parse_args()

    automaton = HyperbolicAutomaton(args.rule, args.p, args.q, args.layers)
    with Search(automaton, args.max_steps, seed=args.seed, file=args.outfile) as search:
        search.print_config()
        search.run()
        
if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)