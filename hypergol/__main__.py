#!/usr/bin/env python3

import random
import threading
import signal
import sys
import argparse
import matplotlib.pyplot as plt

from hypergol.automaton import HyperbolicAutomaton
from hypergol.shell import HypergolShell

def main():
    parser = argparse.ArgumentParser(
        prog='hypergol',
        description='Hyperbolic cellular automata simulator'
    )

    parser.add_argument('p', help='number of sides to a polygon', type=int)
    parser.add_argument('q', help='number of polygons around a vertex', type=int)
    parser.add_argument('rule', help='format: b[0-9 ]+s[0-9 ]+', type=str)
    parser.add_argument('-l', '--layers', help='number of layers to initially generate. default: 5', type=int, required=False, default=5)
    parser.add_argument('-s', '--seed', type=int)
    parser.add_argument('-p', '--init-prob', help='probability of making a cell alive during random automaton initialization', type=float)
    parser.add_argument('-n', '--init-limit', help='limit number of cells to randomize at initialization', type=int)

    args = parser.parse_args()

    if args.layers < 1:
        raise RuntimeError('number of layers must be greater than 0')

    random.seed(args.seed)

    automaton = HyperbolicAutomaton(args.rule, args.p, args.q, args.layers)

    if args.init_prob and args.init_limit:
        automaton.randomize(p_alive=args.init_prob, limit=args.init_limit)
    elif args.init_prob:
        automaton.randomize(p_alive=args.init_prob)
    elif args.init_limit:
        raise RuntimeError('--init-limit must be used with --init-prob')

    with HypergolShell(automaton) as shell:
        plt.ion()
        plt.show()

        shell.draw()

        def handler(signum, frame):
            print('^C')
            print(shell.prompt, end='', flush=True)

        signal.signal(signal.SIGINT, handler)

        io_thread = threading.Thread(target=shell.cmdloop)
        io_thread.start()

        while not shell.dead.is_set():
            try:
                shell.draw_barrier.wait(1)
            except threading.BrokenBarrierError:
                shell.draw_barrier.reset()
                continue
            shell.draw()

        shell.draw_barrier.abort()

        io_thread.join()

if __name__ == '__main__':
    main()


