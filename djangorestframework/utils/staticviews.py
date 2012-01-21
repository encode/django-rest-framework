from django.contrib.auth.views import *
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import base64


def deny_robots(request):
    return HttpResponse('User-agent: *\nDisallow: /', mimetype='text/plain')


def favicon(request):
    data = 'AAABAAEAEREAAAEAIADwBAAAFgAAACgAAAARAAAAIgAAAAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADLy8tLy8vL3svLy1QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAy8vLBsvLywkAAAAATkZFS1xUVPqhn57/y8vL0gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJmVlQ/GxcXiy8vL88vLy4FdVlXzTkZF/2RdXP/Ly8vty8vLtMvLy5DLy8vty8vLxgAAAAAAAAAAAAAAAAAAAABORkUJTkZF4lNMS/+Lh4f/cWtq/05GRf9ORkX/Vk9O/3JtbP+Ef3//Vk9O/2ljYv/Ly8v5y8vLCQAAAAAAAAAAAAAAAE5GRQlORkX2TkZF/05GRf9ORkX/TkZF/05GRf9ORkX/TkZF/05GRf9ORkX/UElI/8PDw5cAAAAAAAAAAAAAAAAAAAAAAAAAAE5GRZZORkX/TkZF/05GRf9ORkX/TkZF/05GRf9ORkX/TkZF/05GRf+Cfn3/y8vLvQAAAAAAAAAAAAAAAAAAAADLy8tIaWNi805GRf9ORkX/YVpZ/396eV7Ly8t7qaen9lZOTu5ORkX/TkZF/25oZ//Ly8v/y8vLycvLy0gAAAAATkZFSGNcXPpORkX/TkZF/05GRf+ysLDzTkZFe1NLSv6Oior/raur805GRf9ORkX/TkZF/2hiYf+npaX/y8vL5wAAAABORkXnTkZF/05GRf9ORkX/VU1M/8vLy/9PR0b1TkZF/1VNTP/Ly8uQT0dG+E5GRf9ORkX/TkZF/1hRUP3Ly8tmAAAAAE5GRWBORkXkTkZF/05GRf9ORkX/t7a2/355eOpORkX/TkZFkISAf1BORkX/TkZF/05GRf9XT075TkZFZgAAAAAAAAAAAAAAAAAAAABORkXDTkZF/05GRf9lX17/ubi4/8vLy/+2tbT/Yltb/05GRf9ORkX/a2Vk/8vLy5MAAAAAAAAAAAAAAAAAAAAAAAAAAFNLSqNORkX/TkZF/05GRf9ORkX/TkZF/05GRf9ORkX/TkZF/05GRf+Cfn3/y8vL+cvLyw8AAAAAAAAAAAAAAABORkUSTkZF+U5GRf9ORkX/TkZF/05GRf9ORkX/TkZF/05GRf9ORkX/TkZF/1BJSP/CwsLmy8vLDwAAAAAAAAAAAAAAAE5GRRJORkXtTkZF9FFJSJ1ORkXJTkZF/05GRf9ORkX/ZF5d9k5GRZ9ORkXtTkZF5HFsaxUAAAAAAAAAAAAAAAAAAAAAAAAAAE5GRQxORkUJAAAAAAAAAABORkXhTkZF/2JbWv7Ly8tgAAAAAAAAAABORkUGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAE5GRWBORkX2TkZFYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//+AAP9/gAD+P4AA4AOAAMADgADAA4AAwAOAAMMBgACCAIAAAAGAAIBDgADAA4AAwAOAAMADgADAB4AA/H+AAP7/gAA='
    return HttpResponse(base64.b64decode(data), mimetype='image/vnd.microsoft.icon')


# BLERGH
# Replicate django.contrib.auth.views.login simply so we don't have get users to update TEMPLATE_CONTEXT_PROCESSORS
# to add ADMIN_MEDIA_PREFIX to the RequestContext.  I don't like this but really really want users to not have to
# be making settings changes in order to accomodate django-rest-framework
@csrf_protect
@never_cache
def api_login(request, template_name='api_login.html',
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


def api_logout(request, next_page=None, template_name='api_login.html', redirect_field_name=REDIRECT_FIELD_NAME):
    return logout(request, next_page, template_name, redirect_field_name)
