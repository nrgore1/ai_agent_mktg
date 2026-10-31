"""Product-scoped, confirmed marketing subscriptions. No campaign dispatch."""
import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import urllib.request
import uuid

from .core import Invalid, now
from . import postmark

BRANDS = {
    'weddingos': {'product_id': 4, 'name': 'WeddingOS', 'host': 'weddingos.pro',
                 'topics': 'planning tools, practical tips, new features and offers', 'privacy': '/privacy', 'reply_to': 'naren@atmakosh.com'},
    'jodiusa': {'product_id': 6, 'name': 'JodiUSA', 'host': 'www.jodiusa.com',
               'topics': 'community news, events and service updates', 'privacy': '/privacy/', 'reply_to': 'rashmi@jodiusa.com'},
    'memoire': {'product_id': 5, 'name': 'Memoire Studio', 'host': 'memoirbookstudio.com',
               'topics': 'photo-book ideas, new features and offers', 'privacy': '/compliance', 'reply_to': 'naren@atmakosh.com'},
}
VERSION = '2026-10-30-v1'
PREFIX = '/marketing-updates/'
GENERIC = {'accepted': True, 'message': 'If this address can receive the requested email, check its inbox. You are not subscribed until you confirm. Allow a few minutes; requests are limited to prevent unwanted email.'}


def notice(brand, config=None):
    b = config or BRANDS[brand]
    return f"I am 18 or older and want marketing emails from {b['name']} about {b['topics']}. This is optional. I can unsubscribe at any time. This permission applies only to {b['name']}."


def brand_for_host(host):
    host = host.lower().split(':')[0]
    for slug, b in BRANDS.items():
        if host in {b['host'], b['host'].removeprefix('www.'), 'www.' + b['host'].removeprefix('www.')}:
            return slug
    raise Invalid('Unknown marketing site')


