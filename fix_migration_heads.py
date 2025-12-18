#!/usr/bin/env python3
"""
Fix multiple heads in Alembic migrations by checking current state
"""
import os
import sys

# Set up path
sys.path.insert(0, os.path.dirname(__file__))

from app.get_args import args
from flask import Flask
from flask_migrate import Migrate, stamp
from app.database import Base, engine, migrations_directory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(args.config_dir, "db", "bazarr.db")}'
migrate = Migrate(app, Base, directory=migrations_directory)

print("Checking migration heads...")
with app.app_context():
    from flask_migrate import current, heads
    
    # Get current revision
    try:
        current_rev = current()
        print(f"Current revision: {current_rev}")
    except Exception as e:
        print(f"Error getting current revision: {e}")
    
    # Get all heads
    try:
        all_heads = heads()
        print(f"All heads: {all_heads}")
    except Exception as e:
        print(f"Error getting heads: {e}")
    
    # Stamp to the latest
    print("\nStamping database to latest revision (2a86a941ecac)...")
    try:
        stamp(revision='2a86a941ecac')
        print("Successfully stamped to 2a86a941ecac")
    except Exception as e:
        print(f"Error stamping: {e}")

