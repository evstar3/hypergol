#!/usr/bin/env python3

import threading
import signal
import sys
import matplotlib.pyplot as plt

from hypergol.automaton import HyperbolicAutomaton
from hypergol.shell import HypergolShell

def main():
    plt.ion()
    plt.show()
    with HyperbolicAutomaton(8, 3, 4) as automaton:
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


