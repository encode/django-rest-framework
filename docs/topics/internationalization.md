# Internationalization

> Supporting internationalization is not optional. It must be a core feature.
>
> &mdash; [Jannis Leidel, speaking at Django Under the Hood, 2015][cite].

REST framework ships with translatable error messages. You can make these appear in your language enabling [Django's standard translation mechanisms][django-translation].

Doing so will allow you to:

* Select a language other than English as the default, using the standard `LANGUAGE_CODE` Django setting.
* Allow clients to choose a language themselves, using the `LocaleMiddleware` included with Django. A typical usage for API clients would be to include an `Accept-Language` request header.

## Enabling internationalized APIs

You can change the default language by using the standard Django `LANGUAGE_CODE` setting:

    LANGUAGE_CODE = "es-es"

You can turn on per-request language requests by adding `LocalMiddleware` to your `MIDDLEWARE` setting:

    MIDDLEWARE = [
        ...
        'django.middleware.locale.LocaleMiddleware'
    ]

When per-request internationalization is enabled, client requests will respect the `Accept-Language` header where possible. For example, let's make a request for an unsupported media type:

**Request**

    GET /api/users HTTP/1.1
    Accept: application/xml
    Accept-Language: es-es
    Host: example.org

**Response**

    HTTP/1.0 406 NOT ACCEPTABLE

    {"detail": "No se ha podido satisfacer la solicitud de cabecera de Accept."}

REST framework includes these built-in translations both for standard exception cases, and for serializer validation errors.

Note that the translations only apply to the error strings themselves. The format of error messages, and the keys of field names will remain the same. An example `400 Bad Request` response body might look like this:

    {"detail": {"username": ["Esse campo deve ser único."]}}

If you want to use different string for parts of the response such as `detail` and `non_field_errors` then you can modify this behavior by using a [custom exception handler][custom-exception-handler].

#### Specifying the set of supported languages.

By default all available languages will be supported.

If you only wish to support a subset of the available languages, use Django's standard `LANGUAGES` setting:

    LANGUAGES = [
        ('de', _('German')),
        ('en', _('English')),
    ]

## Adding new translations

REST framework translations are managed online using [Transifex][transifex-project]. You can use the Transifex service to add new translation languages. The maintenance team will then ensure that these translation strings are included in the REST framework package.

Sometimes you may need to add translation strings to your project locally. You may need to do this if:

* You want to use REST Framework in a language which has not been translated yet on Transifex.
* Your project includes custom error messages, which are not part of REST framework's default translation strings.

#### Translating a new language locally

This guide assumes you are already familiar with how to translate a Django app.  If you're not, start by reading [Django's translation docs][django-translation].

If you're translating a new language you'll need to translate the existing REST framework error messages:

1. Make a new folder where you want to store the internationalization resources. Add this path to your [`LOCALE_PATHS`][django-locale-paths] setting.

2. Now create a subfolder for the language you want to translate. The folder should be named using [locale name][django-locale-name] notation. For example: `de`, `pt_BR`, `es_AR`.

3. Now copy the [base translations file][django-po-source] from the REST framework source code into your translations folder.

4. Edit the `django.po` file you've just copied, translating all the error messages.

5. Run `manage.py compilemessages -l pt_BR` to make the translations
available for Django to use. You should see a message like `processing file django.po in <...>/locale/pt_BR/LC_MESSAGES`.

6. Restart your development server to see the changes take effect.

If you're only translating custom error messages that exist inside your project codebase you don't need to copy the REST framework source `django.po` file into a `LOCALE_PATHS` folder, and can instead simply run Django's standard `makemessages` process.

## How the language is determined

If you want to allow per-request language preferences you'll need to include `django.middleware.locale.LocaleMiddleware` in your `MIDDLEWARE` setting.

You can find more information on how the language preference is determined in the [Django documentation][django-language-preference]. For reference, the method is:

1. First, it looks for the language prefix in the requested URL.
2. Failing that, it looks for the `LANGUAGE_SESSION_KEY` key in the current user’s session.
3. Failing that, it looks for a cookie.
4. Failing that, it looks at the `Accept-Language` HTTP header.
5. Failing that, it uses the global `LANGUAGE_CODE` setting.

For API clients the most appropriate of these will typically be to use the `Accept-Language` header; Sessions and cookies will not be available unless using session authentication, and generally better practice to prefer an `Accept-Language` header for API clients rather than using language URL prefixes.

[cite]: https://youtu.be/Wa0VfS2q94Y
[django-translation]: https://docs.djangoproject.com/en/stable/topics/i18n/translation
[custom-exception-handler]: ../api-guide/exceptions.md#custom-exception-handling
[transifex-project]: https://explore.transifex.com/django-rest-framework-1/django-rest-framework/
[django-po-source]: https://raw.githubusercontent.com/encode/django-rest-framework/master/rest_framework/locale/en_US/LC_MESSAGES/django.po
[django-language-preference]: https://docs.djangoproject.com/en/stable/topics/i18n/translation/#how-django-discovers-language-preference
[django-locale-paths]: https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-LOCALE_PATHS
[django-locale-name]: https://docs.djangoproject.com/en/stable/topics/i18n/#term-locale-name
