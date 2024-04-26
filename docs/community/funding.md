<script>
// Imperfect, but easier to fit in with the existing docs build.
// Hyperlinks should point directly to the "fund." subdomain, but this'll
// handle the nav bar links without requiring any docs build changes for the moment.
if (window.location.hostname == "www.django-rest-framework.org") {
    window.location.replace("https://fund.django-rest-framework.org/topics/funding/");
}
</script>

<style>
.promo li a {
    float: left;
    width: 130px;
    height: 20px;
    text-align: center;
    margin: 10px 30px;
    padding: 150px 0 0 0;
    background-position: 0 50%;
    background-size: 130px auto;
    background-repeat: no-repeat;
    font-size: 120%;
    color: black;
}
.promo li {
    list-style: none;
}
.chart {
    background-color: #e3e3e3;
    background: -webkit-linear-gradient(top, #fff 0, #e3e3e3 100%);
    border: 1px solid #E6E6E6;
    border-radius: 5px;
    box-shadow: 0px 0px 2px 0px rgba(181, 181, 181, 0.3);
    padding: 40px 0px 5px;
    position: relative;
    text-align: center;
    width: 97%;
    min-height: 255px;
    position: relative;
    top: 37px;
    margin-bottom: 20px
}
.quantity {
    text-align: center
}
.dollar {
    font-size: 19px;
    position: relative;
    top: -18px;
}
.price {
    font-size: 49px;
}
.period {
    font-size: 17px;
    position: relative;
    top: -8px;
    margin-left: 4px;
}
.plan-name {
    text-align: center;
    font-size: 20px;
    font-weight: 400;
    color: #777;
    border-bottom: 1px solid #d5d5d5;
    padding-bottom: 15px;
    width: 90%;
    margin: 0 auto;
    margin-top: 8px;
}
.specs {
    margin-top: 20px;
    min-height: 130px;
}
.specs.freelancer {
    min-height: 0px;
}
.spec {
    font-size: 15px;
    color: #474747;
    text-align: center;
    font-weight: 300;
    margin-bottom: 13px;
}
.variable {
    color: #1FBEE7;
    font-weight: 400;
}
form.signup {
    margin-top: 35px
}
.clear-promo {
    padding-top: 30px
}
#main-content h1:first-of-type {
    margin: 0 0 50px;
    font-size: 60px;
    font-weight: 200;
    text-align: center
}
#main-content {
    padding-top: 10px; line-height: 23px
}
#main-content li {
    line-height: 23px
}
</style>

# Funding

If you use REST framework commercially we strongly encourage you to invest in its continued development by signing up for a paid plan.

**We believe that collaboratively funded software can offer outstanding returns on investment, by encouraging our users to collectively share the cost of development.**

Signing up for a paid plan will:

* Directly contribute to faster releases, more features, and higher quality software.
* Allow more time to be invested in documentation, issue triage, and community support.
* Safeguard the future development of REST framework.

REST framework continues to be open-source and permissively licensed, but we firmly believe it is in the commercial best-interest for users of the project to invest in its ongoing development.

---

## What funding has enabled so far

