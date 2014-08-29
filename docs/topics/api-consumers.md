# API Consumers

Building an API is only half the battle.  Someone, somewhere, must consume it!
Here are a few notes on select consumers.


## Ember.js

The [Ember.js][] Javascript framework works well with Django
REST Framework, but requires an adapter.

If you are using [ember-cli][] (you should be!), installing the adapter is
simple:

    npm install --save-dev ember-django-adapter

For more information, visit the [adapter's wiki][ember-django-adapter-wiki].


[Ember.js]: http://emberjs.com/
[ember-cli]: http://www.ember-cli.com/
[ember-django-adapter-wiki]: https://github.com/toranb/ember-data-django-rest-adapter/wiki
