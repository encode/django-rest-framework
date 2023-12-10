# FastAPI REST framework


Django has always lived up to it's tagline, The web framework for perfectionists with deadlines. 
DRF has been facilitating this even more with it's amazing serializers, viewsets, filters, validators, routers and so on...

---
### Here are a few challenges with django we're aiming to address

- One issue with django is that since it's designed as an all-encompassing web framework, designed before the advent of microservices, it comes with a lot of bloat that's not needed
for api services. 
- Alternate frameworks like fastapi exist, which are laser focused on these exact priorities but lack the structure and maturity that a DRF based project has from the get-go.
- Another issue with django is it's tight coupling with app registry and makes things like dynamic table creation non trivial to say the least...  
- The settings being lazyloaded makes restarts necessary for any change which makes dynamic configuration only possible outside the core settings.
- ...
---

This project aims to retain all functionalities of DRF minus the bloat of django... 



# Requirements

* Python 3.9+
* FastAPI 0.104.1+



# Installation

Clone this repository

```bash
python setup.py install
```

Install using `pip`...  **TBD**

    pip install fastapirestframework


# Note
### This is a new fork of DRF, and serves more as a promise as of now... 
*As and when these functionalities are ready, we'll update this readme*


# Contribution

Any and every contribution is welcome 😊
