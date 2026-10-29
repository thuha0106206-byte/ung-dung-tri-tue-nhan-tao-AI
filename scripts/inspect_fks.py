import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
for table_name in inspector.get_table_names():
    fks = inspector.get_foreign_keys(table_name)
    if fks:
        print(f"Table: {table_name}")
        for fk in fks:
            print(f"  FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

