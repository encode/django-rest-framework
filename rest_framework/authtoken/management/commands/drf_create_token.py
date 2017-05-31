from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Create DRF Token for a given user'

    def create_user_token(self, username):
        user = User.objects.get(username=username)
        token = Token.objects.get_or_create(user=user)
        return token[0]

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, nargs='+')

    def handle(self, *args, **options):
        username = options['username']

        try:
            token = self.create_user_token(username)
        except User.DoesNotExist:
            print('Cannot create the Token: user {0} does not exist'.format(
                username
            ))
        print('Generated token {0} for user {1}'.format(token.key, username))
