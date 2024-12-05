#!/usr/bin/env python3

from hypergol.automaton import HyperbolicAutomaton
from hypergol.shell import HypergolShell
import matplotlib.pyplot as plt

def main():
    tiling = HyperbolicAutomaton(7, 3, 4)
    plt.ion()
    plt.show()

    HypergolShell(tiling).cmdloop()

if __name__ == '__main__':
    main()


