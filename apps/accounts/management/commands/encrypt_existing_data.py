"""
Management command to encrypt existing student data
Usage: python manage.py encrypt_existing_data
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import Students
from apps.accounts.encryption import encryption_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Encrypt existing unencrypted student data (nid, uid, phone_number, address)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be encrypted without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        students = Students.objects.all()
        encrypted_count = 0
        already_encrypted = 0
        
        self.stdout.write(
            self.style.WARNING(
                f'Processing {students.count()} students...'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('[DRY RUN] No changes will be made')
            )
        
        for student in students:
            updated = False
            
            # Check and encrypt NID
            if student.nid and not encryption_service.is_encrypted(student.nid):
                if not dry_run:
                    student.nid = encryption_service.encrypt(student.nid)
                updated = True
                encrypted_count += 1
            elif student.nid and encryption_service.is_encrypted(student.nid):
                already_encrypted += 1
            
            # Check and encrypt UID
            if student.uid and not encryption_service.is_encrypted(student.uid):
                if not dry_run:
                    student.uid = encryption_service.encrypt(student.uid)
                updated = True
                encrypted_count += 1
            elif student.uid and encryption_service.is_encrypted(student.uid):
                already_encrypted += 1
            
            # Check and encrypt phone_number
            if student.phone_number and not encryption_service.is_encrypted(student.phone_number):
                if not dry_run:
                    student.phone_number = encryption_service.encrypt(student.phone_number)
                updated = True
                encrypted_count += 1
            elif student.phone_number and encryption_service.is_encrypted(student.phone_number):
                already_encrypted += 1
            
            # Check and encrypt address
            if student.address and not encryption_service.is_encrypted(student.address):
                if not dry_run:
                    student.address = encryption_service.encrypt(student.address)
                updated = True
                encrypted_count += 1
            elif student.address and encryption_service.is_encrypted(student.address):
                already_encrypted += 1
            
            if updated and not dry_run:
                student.save()
        
        # Output results
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully encrypted {encrypted_count} field(s)'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Already encrypted: {already_encrypted} field(s)'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n[DRY RUN COMPLETE] Run without --dry-run to apply changes'
                )
            )