import logging
import urllib
from hashlib import sha1

import gluon.contrib.simplejson
from gluon.storage import Storage
from gluon.html import DIV, A, P, XML, INPUT

import stripe


logger = logging.getLogger("web2py.app.foundit.stripeform")
logger.setLevel(logging.DEBUG)

def clean_stripe_session():

    from gluon import current
    current.session.stripe_uuid = None

class Stripe:
    """
    Use in WEB2PY (guaranteed PCI compliant)

def pay():
    from gluon.contrib.stripe import StripeForm
    form = StripeForm(
        pk=STRIPE_PUBLISHABLE_KEY,
        sk=STRIPE_SECRET_KEY,
        amount=150, # $1.5 (amount is in cents)
        description="Nothing").process()
    if form.accepted:
        payment_id = form.response['id']
        redirect(URL('thank_you'))
    elif form.errors:
        redirect(URL('pay_error'))
    return dict(form=form)

Low level API:

    key='<api key>'
    d = Stripe(key).charge(
               amount=100, # 1 dollar!!!!
               currency='usd',
               description='test charge')
    print d
    print Stripe(key).check(d['id'])
    print Stripe(key).refund(d['id'])

    Sample output (python dict):
    {u'fee': 0, u'description': u'test charge', u'created': 1321242072, u'refunded': False, u'livemode': False, u'object': u'charge', u'currency': u'usd', u'amount': 100, u'paid': True, u'id': u'ch_sdjasgfga83asf', u'card': {u'exp_month': 5, u'country': u'US', u'object': u'card', u'last4': u'4242', u'exp_year': 2012, u'type': u'Visa'}}
    if paid is True than transaction was processed

    """

    def __init__(self, key):
        self.key = key
        stripe.api_key = key

    def charge(self, amount,  # in cents
               currency='usd',
               idempotency_key=None,
               token=None,
               description='test charge',
               more=None):
        if not token:
            return Storage()  # We should only get token from script.js
        res = Storage()
        from gluon import current
        T = current.T
        res.paid = False
        try:
            customer = Customer()
            if not customer.has_card(token):
                token = customer.create_card(token)

            d = {
                'amount': amount,
                'currency': currency,
                'customer': customer.id,
                'source': token,
                'description': description,
                'idempotency_key': idempotency_key
            }
            if more:
                d.update(more)

            res = stripe.Charge.create(**d)
        except (stripe.error.CardError, e):
            # it's a decline, stripe.error.CardError will be caught
            from gluon import current
            T = current.T
            res.errors = T(e.message)
            res.reason = T(e.json_body['error'].get('decline_code', ''))
        except (stripe.error.StripeError, e):
            logger.error("%s", e)
            res.errors = str(XML(T("Unexpected error when communicating with Stripe. If the problem persists, "
                                "let us know at <a href='mailto://webmaster@%s'>webmaster@%s</a>", current.SITE_NAME)))
        return res

    def check(self, charge_id):
        return stripe.Charge.retrieve(charge_id)

    def refund(self, charge_id):
        return stripe.Refund.create(charge=charge_id)


class Customer(object):
    from gluon import current
    def __init__(self):
        pass

    def __getattr__(self, name):
        return self._stripe_customer.get(name)


    @property
    @current.cache('_stripe_customer%s' % current.session.auth.user.id,
                   time_expire=3600,
                   cache_model=current.cache.ram)
    def _stripe_customer(self):
        """ Get stripe customer as stored in the stripe_id extra
        field of the auth_user table. Create a customer if non exists """
        from gluon import current
        user = current.session.auth.user
        db = current.globalenv['db']
        stripe_id = db.auth_user(user.id).stripe_id
        if not stripe_id:
            # get one
            logger.debug("Create Stripe customer")
            customer = stripe.Customer.create(
                description="%s %s" % (user.first_name, user.last_name),
                email=user.email,
                metadata={'user_id': user.id}, )
            logger.debug("Done created Stripe customer")
            db.auth_user[user.id] = dict(stripe_id=customer.id)
        else:
            logger.debug("Retrieve Stripe customer")
            customer = stripe.Customer.retrieve(stripe_id)
            logger.debug("Done retrieving Stripe customer")
        return customer

    @property
    @current.cache('valid_cards%s' % current.session.auth.user.id,
                   time_expire=3600,
                   cache_model=current.cache.ram)
    def valid_cards(self):
        cust_id = self._stripe_customer.id
        cards = stripe.Customer.retrieve(cust_id).sources.all()
        from datetime import datetime
        now = datetime.now()
        res = [c for c in cards['data']
                if c['exp_year'] > now.year or (c['exp_year'] == now.year
                                                and c['exp_month'] >= now.month)]
        return res

    def create_card(self, card_data):
        """ card_data may be a dict or a token returned by stripe.js """
        from gluon import current
        card = self._stripe_customer.sources.create(source=card_data)
            # clear cache for valid_cards
        current.cache.ram.clear('valid_cards%s' % current.session.auth.user.id)

        return card

    def has_card(self, card_token):
        return card_token in [c.id for c in self.valid_cards]


