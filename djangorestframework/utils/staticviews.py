from django.contrib.auth.views import *
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import base64


# BLERGH
# Replicate django.contrib.auth.views.login simply so we don't have get users to update TEMPLATE_CONTEXT_PROCESSORS
# to add ADMIN_MEDIA_PREFIX to the RequestContext.  I don't like this but really really want users to not have to
# be making settings changes in order to accomodate django-rest-framework
@csrf_protect
@never_cache
def api_login(request, template_name='djangorestframework/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    """Displays the login form and handles the login action."""

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Light security check -- make sure redirect_to isn't garbage.
            if not redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Heavier security check -- redirects to http://example.com should
            # not be allowed, but things like /view/?param=http://example.com
            # should be allowed. This regex checks if there is a '//' *before* a
            # question mark.
            elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
                    redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)

    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    #current_site = get_current_site(request)

    return render_to_response(template_name, {
        'form': form,
        redirect_field_name: redirect_to,
        #'site': current_site,
        #'site_name': current_site.name,
        'ADMIN_MEDIA_PREFIX': settings.ADMIN_MEDIA_PREFIX,
    }, context_instance=RequestContext(request))


def api_logout(request, next_page=None, template_name='djangorestframework/login.html', redirect_field_name=REDIRECT_FIELD_NAME):
    return logout(request, next_page, template_name, redirect_field_name)