class MarketingConsent:
    def __init__(self, store, secret=None, mailer=None, clock=None, brands=None):
        self.s = store
        self.brands = brands if brands is not None else BRANDS
        self.secret = secret if secret is not None else os.environ.get('GROWTHPILOT_CONSENT_SECRET', '')
        self.mailer = mailer or self.send_email
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))

    def sign(self, value):
        if len(self.secret) < 32:
            raise Invalid('Subscription service is not configured')
        return hmac.new(self.secret.encode(), value.encode(), hashlib.sha256).hexdigest()

    def identifier(self, brand, email):
        return self.sign('recipient:' + brand + ':' + email)

    def withdrawal_token(self, record):
        return record['id'] + '.' + self.sign('withdraw:' + record['brand'] + ':' + record['id'])

    def event(self, db, record, action):
        stamp = self.clock().isoformat()
        event = {'id': uuid.uuid4().hex, 'product_id': record['product_id'], 'brand': record['brand'],
                 'consent_id': record['id'], 'action': action, 'at': stamp,
                 'notice_version': record.get('notice_version',VERSION), 'notice_sha256': hashlib.sha256(record.get('notice_text','').encode()).hexdigest()}
        self.s.save(db, 'marketing_consent_events', event)
        self.s.audit(db, 'marketing_' + action, record['id'], {'brand': record['brand'], 'notice_version': record.get('notice_version',VERSION)}, 'subscriber')

    def limited(self, db, identity, maximum, seconds):
        ident = self.sign('rate:' + identity)
        current = self.clock().timestamp()
        db.execute("DELETE FROM records WHERE kind='marketing_rate_limits' AND CAST(json_extract(data, '$.start') AS REAL) < ?", (current - 172800,))
        rows = {r['id']: r for r in self.s.rows(db, 'marketing_rate_limits')}
        row = rows.get(ident, {'id': ident, 'start': current, 'count': 0})
        if current - row['start'] >= seconds:
            row.update(start=current, count=0)
        if row['count'] >= maximum:
            return True
        row['count'] += 1
        self.s.save(db, 'marketing_rate_limits', row)
        return False

    def request(self, brand, data, remote='unknown', manage=False):
        if brand not in self.brands or set(data) - {'email', 'consent', 'company', 'notice_version'}:
            raise Invalid('Invalid subscription request')
        if not manage and not self.brands[brand].get('enabled',True):raise Invalid('New subscriptions are not enabled by this site operator')
        if data.get('company'):
            return dict(GENERIC)
        if not manage and (data.get('consent') is not True or data.get('notice_version') != VERSION):
            raise Invalid('Please read and explicitly choose the optional marketing permission')
        email = str(data.get('email', '')).strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", email):
            raise Invalid('Enter a valid email address')
        if '..' in email or email.count('@') != 1:
            raise Invalid('Enter a valid email address')
        ident = self.identifier(brand, email)
        stamp = self.clock()
        with self.s.db() as db:
            if self.limited(db, 'global', 100, 3600) or self.limited(db, 'ip:' + remote, 20, 3600):
                return dict(GENERIC)
            if self.limited(db, 'address:' + brand + ':' + email, 1, 900) or self.limited(db, 'daily:' + email, 3, 86400):
                return dict(GENERIC)
            record = next((r for r in self.s.rows(db, 'marketing_subscriptions') if r['id'] == ident), None)
            if manage:
                if not record:
                    return dict(GENERIC)
                token = None
            else:
                if record and record['status'] == 'confirmed':
                    return dict(GENERIC)
                token = secrets.token_urlsafe(32)
                record = dict(record or {}, id=ident, brand=brand, product_id=self.brands[brand]['product_id'], email=email,
                              status='pending', confirmed_at=None, withdrawn_at=None, notice_text=notice(brand,self.brands[brand]), notice_version=VERSION,
                              source='https://' + self.brands[brand]['host'] + PREFIX, requested_at=stamp.isoformat(),
                              confirm_hash=hashlib.sha256(token.encode()).hexdigest(),
                              confirm_expires=(stamp + dt.timedelta(hours=24)).isoformat(),
                              synthetic=email.endswith(('@example.com', '@example.org', '@example.net', '.invalid')),
                              delivery_status='pending')
                self.s.save(db, 'marketing_subscriptions', record)
                self.event(db, record, 'requested')
        # Network access is deliberately outside the database transaction.
        try:
            receipt = self.mailer(record, token, manage)
            status = 'accepted'
        except Exception:
            receipt = {}; status = 'not_confirmed'
        with self.s.db() as db:
            latest = self.s.get(db, 'marketing_subscriptions', ident)
            if latest.get('status')=='erased':return dict(GENERIC)
            latest.update(delivery_status=status, last_email_at=self.clock().isoformat(), provider_id=receipt.get('provider_id'))
            self.s.save(db, 'marketing_subscriptions', latest)
            self.s.audit(db, 'marketing_confirmation_delivery', ident, {'status': status, 'kind': 'manage' if manage else 'confirm'}, 'subscription_service')
        return dict(GENERIC)

    def confirm(self, brand, token):
        if not self.brands[brand].get('enabled',True):raise Invalid('New subscriptions are not enabled by this site operator')
        if not isinstance(token, str) or not 32 <= len(token) <= 100:
            raise Invalid('This confirmation link is invalid or has expired')
        hashed = hashlib.sha256(token.encode()).hexdigest()
        with self.s.db() as db:
            record = next((r for r in self.s.rows(db, 'marketing_subscriptions') if r['brand'] == brand and
                           hmac.compare_digest(r.get('confirm_hash', ''), hashed)), None)
            if not record or record['status'] != 'pending' or dt.datetime.fromisoformat(record['confirm_expires']) <= self.clock():
                raise Invalid('This confirmation link is invalid or has expired')
            record.update(status='confirmed', confirmed_at=self.clock().isoformat(), confirm_hash='', confirm_expires='')
            self.s.save(db, 'marketing_subscriptions', record)
            self.event(db, record, 'confirmed')
            # Synthetic records remain evidence for QA, never campaign leads.
            if not record['synthetic']:
                lid = 'marketing-' + record['id']
                lead = next((r for r in self.s.rows(db, 'leads') if r['id'] == lid), {})
                if lead.get('erased_at'):lead={}
                lead.update(id=lid, product_id=record['product_id'], email=record['email'], name='Subscriber',
                            consent='opt_in', pipeline='customer', source=record['source'], stage=lead.get('stage', 'research'),
                            marketing_brand=brand, marketing_consent_id=record['id'],
                            consent_notice_version=record['notice_version'], updated_at=now())
                self.s.save(db, 'leads', lead)
            return {'confirmed': True, 'brand': self.brands[brand]['name'],
                    'manage_url': PREFIX + 'withdraw#' + self.withdrawal_token(record)}

    def withdraw(self, brand, token):
        if not isinstance(token, str) or not re.fullmatch(r'[a-f0-9]{64}\.[a-f0-9]{64}', token):
            raise Invalid('This preference link is invalid')
        ident, signature = token.split('.')
        if not hmac.compare_digest(signature, self.sign('withdraw:' + brand + ':' + ident)):
            raise Invalid('This preference link is invalid')
        with self.s.db() as db:
            record = self.s.get(db, 'marketing_subscriptions', ident)
            if record['brand'] != brand:
                raise Invalid('This preference link belongs to a different product')
            if record['status']=='erased':return {'withdrawn':True,'brand':self.brands[brand]['name']}
            if record['status'] != 'withdrawn':
                record.update(status='withdrawn', withdrawn_at=self.clock().isoformat(), confirm_hash='', confirm_expires='')
                self.s.save(db, 'marketing_subscriptions', record)
                self.event(db, record, 'withdrawn')
            for lead in self.s.rows(db, 'leads'):
                if lead.get('marketing_consent_id') == ident:
                    lead.update(consent='opt_out', updated_at=now())
                    self.s.save(db, 'leads', lead)
            return {'withdrawn': True, 'brand': self.brands[brand]['name']}

    def validate_lead(self, db, lead, payload):
        ident = lead.get('marketing_consent_id')
        if not ident:
            if len(self.secret)>=32:
                for brand,b in self.brands.items():
                    if b['product_id']==payload.get('product_id'):
                        marker=self.identifier(brand,str(lead.get('email','')).strip().lower())
                        if any(r['id']==marker for r in self.s.rows(db,'marketing_erasure_suppressions')):raise Invalid('Recipient has an erasure suppression')
            return
        record = self.s.get(db, 'marketing_subscriptions', ident)
        if not self.brands.get(record['brand'],{}).get('enabled',True):raise Invalid('Tenant marketing collection is disabled')
        if record['brand'].startswith('tenant-'):raise Invalid('Tenant campaign delivery requires its own sender and release approval')
        if record['status'] != 'confirmed' or record.get('synthetic') or record['email'] != lead.get('email'):
            raise Invalid('Current confirmed marketing permission is required')
        if payload.get('marketing_brand') != record['brand'] or payload.get('product_id') != record['product_id'] or lead.get('marketing_brand') != record['brand'] or lead.get('product_id') != record['product_id']:
            raise Invalid('Marketing permission does not cover this product or brand')

    def summary(self):
        with self.s.db() as db:
            rows = self.s.rows(db, 'marketing_subscriptions')
            records = [{k: r.get(k) for k in ('id', 'brand', 'product_id', 'email', 'status', 'notice_version', 'notice_text',
                       'source', 'requested_at', 'confirmed_at', 'withdrawn_at', 'erased_at', 'synthetic', 'delivery_status')} for r in rows]
            return {'brands': [{**b, 'slug': slug, 'form_url': 'https://' + b['host'] + PREFIX,
                                'confirmed': sum(r['brand'] == slug and r['status'] == 'confirmed' and not r.get('synthetic') for r in rows),
                                'pending': sum(r['brand'] == slug and r['status'] == 'pending' and not r.get('synthetic') for r in rows),
                                'erased': sum(r['brand']==slug and r['status']=='erased' for r in rows),
                                'withdrawn': sum(r['brand'] == slug and r['status'] == 'withdrawn' and not r.get('synthetic') for r in rows)} for slug,b in self.brands.items()],
                    'records': records, 'campaign_dispatch_enabled_by_subscription': False}

    def send_email(self, record, token, manage):
        brand = self.brands[record['brand']]
        home = 'https://' + brand['host'] + PREFIX
        stop = home + 'withdraw#' + self.withdrawal_token(record)
        text = (f"You requested to manage marketing emails from {brand['name']}.\n\nStop these emails: {stop}\n\n"
                if manage else f"You asked to receive marketing emails from {brand['name']}.\n\nYour choice:\n{record['notice_text']}\n\nConfirm within 24 hours: {home}confirm#{token}\n\nStop or cancel this request: {stop}\n\n")
        if manage=='rights':text=f"You requested private access to your {brand['name']} marketing consent record.\n\nExport or delete within 30 minutes: {home}rights#{token}\n\nThis link does not grant account access.\n\n"
        text += 'If you did not request this email, ignore it. No new subscription is activated without confirmation.\n\n' + brand.get('operator','Atmakosh LLC') + '\n' + brand['reply_to']
        body = {'From': 'naren@atmakosh.com', 'ReplyTo': brand['reply_to'], 'To': record['email'],
                'Subject': ('Private consent access: ' if manage=='rights' else 'Manage ' if manage else 'Confirm ') + brand['name'] + ' marketing emails',
                'TextBody': text, 'MessageStream': 'outbound', 'TrackOpens': False, 'TrackLinks': 'None',
                'Tag': 'marketing-consent', 'Metadata': {'brand': record['brand'], 'consent_id': record['id']}}
        mode = os.environ.get('GROWTHPILOT_CONSENT_MODE', 'live')
        if mode == 'file':
            if os.environ.get('GROWTHPILOT_ENVIRONMENT') != 'consent-qa' or os.environ.get('GROWTHPILOT_SECURE_COOKIE') == 'true':
                raise Invalid('Test mail is restricted to the isolated QA service')
            folder = Path(self.s.path).parent / 'consent-test-outbox'; folder.mkdir(mode=0o700, exist_ok=True)
            p = folder / (uuid.uuid4().hex + '.json'); p.write_text(json.dumps(body)); p.chmod(0o600)
            return {'provider_id': 'isolated-test'}
        if mode != 'live' or os.environ.get('GROWTHPILOT_ENABLE_CONSENT_EMAIL') != 'true':
            raise Invalid('Confirmation delivery is not enabled')
        account = postmark.configured(record['product_id'])
        if account.get('sender') != 'naren@atmakosh.com' or account.get('status') != 'configured' or not account.get('token'):
            raise Invalid('Confirmed product sender is required')
        req = urllib.request.Request('https://api.postmarkapp.com/email', data=json.dumps(body).encode(),
              headers={'Content-Type':'application/json','Accept':'application/json','X-Postmark-Server-Token':account['token']})
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.load(response)
        if result.get('ErrorCode') != 0 or not result.get('MessageID'):
            raise Invalid('Confirmation delivery was not accepted')
        return {'provider_id': result['MessageID']}
