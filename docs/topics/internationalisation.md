# Internationalisation
REST framework ships with translatable error messages.  You can make these appear in your language enabling [Django's standard translation mechanisms][django-translation] and by translating the messages into your language.

## How to translate REST Framework errors

REST framework translations are managed online using [Transifex.com][transifex]. To get started, checkout the guide in the [CONTRIBUTING.md guide][contributing].

Sometimes you may want to use REST Framework in a language which has not been translated yet on Transifex. If that is the case then you should translate the error messages locally.

#### How to translate REST Framework error messages locally:

This guide assumes you are already familiar with how to translate a Django app.  If you're not, start by reading [Django's translation docs][django-translation].

1. Make a new folder where you want to store the translated errors. Add this 
path to your [`LOCALE_PATHS`][django-locale-paths] setting. 

  ---

  **Note:** For the rest of 
this document we will assume the path you created was 
`/home/www/project/conf/locale/`, and that you have updated your `settings.py` to include the setting:

  ```
  LOCALE_PATHS = (
      '/home/www/project/conf/locale/',
  )
  ```

  ---

2. Now create a subfolder for the language you want to translate. The folder should be named using [locale 
name][django-locale-name] notation.  E.g. `de`, `pt_BR`, `es_AR`, etc.

  ```
  mkdir /home/www/project/conf/locale/pt_BR/LC_MESSAGES
  ```

3. Now copy the base translations file from the REST framework source code 
into your translations folder

  ```
  cp /home/user/.virtualenvs/myproject/lib/python2.7/site-packages/rest_framework/locale/en_US/LC_MESSAGES/django.po
  /home/www/project/conf/locale/pt_BR/LC_MESSAGES
  ```
  
  This should create the file 
  `/home/www/project/conf/locale/pt_BR/LC_MESSAGES/django.po`
  
  ---

  **Note:** To find out where `rest_framework` is installed, run 

  ```
  python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"
  ```

  ---
  
  
4. Edit `/home/www/project/conf/locale/pt_BR/LC_MESSAGES/django.po` and 
translate all the error messages.

5. Run `manage.py compilemessages -l pt_BR` to make the translations 
available for Django to use. You should see a message

    ```
    processing file django.po in /home/www/project/conf/locale/pt_BR/LC_MESSAGES
    ```

6. Restart your server.



## How Django chooses which language to use
REST framework will use the same preferences to select which language to 
display as Django does.  You can find more info in the [Django docs on discovering language preferences][django-language-preference].  For reference, these are

1. First, it looks for the language prefix in the requested URL
2. Failing that, it looks for the `LANGUAGE_SESSION_KEY` key in the current user’s session.
3. Failing that, it looks for a cookie
4. Failing that, it looks at the `Accept-Language` HTTP header.
5. Failing that, it uses the global `LANGUAGE_CODE` setting.

---

**Note:** You'll need to include the `django.middleware.locale.LocaleMiddleware` to enable any of the per-request language preferences.

---


[django-translation]: https://docs.djangoproject.com/en/1.7/topics/i18n/translation
[django-language-preference]: https://docs.djangoproject.com/en/1.7/topics/i18n/translation/#how-django-discovers-language-preference
[django-locale-paths]: https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-LOCALE_PATHS
[django-locale-name]: https://docs.djangoproject.com/en/1.7/topics/i18n/#term-locale-name
[contributing]: ../../CONTRIBUTING.md
