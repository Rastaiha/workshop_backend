from django.core.management import BaseCommand

from apps.accounts.models import User, UserWebsite
from apps.fsm.models import RegistrationReceipt


class Command(BaseCommand):

    def handle(self, *args, **options):
        for registration_receipt in RegistrationReceipt.objects.all():
            website = registration_receipt.answer_sheet_of.program.website
            user = registration_receipt.user
            UserWebsite.objects.create(
                user=user,
                website=website,
                password=user.password,
            )