class StripeForm(object):
    def __init__(self, pk, sk, amount,  # in cents
                 description,
                 currency='usd',
                 currency_symbol='$',
                 security_notice=True,
                 disclosure_notice=True,
                 template=None,
                 extraenv=None,
                 more=None):
        from gluon import current, redirect, URL
        from gluon.utils import web2py_uuid
        if not (current.request.is_local or current.request.is_https):
            redirect(URL(args=current.request.args, scheme='https'))
        self.pk = pk
        self.sk = sk
        self.stripe = Stripe(sk)
        self.amount = amount
        self.description = description
        self.currency = currency
        self.currency_symbol = currency_symbol
        self.security_notice = security_notice
        self.disclosure_notice = disclosure_notice
        self.template = template or TEMPLATE
        self.accepted = None
        self.more = more
        self.errors = None
        self.signature = sha1(repr((current.session.auth.user.id,
                                    self.amount,
                                    self.description))).hexdigest()
        self.uuid = current.session.stripe_uuid or web2py_uuid()
        self.extraenv = extraenv
        self.customer = None
        if not current.session.stripe_uuid:
            current.session.stripe_uuid = self.uuid

    def process(self):
        from gluon import current
        request = current.request
        if request.post_vars:
            if self.signature == request.post_vars.signature:
                self.response = self.stripe.charge(
                    token=request.post_vars.stripeToken,
                    amount=self.amount,
                    idempotency_key=self.uuid,
                    description=self.description,
                    more=self.more,
                    currency=self.currency)
                if self.response.get('paid', False):
                    current.session.stripe_uuid = None
                    self.accepted = True
                    return self
            self.errors = True
        return self

    def xml(self):
        from gluon.template import render
        from gluon import current
        T = current.T
        if self.accepted:
            return str(T("Your payment was processed successfully"))
        cards = default_card = None
        try:
            self.customer = Customer()
            cards=self.customer.valid_cards
            default_card=self.customer.default_source
        except (stripe.error.APIConnectionError, e):
            return str(DIV(XML(T("We've got some connexion error when communicating with Stripe. If the problem persists, "
                                "let us know at <a href='mailto://webmaster@%s'>webmaster@%s</a>", current.SITE_NAME, current.SITE_NAME)),
                            _class="error"))

        except (stripe.error.StripeError, e):
            logger.error("%s", e)
            return str(DIV(XML(T("Unexpected error when communicating with Stripe. If the problem persists, "
                                "let us know at <a href='mailto://webmaster@%s'>webmaster@%s</a>", current.SITE_NAME, current.SITE_NAME)),
                            _class="error"))
        context = dict(amount=self.amount,
                       signature=self.signature,
                       pk=self.pk,
                       currency_symbol=self.currency_symbol,
                       security_notice=self.security_notice,
                       disclosure_notice=self.disclosure_notice,
                       cards=cards,
                       error=(self.errors and self.response.errors) or '',
                       default_card=default_card)
        context.update({'T':T, 'A':A, 'DIV':DIV, 'XML':XML, 'INPUT':INPUT})
        return render(content=self.template, context=context)


