from django.core.urlresolvers import resolve, get_script_prefix


def get_breadcrumbs(url):
    """Given a url returns a list of breadcrumbs, which are each a tuple of (name, url)."""

    from rest_framework.views import APIView

    def breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen):
        """Add tuples of (name, url) to the breadcrumbs list, progressively chomping off parts of the url."""

        try:
            (view, unused_args, unused_kwargs) = resolve(url)
        except Exception:
            pass
        else:
            # Check if this is a REST framework view, and if so add it to the breadcrumbs
            if isinstance(getattr(view, 'cls_instance', None), APIView):
                # Don't list the same view twice in a row.
                # Probably an optional trailing slash.
                if not seen or seen[-1] != view:
                    breadcrumbs_list.insert(0, (view.cls_instance.get_name(), prefix + url))
                    seen.append(view)

        if url == '':
            # All done
            return breadcrumbs_list

        elif url.endswith('/'):
            # Drop trailing slash off the end and continue to try to resolve more breadcrumbs
            return breadcrumbs_recursive(url.rstrip('/'), breadcrumbs_list, prefix, seen)

        # Drop trailing non-slash off the end and continue to try to resolve more breadcrumbs
        return breadcrumbs_recursive(url[:url.rfind('/') + 1], breadcrumbs_list, prefix, seen)

    prefix = get_script_prefix().rstrip('/')
    url = url[len(prefix):]
    return breadcrumbs_recursive(url, [], prefix, [])
