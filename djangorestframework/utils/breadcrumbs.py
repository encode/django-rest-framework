from django.core.urlresolvers import resolve

def get_breadcrumbs(url):
    """Given a url returns a list of breadcrumbs, which are each a tuple of (name, url)."""

    from djangorestframework.views import View

    def breadcrumbs_recursive(url, breadcrumbs_list):
        """Add tuples of (name, url) to the breadcrumbs list, progressively chomping off parts of the url."""

        try:
            (view, unused_args, unused_kwargs) = resolve(url)
        except Exception:
            pass
        else:
            # Check if this is a REST framework view, and if so add it to the breadcrumbs
            if isinstance(getattr(view, 'cls_instance', None), View):
                breadcrumbs_list.insert(0, (view.cls_instance.get_name(), url))

        if url == '':
            # All done
            return breadcrumbs_list

        elif url.endswith('/'):
            # Drop trailing slash off the end and continue to try to resolve more breadcrumbs
            return breadcrumbs_recursive(url.rstrip('/'), breadcrumbs_list)

        # Drop trailing non-slash off the end and continue to try to resolve more breadcrumbs
        return breadcrumbs_recursive(url[:url.rfind('/') + 1], breadcrumbs_list)

    return breadcrumbs_recursive(url, [])