# TODO use web2py FOMR in order to protect from double submission
TEMPLATE = """
<script type="text/javascript" src="https://js.stripe.com/v2/"></script>
<script>
jQuery(function(){
    // This identifies your website in the createToken call below
    Stripe.setPublishableKey('{{=pk}}');

    var stripeResponseHandler = function(status, response) {
      var jQueryform = jQuery('#payment-form');

      if (response.error) {
        // Show the errors on the form
        jQuery('.payment-errors').text(response.error.message).show();
        jQueryform.find('button').prop('disabled', false);
      } else {
        // token contains id, last4, and card type
        var token = response.id;
        // Insert the token into the form so it gets submitted to the server
        var tokenInput = jQuery('<input type="hidden" name="stripeToken" />');
        jQueryform.append(tokenInput.val(token));
        // and re-submit
        jQueryform.get(0).submit();
      }
    };

    jQuery(function(jQuery) {
      jQuery('#payment-form').submit(function(e) {

        var jQueryform = jQuery(this);

        // Disable the submit button to prevent repeated clicks
        jQueryform.find('button').prop('disabled', true);

        Stripe.createToken(jQueryform, stripeResponseHandler);

        // Prevent the form from submitting with the default action
        return false;
      });
    });
});
</script>

<h3>{{=T("Payment Amount: %(currency)s %(amount)s", dict(currency=currency_symbol,
      amount="%.2f" % (0.01*amount)))}}</h3>
{{ if cards:}}
    <div class="panel panel-default">
    <div class="panel-body">
    <h4>{{=T("Pay With an Existing Card")}}</h4>
    <form action="" method="POST" id="payment-existing-card" class="form-horizontal">
    {{for i,card in enumerate(cards):}}
        <div class="form-row form-group">
            <div class="controls col-sm-offset-1">
        {{=INPUT(_type='radio', _name='stripeToken', _id='stripeToken%d' % i, _value=card.id, value=default_card)}} {{=card.brand}} ************{{=card.last4}} {{=card.exp_month}}/{{=card.exp_year}}
        </div></div>
    {{pass}}
        <div class="form-row form-group">
            <div class="controls col-sm-offset-4 col-lg-8">
    <button type="submit" value="submitcard" class="btn btn-primary">{{=T("Submit Payment")}}</button>
        </div></div>
  <input type="hidden" name="signature" value="{{=signature}}" />
    </form>
    </div>
    </div>
{{pass}}
<div class="panel panel-default">
<div class="panel-body">
<h4>{{=T("Pay With a New Card")}}</h4>
<form action="" method="POST" id="payment-form" class="form-horizontal">

  <div class="form-row form-group">
    <label class="col-sm-4 control-label">{{=T("Card Number")}}</label>
    <div class="controls col-sm-8">
      <input type="text" size="20" style="width:200px" data-stripe="number"
             name="number" placeholder="4242424242424242" class="form-control"/>
    </div>
  </div>

  <div class="form-row form-group">
    <label class="col-sm-4 control-label">{{=T("Expiration")}}</label>
    <div class="controls col-sm-8">
      <input type="text" size="2" style="width:60px; display:inline-block"
      name='exp_month' data-stripe="exp-month" placeholder="MM"
      class="form-control"/>
      /
      <input type="text" size="4" style="width:80px; display:inline-block"
             name='exp_year' data-stripe="exp-year" placeholder="YYYY"
             class="form-control"/>
    </div>
  </div>

  <div class="form-row form-group">
    <label class="col-sm-4 control-label">{{=T("CVC")}}</label>
    <div class="controls col-sm-8">
      <input type="text" size="4" style="width:80px" data-stripe="cvc"
             name='cvc' placeholder="XXX" class="form-control"/>
      <a href="http://en.wikipedia.org/wiki/Card_Verification_Code" target="_blank">{{=T("What is this?")}}</a>
    </div>
  </div>

  <div class="form-row form-group">
    <div class="controls col-sm-offset-4 col-lg-8">
      <button type="submit" value="submit" class="btn btn-primary">{{=T("Submit Payment")}}</button>
      <div class="payment-errors error">{{=error}}</div>
    </div>
  </div>
  <input type="hidden" name="signature" value="{{=signature}}" />
</form>
</div>
</div>

"""
