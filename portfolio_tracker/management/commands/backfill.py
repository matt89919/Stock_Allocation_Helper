# portfolio_tracker/management/commands/backfill_transactions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from portfolio_tracker.models import Holding, Transaction

class Command(BaseCommand):
    help = 'Backfills initial buy transactions from existing holdings.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to backfill transactions from holdings...")
        
        created_count = 0
        skipped_count = 0

        for holding in Holding.objects.all():
            # Check if a transaction for this exact instrument already exists
            # This is a simple check to prevent creating duplicates if run multiple times
            transaction_exists = Transaction.objects.filter(
                content_type=holding.content_type,
                object_id=holding.object_id,
                transaction_type='buy'
            ).exists()

            if transaction_exists:
                self.stdout.write(self.style.WARNING(f"Skipping {holding.instrument}, a transaction already exists."))
                skipped_count += 1
                continue

            # Create the initial "buy" transaction
            Transaction.objects.create(
                instrument=holding.instrument,
                transaction_type='buy',
                quantity=holding.quantity,
                price=holding.cost_basis,  # Assume cost_basis is the original purchase price
                date=timezone.now() # NOTE: The date will be today, as we don't know the original purchase date.
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created initial 'buy' transaction for {holding.instrument}"))

        self.stdout.write("--------------------")
        self.stdout.write(self.style.SUCCESS(f"Backfill complete. Created: {created_count}, Skipped: {skipped_count}."))