from django.contrib import admin

from rest_framework.authtoken.models import Token


class TokenAdmin(admin.ModelAdmin):
    search_fields = ("key", "user__username")
    list_display = ('key', 'user', 'created')
    fields = ('user',)
    ordering = ('-created',)


admin.site.register(Token, TokenAdmin)
