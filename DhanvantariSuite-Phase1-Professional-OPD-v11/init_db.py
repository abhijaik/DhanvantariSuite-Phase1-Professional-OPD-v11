"""
Database Schema Initialization and Seed Script for Dhanvantari Clinic ERP
Usage:
    python init_db.py
    python init_db.py --seed
    python init_db.py --reset  (Caution: drops and recreates tables)
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from sqlalchemy import inspect
from src.adapters.db.connection import engine, init_db, DATABASE_URL
from src.adapters.db.orm_models import Base
from src.main import seed_data

def run_db_init(reset: bool = False, seed: bool = True):
    print("=" * 60)
    print("DHANVANTARI CLINIC ERP - DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"Target Database URL: {DATABASE_URL}")
    
    try:
        with engine.connect() as conn:
            print("Successfully connected to database engine.")
    except Exception as e:
        print(f"\n[ERROR] Could not connect to database:")
        print(f"  {e}")
        print("\nPlease verify:")
        print("  1. PostgreSQL service is running.")
        print("  2. The target database exists (e.g. 'CREATE DATABASE clinic_erp;').")
        print("  3. Credentials in DATABASE_URL environment variable are correct.")
        print("     Example: set DATABASE_URL=postgresql://postgres:password@localhost:5432/clinic_erp")
        sys.exit(1)

    if reset:
        print("\n[RESET] Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped.")

    print("\nCreating tables, constraints, and indexes...")
    init_db()

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Successfully verified {len(tables)} tables:")
    for t in sorted(tables):
        print(f"  - {t}")

    if seed:
        print("\nSeeding initial data (roles, demo users, medicines)...")
        seed_data()
        print("Data seeding completed.")
        print("\nDemo Accounts Available:")
        print("  - Admin:        admin_user        / adminpass123")
        print("  - Receptionist: receptionist_user / receppass123")
        print("  - Doctor:       doctor_user       / docpass123")

    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema for Dhanvantari Clinic ERP")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables before recreating")
    parser.add_argument("--no-seed", dest="seed", action="store_false", help="Skip inserting default demo data")
    args = parser.parse_args()

    run_db_init(reset=args.reset, seed=args.seed)
