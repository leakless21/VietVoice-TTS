"""
Main entry point for running vietvoicetts as a module with python -m vietvoicetts
"""

# Import deterministic module to freeze all random seeds
import vietvoicetts.deterministic

from .cli import main

if __name__ == "__main__":
    main() 