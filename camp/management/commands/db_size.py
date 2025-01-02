from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Displays the size of the database.'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute("PRAGMA page_count;")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size;")
                page_size = cursor.fetchone()[0]
                size_mb = (page_count * page_size) / (1024 * 1024)
                self.stdout.write(f"Database size: {size_mb:.2f} MB")
            elif connection.vendor == 'postgresql':
                cursor.execute(
                    "SELECT pg_size_pretty(pg_database_size(current_database()));")
                size = cursor.fetchone()[0]
                self.stdout.write(f"Database size: {size}")
            elif connection.vendor == 'mysql':
                cursor.execute(
                    "SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb FROM information_schema.tables WHERE table_schema = DATABASE() GROUP BY table_schema;")
                size_mb = cursor.fetchone()[1]
                self.stdout.write(f"Database size: {size_mb:.2f} MB")
            else:
                self.stdout.write("Unsupported database backend.")
