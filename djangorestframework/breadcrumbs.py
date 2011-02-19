from django.core.urlresolvers import resolve
from djangorestframework.description import get_name

def get_breadcrumbs(url):
    """Given a url returns a list of breadcrumbs, which are each a tuple of (name, url)."""
    
    def breadcrumbs_recursive(url, breadcrumbs_list):
        """Add tuples of (name, url) to the breadcrumbs list, progressively chomping off parts of the url."""
        
        # This is just like compsci 101 all over again...
        try:
            (view, unused_args, unused_kwargs) = resolve(url)
        except:
            pass
        else:
            if callable(view):
                breadcrumbs_list.insert(0, (get_name(view), url))
        
        if url == '':
            # All done
            return breadcrumbs_list
    
        elif url.endswith('/'):
            # Drop trailing slash off the end and continue to try to resolve more breadcrumbs
            return breadcrumbs_recursive(url.rstrip('/'), breadcrumbs_list)
    
        # Drop trailing non-slash off the end and continue to try to resolve more breadcrumbs
        return breadcrumbs_recursive(url[:url.rfind('/') + 1], breadcrumbs_list)

    return breadcrumbs_recursive(url, [])

