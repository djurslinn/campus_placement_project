import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_placement.settings')
django.setup()

with connection.cursor() as cursor:
    print("--- TABLES ---")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
    
    print("\n--- MIGRATIONS ---")
    cursor.execute("SELECT app, name from django_migrations")
    migrations = cursor.fetchall()
    for mig in migrations:
        print(f"{mig[0]}: {mig[1]}")
