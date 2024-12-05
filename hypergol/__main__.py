#!/usr/bin/env python3

import threading
import signal
import sys
import argparse
import matplotlib.pyplot as plt

from hypergol.automaton import HyperbolicAutomaton
from hypergol.shell import HypergolShell

def main():
    parser = argparse.ArgumentParser(
        description='Hyperbolic cellular automata simulator'
    )

    parser.add_argument('p', help='number of sides to a polygon', type=int)
    parser.add_argument('q', help='number of polygons around a vertex', type=int)
    parser.add_argument('-l', '--layers', required=False, default=5, type=int)

    args = parser.parse_args()

    if args.layers < 1:
        raise RuntimeError('number of layers must be greater than 0')

    plt.ion()
    plt.show()
    with HyperbolicAutomaton(args.p, args.q, args.layers) as automaton:
        shell = HypergolShell(automaton)

        def handler(signum, frame):
            print('^C')
            print(shell.prompt, end='', flush=True)

        signal.signal(signal.SIGINT, handler)

        io_thread = threading.Thread(target=shell.cmdloop)
        io_thread.start()

        while io_thread.is_alive():
            try:
                automaton.draw_barrier.wait()
                automaton.draw()
                automaton.draw_done.set()
            except threading.BrokenBarrierError:
                break

        io_thread.join()

if __name__ == '__main__':
    main()


