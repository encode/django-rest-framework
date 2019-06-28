from django.contrib import admin

from rest_framework.authtoken.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    fields = ('user',)
    ordering = ('-created',)
    autocomplete_fields = ('user',)


admin.site.register(Token, TokenAdmin)
