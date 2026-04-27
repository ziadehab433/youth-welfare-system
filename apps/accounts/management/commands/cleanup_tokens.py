from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import RefreshToken


class Command(BaseCommand):
    help = 'Delete expired and revoked refresh tokens older than 30 days'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=30)
        deleted, _ = RefreshToken.objects.filter(
            is_revoked=True,
            created_at__lt=cutoff,
        ).delete()

        expired, _ = RefreshToken.objects.filter(
            expires_at__lt=timezone.now(),
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up {deleted} revoked + {expired} expired tokens.'
            )
        )




##python manage.py cleanup_tokens