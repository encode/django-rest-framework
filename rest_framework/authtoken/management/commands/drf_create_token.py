from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


UserModel = get_user_model()


class Command(BaseCommand):
    help = 'Create DRF Token for a given user'

    def create_user_token(self, username):
        user = UserModel._default_manager.get_by_natural_key(username)
        token = Token.objects.get_or_create(user=user)
        return token[0]

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, nargs='+')

    def handle(self, *args, **options):
        username = options['username']

        try:
            token = self.create_user_token(username)
        except UserModel.DoesNotExist:
            print('Cannot create the Token: user {0} does not exist'.format(
                username
            ))
        print('Generated token {0} for user {1}'.format(token.key, username))