* The [3.4](https://www.django-rest-framework.org/community/3.4-announcement/) and [3.5](https://www.django-rest-framework.org/community/3.5-announcement/) releases, including schema generation for both Swagger and RAML, a Python client library, a Command Line client, and addressing of a large number of outstanding issues.
* The [3.6](https://www.django-rest-framework.org/community/3.6-announcement/) release, including JavaScript client library, and API documentation, complete with auto-generated code samples.
* The [3.7 release](https://www.django-rest-framework.org/community/3.7-announcement/), made possible due to our collaborative funding model, focuses on improvements to schema generation and the interactive API documentation.
* The recent [3.8 release](https://www.django-rest-framework.org/community/3.8-announcement/).
* Tom Christie, the creator of Django REST framework, working on the project full-time.
* Around 80-90 issues and pull requests closed per month since Tom Christie started working on the project full-time.
* A community & operations manager position part-time for 4 months, helping mature the business and grow sponsorship.
* Contracting development time for the work on the JavaScript client library and API documentation tooling.

---

## What future funding will enable

* Realtime API support, using WebSockets. This will consist of documentation and support for using REST framework together with Django Channels, plus integrating WebSocket support into the client libraries.
* Better authentication defaults, possibly bringing JWT & CORS support into the core package.
* Securing the community & operations manager position long-term.
* Opening up and securing a part-time position to focus on ticket triage and resolution.
* Paying for development time on building API client libraries in a range of programming languages. These would be integrated directly into the upcoming API documentation.

Sign up for a paid plan today, and help ensure that REST framework becomes a sustainable, full-time funded project.

---

## What our sponsors and users say

> As a developer, Django REST framework feels like an obvious and natural extension to all the great things that make up Django and it's community. Getting started is easy while providing simple abstractions which makes it flexible and customizable. Contributing and supporting Django REST framework helps ensure its future and one way or another it also helps Django, and the Python ecosystem.
>
> &mdash; José Padilla, Django REST framework contributor

&nbsp;

> The number one feature of the Python programming language is its community. Such a community is only possible because of the Open Source nature of the language and all the culture that comes from it. Building great Open Source projects require great minds. Given that, we at Vinta are not only proud to sponsor the team behind DRF but we also recognize the ROI that comes from it.
>
> &mdash; Filipe Ximenes, Vinta Software

&nbsp;

> It's really awesome that this project continues to endure. The code base is top notch and the maintainers are committed to the highest level of quality.
DRF is one of the core reasons why Django is top choice among web frameworks today. In my opinion, it sets the standard for rest frameworks for the development community at large.
>
> &mdash; Andrew Conti, Django REST framework user

---

## Individual plan

This subscription is recommended for individuals with an interest in seeing REST framework continue to&nbsp;improve.

If you are using REST framework as a full-time employee, consider recommending that your company takes out a [corporate&nbsp;plan](#corporate-plans).

<div class="pricing">
                <div class="span4">
                    <div class="chart first">
                        <div class="quantity">
                            <span class="dollar">{{ symbol }}</span>
                            <span class="price">{{ rates.personal1 }}</span>
                            <span class="period">/month{% if vat %} +VAT{% endif %}</span>
                        </div>
                        <div class="plan-name">Individual</div>
                        <div class="specs freelancer">
                            <div class="spec">
                                Support ongoing development
                            </div>
                            <div class="spec">
                                Credited on the site
                            </div>
                        </div>
                        <form class="signup" action="/signup/{{ currency }}-{{ rates.personal1 }}/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="{{ stripe_amounts.personal1 }}"
    data-name="Django REST framework"
    data-description="Individual"
    data-currency="{{ currency }}"
    data-allow-remember-me=false
    data-billing-address=true
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
                    </div>
                </div>
            </div>
<div style="clear: both; padding-top: 50px"></div>

*Billing is monthly and you can cancel at any time.*

---

## Corporate plans

These subscriptions are recommended for companies and organizations using REST framework either publicly or privately.

In exchange for funding you'll also receive advertising space on our site, allowing you to **promote your company or product to many tens of thousands of developers worldwide**.

Our professional and premium plans also include **priority support**. At any time your engineers can escalate an issue or discussion group thread, and we'll ensure it gets a guaranteed response within the next working day.

<div class="pricing">
                <div class="span4">
                    <div class="chart first">
                        <div class="quantity">
                            <span class="dollar">{{ symbol }}</span>
                            <span class="price">{{ rates.corporate1 }}</span>
                            <span class="period">/month{% if vat %} +VAT{% endif %}</span>
                        </div>
                        <div class="plan-name">Basic</div>
                        <div class="specs startup">
                            <div class="spec">
                                Support ongoing development
                            </div>
                            <div class="spec">
                                <span class="variable">Funding page</span> ad placement
                            </div>
                        </div>
                        <form class="signup" action="/signup/{{ currency }}-{{ rates.corporate1 }}/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="{{ stripe_amounts.corporate1 }}"
    data-name="Django REST framework"
    data-description="Basic"
    data-currency="{{ currency }}"
    data-allow-remember-me=false
    data-billing-address=true
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
                    </div>
                </div>
                <div class="span4">
                    <div class="chart">
                        <div class="quantity">
                            <span class="dollar">{{ symbol }}</span>
                            <span class="price">{{ rates.corporate2 }}</span>
                            <span class="period">/month{% if vat %} +VAT{% endif %}</span>
                        </div>
                        <div class="plan-name">Professional</div>
                        <div class="specs">
                            <div class="spec">
                                Support ongoing development
                            </div>
                            <div class="spec">
                                <span class="variable">Sidebar</span> ad placement
                            </div>
                            <div class="spec">
                                <span class="variable">Priority support</span> for your engineers
                            </div>
                        </div>
                        <form class="signup" action="/signup/{{ currency }}-{{ rates.corporate2 }}/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="{{ stripe_amounts.corporate2 }}"
    data-name="Django REST framework"
    data-description="Professional"
    data-currency="{{ currency }}"
    data-allow-remember-me=false
    data-billing-address=true
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
                    </div>
                </div>
                <div class="span4">
                    <div class="chart last">
                        <div class="quantity">
                            <span class="dollar">{{ symbol }}</span>
                            <span class="price">{{ rates.corporate3 }}</span>
                            <span class="period">/month{% if vat %} +VAT{% endif %}</span>
                        </div>
                        <div class="plan-name">Premium</div>
                        <div class="specs">
                        <div class="spec">
                            Support ongoing development
                        </div>
                            <div class="spec">
                                <span class="variable">Homepage</span> ad placement
                            </div>
                            <div class="spec">
                                <span class="variable">Sidebar</span> ad placement
                            </div>
                            <div class="spec">
                                <span class="variable">Priority support</span> for your engineers
                            </div>
                        </div>
                        <form class="signup" action="/signup/{{ currency }}-{{ rates.corporate3 }}/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="{{ stripe_amounts.corporate3 }}"
    data-name="Django REST framework"
    data-description="Premium"
    data-currency="{{ currency }}"
    data-allow-remember-me=false
    data-billing-address=true
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
                    </div>
                </div>
            </div>

<div style="clear: both; padding-top: 50px"></div>

*Billing is monthly and you can cancel at any time.*

Once you've signed up, we will contact you via email and arrange your ad placements on the site.

For further enquires please contact <a href=mailto:funding@django-rest-framework.org>funding@django-rest-framework.org</a>.

---

## Accountability

In an effort to keep the project as transparent as possible, we are releasing [monthly progress reports](https://www.encode.io/reports/march-2018/) and regularly include financial reports and cost breakdowns.

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

---

## Frequently asked questions

**Q: Can you issue monthly invoices?**
A: Yes, we are happy to issue monthly invoices. Please just <a href=mailto:funding@django-rest-framework.org>email us</a> and let us know who to issue the invoice to (name and address) and which email address to send it to each month.

**Q: Does sponsorship include VAT?**
A: Sponsorship is VAT exempt.

**Q: Do I have to sign up for a certain time period?**
A: No, we appreciate your support for any time period that is convenient for you. Also, you can cancel your sponsorship anytime.

**Q: Can I pay yearly? Can I pay upfront fox X amount of months at a time?**
A: We are currently only set up to accept monthly payments. However, if you'd like to support Django REST framework and you can only do yearly/upfront payments, we are happy to work with you and figure out a convenient solution.

**Q: Are you only looking for corporate sponsors?**
A: No, we value individual sponsors just as much as corporate sponsors and appreciate any kind of support.

---

## Our sponsors

<div id="fundingInclude"></div>

<script src="https://fund.django-rest-framework.org/funding_include.js"></script>
