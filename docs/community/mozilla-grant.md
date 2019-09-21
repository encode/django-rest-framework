# Mozilla Grant

We have recently been [awarded a Mozilla grant](https://blog.mozilla.org/blog/2016/04/13/mozilla-open-source-support-moss-update-q1-2016/), in order to fund the next major releases of REST framework. This work will focus on seamless client-side integration by introducing supporting client libraries that are able to dynamically interact with REST framework APIs. The framework will provide for either hypermedia or schema endpoints, which will expose the available interface for the client libraries to interact with.

Additionally, we will be building on the realtime support that Django Channels provides, supporting and documenting how to build realtime APIs with REST framework. Again, this will include supporting work in the associated client libraries, making it easier to build richly interactive applications.

The [Core API](https://www.coreapi.org/) project will provide the foundations for our client library support, and will allow us to support interaction using a wide range of schemas and hypermedia formats. It's worth noting that these client libraries won't be tightly coupled to solely REST framework APIs either, and will be able to interact with *any* API that exposes a supported schema or hypermedia format.

Specifically, the work includes:

## Client libraries

This work will include built-in schema and hypermedia support, allowing dynamic client libraries to interact with the API. I'll also be releasing both Python and Javascript client libraries, plus a command-line client, a new tutorial section, and further documentation.

* Client library support in REST framework.
  * Schema & hypermedia support for REST framework APIs.
  * A test client, allowing you to write tests that emulate a client library interacting with your API.
  * New tutorial sections on using client libraries to interact with REST framework APIs.
* Python client library.
* JavaScript client library.
* Command line client.

## Realtime APIs

The next goal is to build on the realtime support offered by Django Channels, adding support & documentation for building realtime API endpoints.

* Support for API subscription endpoints, using REST framework and Django Channels.
* New tutorial section on building realtime API endpoints with REST framework.
* Realtime support in the Python & Javascript client libraries.

## Accountability

In order to ensure that I can be fully focused on trying to secure a sustainable
& well-funded open source business I will be leaving my current role at [DabApps](https://www.dabapps.com/)
at the end of May 2016.

I have formed a UK limited company, [Encode](https://www.encode.io/), which will
act as the business entity behind REST framework. I will be issuing monthly reports
from Encode on progress both towards the Mozilla grant, and for development time
funded via the [REST framework paid plans](funding.md).

<!-- Begin MailChimp Signup Form -->
<link href="//cdn-images.mailchimp.com/embedcode/classic-10_7.css" rel="stylesheet" type="text/css">
<style type="text/css">
    #mc_embed_signup{background:#fff; clear:left; font:14px Helvetica,Arial,sans-serif; }
    /* Add your own MailChimp form style overrides in your site stylesheet or in this style block.
       We recommend moving this block and the preceding CSS link to the HEAD of your HTML file. */
</style>
<div id="mc_embed_signup">
<form action="//encode.us13.list-manage.com/subscribe/post?u=b6b66bb5e4c7cb484a85c8dd7&amp;id=e382ef68ef" method="post" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" class="validate" target="_blank" novalidate>
    <div id="mc_embed_signup_scroll">
    <h2>Stay up to date, with our monthly progress reports...</h2>
<div class="mc-field-group">
    <label for="mce-EMAIL">Email Address </label>
    <input type="email" value="" name="EMAIL" class="required email" id="mce-EMAIL">
</div>
    <div id="mce-responses" class="clear">
        <div class="response" id="mce-error-response" style="display:none"></div>
        <div class="response" id="mce-success-response" style="display:none"></div>
    </div>    <!-- real people should not fill this in and expect good things - do not remove this or risk form bot signups-->
    <div style="position: absolute; left: -5000px;" aria-hidden="true"><input type="text" name="b_b6b66bb5e4c7cb484a85c8dd7_e382ef68ef" tabindex="-1" value=""></div>
    <div class="clear"><input type="submit" value="Subscribe" name="subscribe" id="mc-embedded-subscribe" class="button"></div>
    </div>
</form>
</div>
<script type='text/javascript' src='//s3.amazonaws.com/downloads.mailchimp.com/js/mc-validate.js'></script><script type='text/javascript'>(function($) {window.fnames = new Array(); window.ftypes = new Array();fnames[0]='EMAIL';ftypes[0]='email';fnames[1]='FNAME';ftypes[1]='text';fnames[2]='LNAME';ftypes[2]='text';}(jQuery));var $mcj = jQuery.noConflict(true);</script>
<!--End mc_embed_signup-->
