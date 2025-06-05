"""
Django command to wait for the db to be available
"""
from django.core.management.base import BaseCommand
import time

from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """ Django Command to wait for the database to be ready"""

    def handle(self, *args, **options):
        """Entrypoint for the command"""
        self.stdout.write('Waiting for the database...')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default']) # type: ignore
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))