<a class="github" href="negotiation.py"></a>

# Content negotiation

> HTTP has provisions for several mechanisms for "content negotiation" - the process of selecting the best representation for a given response when there are multiple representations available.
>
> &mdash; [RFC 2616][cite], Fielding et al.

[cite]: http://www.w3.org/Protocols/rfc2616/rfc2616-sec12.html

**TODO**: Describe content negotiation style used by REST framework.

## Custom content negotiation

It's unlikley that you'll want to provide a custom content negotiation scheme for REST framework, but you can do so if needed.  To implement a custom content negotiation scheme, override `BaseContentNegotiation`, and implement the `.select_parser(request, parsers)` and `.select_renderer(request, renderers, format_suffix)`