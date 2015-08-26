<script>
// Imperfect, but easier to fit in with the existing docs build.
// Hyperlinks should point directly to the "fund." subdomain, but this'll
// handle the nav bar links without requiring any docs build changes for the moment.
if (window.location.hostname == "www.django-rest-framework.org") {
    window.location.replace("https://fund.django-rest-framework.org/topics/funding/");
}
</script>

<style>
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
    margin-bottom: 20px}
.quantity {
    text-align: center}
.dollar {
    font-size: 19px;
    position: relative;
    top: -18px;
}
.price {
    font-size: 49px;}
.period {
    font-size: 17px;
    position: relative;
    top: -8px;
    margin-left: 4px;}
.plan-name {
	 text-align: center;
    font-size: 20px;
    font-weight: 400;
    color: #777;
    border-bottom: 1px solid #d5d5d5;
    padding-bottom: 15px;
    width: 90%;
    margin: 0 auto;
    margin-top: 8px;}
.specs {
    margin-top: 20px;}
.specs.startup {
    margin-bottom: 93px}
.spec {
    font-size: 15px;
    color: #474747;
    text-align: center;
    font-weight: 300;
    margin-bottom: 13px;}
.variable {
    color: #1FBEE7;
    font-weight: 400;}
form.signup {
    margin-top: 35px}
.clear-promo {
    padding-top: 30px}
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

**We believe that collaboratively funded software can offer outstanding returns on investment, by allowing users and clients to collectively share the cost of development.**

Signing up for a paid plan will:

* Directly contribute to faster releases, more features and higher quality software.
* Allow more time to be invested in documentation, issue triage and community support.
* Safeguard the future development of REST framework.

REST framework will always be open source and permissively licensed, but we firmly believe it is in the commercial best-interest for users of the project to fund its ongoing development.

---

## Making the business case

Our successful Kickstarter campaign demonstrates the cost-reward ratio of shared development funding.

With *typical corporate fundings of just £100-£1000 per organization* we successfully delivered:

* The comprehensive 3.0 serializer redesign.
* Substantial improvements to the Browsable API.
* The admin interface.
* A new pagination API including offset/limit and cursor pagination implementations, plus on-page controls.
* A versioning API, including URL-based and header-based versioning schemes.
* Support for customizable exception handling.
* Support for Django's PostgreSQL HStoreField, ArrayField and JSONField.
* Templated HTML form support, including HTML forms with nested list and objects.
* Internationalization support for API responses, currently with 27 languages.
* The metadata APIs for handling `OPTIONS` requests and schema endpoints.
* Numerous minor improvements and better quality throughout the codebase.
* Ongoing triage and community support, closing over 1600 tickets.

This incredible level of return on investment is *only possible through collaboratively funded models*, which is why we believe that supporting our paid plans is in everyone's best interest.

---

## Individual plan

This subscription is recommended for freelancers and other individuals with an interest in seeing REST framework continue to&nbsp;improve.

If you are using REST framework as an full-time employee, consider recommending that your company takes out a [corporate&nbsp;plan](#corporate-plans).

<div class="pricing">
				<div class="span4">
					<div class="chart first">
						<div class="quantity">
							<span class="dollar">$</span>
							<span class="price">15</span>
							<span class="period">/month</span>
						</div>
						<div class="plan-name">Individual</div>
						<div class="specs">
							<div class="spec">
								Support ongoing development
							</div>
							<div class="spec">
								Credited on the site
							</div>
						</div>
						<form class="signup" action="/signup/individual/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="1500"
    data-name="Django REST framework"
    data-description="Individual"
    data-currency="usd"
    data-allow-remember-me=false
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
							<span class="dollar">$</span>
							<span class="price">50</span>
							<span class="period">/month</span>
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
						<form class="signup" action="/signup/startup/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="5000"
    data-name="Django REST framework"
    data-description="Basic"
    data-currency="usd"
    data-allow-remember-me=false
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
					</div>
				</div>
				<div class="span4">
					<div class="chart">
						<div class="quantity">
							<span class="dollar">$</span>
							<span class="price">250</span>
							<span class="period">/month</span>
						</div>
						<div class="plan-name">Professional</div>
						<div class="specs">
							<div class="spec">
								Add a <span class="variable">half day per&nbsp;month</span> development time to the project
							</div>
							<div class="spec">
								<span class="variable">Homepage</span> ad placement
							</div>
							<div class="spec">
								<span class="variable">Priority support</span> for your engineers
							</div>
						</div>
						<form class="signup" action="/signup/professional/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="25000"
    data-name="Django REST framework"
    data-description="Professional"
    data-currency="usd"
    data-allow-remember-me=false
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
					</div>
				</div>
				<div class="span4">
					<div class="chart last">
						<div class="quantity">
							<span class="dollar">$</span>
							<span class="price">500</span>
							<span class="period">/month</span>
						</div>
						<div class="plan-name">Premium</div>
						<div class="specs">
							<div class="spec">
								Add <span class="variable">one full day per&nbsp;month</span> development time to the project
							</div>
							<div class="spec">
								<span class="variable">Full site</span> ad placement
							</div>
							<div class="spec">
								<span class="variable">Priority support</span> for your engineers
							</div>
						</div>
						<form class="signup" action="/signup/premium/" method="POST">
  <script
    src="https://checkout.stripe.com/checkout.js" class="stripe-button"
    data-key="{{ stripe_public }}"
    data-amount="50000"
    data-name="Django REST framework"
    data-description="Premium"
    data-currency="usd"
    data-allow-remember-me=false
    data-label='Sign up'
    data-panel-label='Sign up - {% verbatim %}{{amount}}{% endverbatim %}/mo'>
  </script>
</form>
					</div>
				</div>
			</div>

<div style="clear: both; padding-top: 50px"></div>

*Billing is monthly and you can cancel at any time.*

Once you've signed up we'll contact you via email and arrange your ad placements on the site.

For further enquires please contact <a href=mailto:tom@tomchristie.com>tom@tomchristie.com</a>.

---

## Roadmap

Although we're incredibly proud of REST framework in its current state we believe there is still huge scope for improvement. What we're aiming for here is a *highly polished, rock solid product*. This needs to backed up with impeccable documentation and a great third party ecosystem.

The roadmap below is a broad indication of just some of the ongoing and future work we believe is important to REST framework.

* Increasing our "bus factor" through documented organizational process & safeguards.
* More time towards testing and hardening releases, with only gradual, well-documented deprecations.
* A formal policy on security backports for non-current releases.
* Continuing triage & community support.
* Improved project documentation, including versioned & internationalized docs.
* Improved third party package visibility.
* Further work on the the admin API, making it suitable as a customizable end-user facing application.
* Support for alternative backends such as SQLAlchemy.
* HTTP Caching API & support for conditional database lookups.
* Benchmarking and performance improvements.
* In depth documentation on advanced usage and best practices.
* Documentation & support for integration with realtime systems.
* Hypermedia support and client libraries.
* Support for JSON schema as endpoints or `OPTIONS` responses.
* API metric tools.
* Debug & logging tools.
* Third party GraphQL support.

By taking out a paid plan you'll be directly contributing towards making these features happen.
