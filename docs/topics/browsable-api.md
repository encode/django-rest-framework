# The Browsable API

> It is a profoundly erroneous truism... that we should cultivate the habit of thinking of what we are doing.  The precise opposite is the case.  Civilization advances by extending the number of important operations which we can perform without thinking about them.
>
> &mdash; [Alfred North Whitehead][cite], An Introduction to Mathematics (1911)


API may stand for Application *Programming* Interface, but humans have to be able to read the APIs, too; someone has to do the programming.  Django REST Framework supports generating human-friendly HTML output for each resource when the `HTML` format is requested.  These pages allow for easy browsing of resources, as well as forms for submitting data to the resources using `POST`, `PUT`, and `DELETE`.

## URLs

If you include fully-qualified URLs in your resource output, they will be 'urlized' and made clickable for easy browsing by humans.  The `rest_framework` package includes a [`reverse`][drfreverse] helper for this purpose.

## Formats

By default, the API will return the format specified by the headers, which in the case of the browser is HTML.  The format can be specified using `?format=` in the request, so you can look at the raw JSON response in a browser by adding `?format=json` to the URL.  There are helpful extensions for viewing JSON in [Firefox][ffjsonview] and [Chrome][chromejsonview].

## Customizing

The browsable API is built with [Twitter's Bootstrap][bootstrap] (v 2.1.1), making it easy to customize the look-and-feel.

To customize the default style, create a template called `rest_framework/api.html` that extends from `rest_framework/base.html`.  For example:

**templates/rest_framework/api.html**

    {% extends "rest_framework/base.html" %}

    ...  # Override blocks with required customizations

### Overriding the default theme

To replace the default theme, add a `bootstrap_theme` block to your `api.html` and insert a `link` to the desired Bootstrap theme css file.  This will completely replace the included theme.

    {% block bootstrap_theme %}
        <link rel="stylesheet" href="/path/to/my/bootstrap.css" type="text/css">
    {% endblock %}

A suitable replacement theme can be generated using Bootstrap's [Customize Tool][bcustomize].  There are also pre-made themes available at [Bootswatch][bswatch].  To use any of the Bootswatch themes, simply download the theme's `bootstrap.min.css` file, add it to your project, and replace the default one as described above.

You can also change the navbar variant, which by default is `navbar-inverse`, using the `bootstrap_navbar_variant` block.  The empty `{% block bootstrap_navbar_variant %}{% endblock %}` will use the original Bootstrap navbar style.

Full example:

    {% extends "rest_framework/base.html" %}

    {% block bootstrap_theme %}
        <link rel="stylesheet" href="http://bootswatch.com/flatly/bootstrap.min.css" type="text/css">
    {% endblock %}

    {% block bootstrap_navbar_variant %}{% endblock %}

For more specific CSS tweaks than simply overriding the default bootstrap theme you can override the `style` block.

---

![Cerulean theme][cerulean]

*Screenshot of the bootswatch 'Cerulean' theme*

---

![Slate theme][slate]

*Screenshot of the bootswatch 'Slate' theme*

---

### Blocks

All of the blocks available in the browsable API base template that can be used in your `api.html`.

* `bodyclass`                  - Class attribute for the `<body>` tag, empty by default.
* `bootstrap_theme`            - CSS for the Bootstrap theme.
* `bootstrap_navbar_variant`   - CSS class for the navbar.
* `branding`                   - Branding section of the navbar, see [Bootstrap components][bcomponentsnav].
* `breadcrumbs`                - Links showing resource nesting, allowing the user to go back up the resources.  It's recommended to preserve these, but they can be overridden using the breadcrumbs block.
* `footer`                     - Any copyright notices or similar footer materials can go here (by default right-aligned).
* `script`                     - JavaScript files for the page.
* `style`                      - CSS stylesheets for the page.
* `title`                      - Title of the page.
* `userlinks`                  - This is a list of links on the right of the header, by default containing login/logout links.  To add links instead of replace, use `{{ block.super }}` to preserve the authentication links.

#### Components

All of the standard [Bootstrap components][bcomponents] are available.

#### Tooltips

The browsable API makes use of the Bootstrap tooltips component.  Any element with the `js-tooltip` class and a `title` attribute has that title content will display a tooltip on hover events.

### Login Template

To add branding and customize the look-and-feel of the login template, create a template called `login.html` and add it to your project, eg: `templates/rest_framework/login.html`.  The template should extend from `rest_framework/login_base.html`.

You can add your site name or branding by including the branding block:

    {% block branding %}
        <h3 style="margin: 0 0 20px;">My Site Name</h3>
    {% endblock %}

You can also customize the style by adding the `bootstrap_theme` or `style` block similar to `api.html`.

### Advanced Customization

#### Context

The context that's available to the template:

* `allowed_methods`     : A list of methods allowed by the resource
* `api_settings`        : The API settings
* `available_formats`   : A list of formats allowed by the resource
* `breadcrumblist`      : The list of links following the chain of nested resources
* `content`             : The content of the API response
* `description`         : The description of the resource, generated from its docstring
* `name`                : The name of the resource
* `post_form`           : A form instance for use by the POST form (if allowed)
* `put_form`            : A form instance for use by the PUT form (if allowed)
* `display_edit_forms`  : A boolean indicating whether or not POST, PUT and PATCH forms will be displayed
* `request`             : The request object
* `response`            : The response object
* `version`             : The version of Django REST Framework
* `view`                : The view handling the request
* `FORMAT_PARAM`        : The view can accept a format override
* `METHOD_PARAM`        : The view can accept a method override

You can override the `BrowsableAPIRenderer.get_context()` method to customise the context that gets passed to the template.

#### Not using base.html

For more advanced customization, such as not having a Bootstrap basis or tighter integration with the rest of your site, you can simply choose not to have `api.html` extend `base.html`.  Then the page content and capabilities are entirely up to you.

#### Autocompletion

When a `ChoiceField` has too many items, rendering the widget containing all the options can become very slow, and cause the browsable API rendering to perform poorly.  One solution is to replace the selector by an autocomplete widget, that only loads and renders a subset of the available options as needed.

There are [a variety of packages for autocomplete widgets][autocomplete-packages], such as [django-autocomplete-light][django-autocomplete-light].  To setup `django-autocomplete-light`, follow the [installation documentation][django-autocomplete-light-install], add the the following to the `api.html` template:

    {% block script %}
    {{ block.super }}
    {% include 'autocomplete_light/static.html' %}
    {% endblock %}

You can now add the `autocomplete_light.ChoiceWidget` widget to the serializer field.

    import autocomplete_light

    class BookSerializer(serializers.ModelSerializer):
        author = serializers.ChoiceField(
            widget=autocomplete_light.ChoiceWidget('AuthorAutocomplete')
        )

        class Meta:
            model = Book

---

![Autocomplete][autocomplete-image]

*Screenshot of the autocomplete-light widget*

---

[cite]: http://en.wikiquote.org/wiki/Alfred_North_Whitehead
[drfreverse]: ../api-guide/reverse.md
[ffjsonview]: https://addons.mozilla.org/en-US/firefox/addon/jsonview/
[chromejsonview]: https://chrome.google.com/webstore/detail/chklaanhfefbnpoihckbnefhakgolnmc
[bootstrap]: http://getbootstrap.com
[cerulean]: ../img/cerulean.png
[slate]: ../img/slate.png
[bcustomize]: http://twitter.github.com/bootstrap/customize.html#variables
[bswatch]: http://bootswatch.com/
[bcomponents]: http://twitter.github.com/bootstrap/components.html
[bcomponentsnav]: http://twitter.github.com/bootstrap/components.html#navbar
[autocomplete-packages]: https://www.djangopackages.com/grids/g/auto-complete/
[django-autocomplete-light]: https://github.com/yourlabs/django-autocomplete-light
[django-autocomplete-light-install]: http://django-autocomplete-light.readthedocs.org/en/latest/#install
[autocomplete-image]: ../img/autocomplete.png
