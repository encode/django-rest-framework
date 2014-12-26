# Internationalisation
REST framework ships with translatable error messages.  You can make these appear in your language enabling [Django's standard translation mechanisms][django-translation] and by translating the messages into your language.

## How to translate REST Framework errors


This guide assumes you are already familiar with how to translate a Django app.  If you're not, start by reading [Django's translation docs][django-translation].


#### To translate REST framework error messages:

1. Pick an app where you want the translations to be, for example `myapp`

2. Add a symlink from that app to the installed `rest_framework`
  ```
  ln -s /home/user/.virtualenvs/myproject/lib/python2.7/site-packages/rest_framework/ rest_framework
  ```
  
  ---

  **Note:** To find out where `rest_framework` is installed, run 

  ```
  python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"
  ```

  ---
  
  

3. Run Django's `makemessages` command in the normal way, but add the `--symlink` option.  For example, if you want to translate into Brazilian Portuguese you would run
  ```
  manage.py makemessages --symlink -l pt_BR
  ```
  
4. Translate the `django.po` file which is created as normal.  This will be in the folder `myapp/locale/pt_BR/LC_MESSAGES`.

5. Run `manage.py compilemessages` as normal

6. Restart your server



## How Django chooses which language to use
REST framework will use the same preferences to select which language to display as Django does.  You can find more info in the [django docs on discovering language preferences][django-language-preference].  For reference, these are

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
