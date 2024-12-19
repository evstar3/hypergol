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
    parser.add_argument('rule', type=str)
    parser.add_argument('-l', '--layers', help='number of layers to initially generate. default: 6', type=int, required=False, default=6)
    parser.add_argument('-s', '--seed', type=int)
    parser.add_argument('-i', '--init', nargs='+')

    args = parser.parse_args()

    if args.layers < 1:
        raise RuntimeError('number of layers must be greater than 0')

    random.seed(args.seed)

    automaton = HyperbolicAutomaton(args.rule, args.p, args.q, args.layers)

    if args.init:
        if len(args.init) == 1:
            automaton.randomize(p_alive=float(args.init[0]))
        elif len(args.init) == 2:
            automaton.randomize(p_alive=float(args.init[0]), limit=int(args.init[1]))
        else:
            raise RuntimeError('too many arguments to --init')

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


