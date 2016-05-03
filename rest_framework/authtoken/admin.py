from django.contrib import admin
from rest_framework.authtoken.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    raw_id_fields = ('user',)
    ordering = ('-created',)


admin.site.register(Token, TokenAdmin)
