"""
Root wrapper to initialize database schema for Dhanvantari Clinic ERP
"""
import os
import sys
from pathlib import Path

INNER_DIR = Path(__file__).resolve().parent / "DhanvantariSuite-Phase1-Professional-OPD-v11"
sys.path.insert(0, str(INNER_DIR))
os.chdir(str(INNER_DIR))

from init_db import run_db_init
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema for Dhanvantari Clinic ERP")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables before recreating")
    parser.add_argument("--no-seed", dest="seed", action="store_false", help="Skip inserting default demo data")
    args = parser.parse_args()

    run_db_init(reset=args.reset, seed=args.seed)
