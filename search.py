#!/usr/bin/env python3

import argparse
import random
import time
import json
import sys
import os
import itertools
import statistics

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
    def __init__(self, rule, p, q, layers, seed, max_steps=None, file=None, init_prob=None, init_limit=None):
        self.seed = seed
        random.seed(self.seed)

        self.init_prob = init_prob
        self.init_limit = init_limit
        self.automaton = HyperbolicAutomaton(rule, p, q, layers, init_prob=init_prob, init_limit=init_limit)

        if file is None:
            self.file = sys.stdout
        else:
            self.file = file

        if max_steps is None:
            self.max_steps = 4096
        else:
            self.max_steps = max_steps

        self.current_generation = 0

        self.states = []
        self.state_to_generation = {}

    def print_config(self):
        config_dict = {
            'rule': self.automaton.get_rule(),
            'p': self.automaton.tiling.p,
            'q': self.automaton.tiling.q,
            'layers': self.automaton.tiling.n,
            'max_steps': self.max_steps,
            'seed': self.seed,
            'init_prob': self.init_prob,
            'init_limit': self.init_limit
        }

        print(json.dumps(config_dict), file=self.file)

    def print_prologue(self, reason):
        print(f'TERMINATED: ' + reason, file=self.file) 

        for state_type in self.automaton.States:
            counts = [state.counts[state_type] for state in self.states]
            max_count = max(counts)
            min_count = min(counts)
            print(f'{state_type.name} MAX_COUNT={max_count}', file=self.file)
            print(f'{state_type.name} MIN_COUNT={min_count}', file=self.file)
            print(f'{state_type.name} RANGE_COUNT={max_count - min_count}', file=self.file)

            if len(counts) > 1:
                sd_count = statistics.stdev(counts)
                print(f'{state_type.name} STDEV_COUNT={sd_count}', file=self.file)

                diffs = [counts[i + 1] - counts[i] for i in range(self.current_generation - 1)]
                max_diff = max(diffs)
                min_diff = min(diffs)
                print(f'{state_type.name} MAX_DIFF={max_diff}', file=self.file)
                print(f'{state_type.name} MIN_DIFF={min_diff}', file=self.file)
                print(f'{state_type.name} RANGE_DIFF={max_diff - min_diff}', file=self.file)

                if len(diffs) > 1:
                    sd_diff = statistics.stdev(diffs)
                    print(f'{state_type.name} STDEV_DIFF={sd_diff}', file=self.file)

        print('### DONE ###', file=self.file)

    def state_generator(self):
        while True:
            automaton_state = AutomatonState(self.automaton.states, self.automaton.States)
            self.states.append(automaton_state)
            yield automaton_state

            if automaton_state.all_equal():
                self.print_prologue(f'ALL STATES EQUAL {automaton_state.state[0].name}')
                break

            if previous_gen := self.state_to_generation.get(automaton_state):
                if previous_gen == self.current_generation - 1:
                    self.print_prologue(f'STATIC. NO CHANGE FROM GENERATION {previous_gen}')
                else:
                    self.print_prologue(f'PERIODIC. REVISITED GENERATION {previous_gen}. PERIOD={self.current_generation - previous_gen}')
                break

            if self.current_generation >= self.max_steps:
                self.print_prologue('MAX STEPS REACHED')
                break

            self.state_to_generation[automaton_state] = self.current_generation

            self.automaton.step()
            self.current_generation += 1

    def run(self, steps=None):
        for state in itertools.islice(self.state_generator(), steps):
            print(f'{self.current_generation}: ' + state.summary(), file=self.file)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('p', help='number of sides to a polygon', type=int)
    parser.add_argument('q', help='number of polygons around a vertex', type=int)
    parser.add_argument('rule', help='format: b[0-9 ]+s[0-9 ]+', type=str)
    parser.add_argument('-l', '--layers', help='number of layers to initially generate. default: 5', type=int, required=False, default=5)
    parser.add_argument('-s', '--seed', type=int)
    parser.add_argument('-p', '--init-prob', help='probability of making a cell alive during random automaton initialization. default: 0.5',
                        type=float, default=0.5)
    parser.add_argument('-n', '--init-limit', help='limit number of cells to randomize at initialization', type=int)
    parser.add_argument('-m', '--max-steps', type=int)
    parser.add_argument('-o', '--outfile', type=Path)

    args = parser.parse_args()

    if args.layers < 1:
        raise RuntimeError('number of layers must be greater than 0')

    random.seed(args.seed)

    if args.outfile:
        fp = args.outfile.open('w')
    else:
        fp = sys.stdout

    search = Search(
        args.rule,
        args.p,
        args.q,
        args.layers,
        args.seed,
        max_steps=args.max_steps,
        file=fp,
        init_prob=args.init_prob,
        init_limit=args.init_limit
    )

    search.print_config()
    search.run()

    if args.outfile:
        fp.close()
        
if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
