"""
Management command to clean up old system logs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventory.models import LoginLog, ActionLog


class Command(BaseCommand):
    help = 'Clean up old system logs to free up database space'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete logs older than this many days (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without making changes'
        )
        parser.add_argument(
            '--keep-login-logs',
            action='store_true',
            help='Keep login logs (only delete action logs)'
        )
        parser.add_argument(
            '--keep-action-logs',
            action='store_true',
            help='Keep action logs (only delete login logs)'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        keep_login_logs = options['keep_login_logs']
        keep_action_logs = options['keep_action_logs']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        cutoff_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f'Cleaning up logs older than {days} days (before {cutoff_date.date()})')

        deleted_login_logs = 0
        deleted_action_logs = 0

        # Clean up login logs
        if not keep_login_logs:
            old_login_logs = LoginLog.objects.filter(login_time__lt=cutoff_date)
            login_count = old_login_logs.count()
            
            if login_count > 0:
                self.stdout.write(f'Found {login_count} old login logs to delete')
                
                if not dry_run:
                    deleted_login_logs = old_login_logs.delete()[0]
                    self.stdout.write(f'Deleted {deleted_login_logs} login logs')
                else:
                    self.stdout.write(f'Would delete {login_count} login logs')
            else:
                self.stdout.write('No old login logs found')

        # Clean up action logs
        if not keep_action_logs:
            old_action_logs = ActionLog.objects.filter(timestamp__lt=cutoff_date)
            action_count = old_action_logs.count()
            
            if action_count > 0:
                self.stdout.write(f'Found {action_count} old action logs to delete')
                
                if not dry_run:
                    deleted_action_logs = old_action_logs.delete()[0]
                    self.stdout.write(f'Deleted {deleted_action_logs} action logs')
                else:
                    self.stdout.write(f'Would delete {action_count} action logs')
            else:
                self.stdout.write('No old action logs found')

        # Summary
        total_deleted = deleted_login_logs + deleted_action_logs
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run. No changes were made.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {total_deleted} log entries')
            )
