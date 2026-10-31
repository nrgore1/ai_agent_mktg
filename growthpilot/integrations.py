"""PRD provider boundary: read-only checks, scoped CRM exchange and approved handoffs.

No account discovery, credential export, automatic invites or social publication.
"""
import csv
import datetime as dt
import io
import json
import os
import re
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit, quote
from .core import Invalid, digest, now
from . import postmark

INTERNAL_PRODUCTS = {10, 11, 12, 13, 14}
CRM_FIELDS = ['name', 'email', 'organization', 'pipeline', 'source']


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Invalid('Provider redirects are not accepted')


def read_json(url, headers=None):
    request = urllib.request.Request(url, headers={'Accept': 'application/json', **(headers or {})})
    # URLs come from fixed provider routes or trusted deployment configuration, never UI input.
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as response:
        raw = response.read(1048577)
    if len(raw) > 1048576:
        raise Invalid('Provider response too large')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise Invalid('Invalid provider response')
    return value


def calendar_event(value):
    if not isinstance(value, dict) or set(value) != {'start', 'end', 'location'}:
        raise Invalid('Calendar requires start, end and location')
    result = {}
    for field in ('start', 'end'):
        try:
            stamp = dt.datetime.fromisoformat(value[field])
            if stamp.tzinfo is None:
                raise ValueError()
            result[field] = stamp.astimezone(dt.timezone.utc).isoformat()
        except (ValueError, TypeError):
            raise Invalid('Calendar times require explicit timezone offsets')
    duration = dt.datetime.fromisoformat(result['end']) - dt.datetime.fromisoformat(result['start'])
    if duration.total_seconds() <= 0 or duration > dt.timedelta(days=1):
        raise Invalid('Meeting duration must be positive and at most 24 hours')
    result['location'] = clean(value['location'], 500)
    return result


def clean(value, limit=2000):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
        raise Invalid('Invalid text field')
    return value.strip()


def ics_text(value):
    return str(value).replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    # RFC 5545: 75 octets, preserving UTF-8 character boundaries.
    lines, part = [], ''
    for char in line:
        if len((part + char).encode('utf-8')) > 75:
            lines.append(part)
            part = ' '
        part += char
    return '\r\n'.join(lines + [part])


class IntegrationHub:
    def __init__(self, store):
        self.s = store

    def payments(self):
        result = {'status': 'missing', 'accounts': [], 'captured_at': None,
                  'margin_ready': False, 'note': 'Processor totals are not recognized product revenue. Currencies and shared accounts remain separate.'}
        path = Path(self.s.path).parent / 'economics-source.json'
        if not path.exists():
            return result
        try:
            if path.stat().st_size > 262144:
                raise ValueError()
            source = json.loads(path.read_text()).get('actual_finance', {})
            stamp = dt.datetime.fromisoformat(source['captured_at'])
            age = (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds()
            seen = set()
            for account in source.get('processor_accounts', []):
                fingerprint = account.get('account_fingerprint')
                if fingerprint:
                    if fingerprint in seen:
                        raise ValueError('Duplicate processor account')
                    seen.add(fingerprint)
                rows = []
                for row in account.get('captured_charge_groups', []):
                    if not re.fullmatch(r'[a-zA-Z]{3}', str(row.get('currency', ''))):
                        raise ValueError()
                    fields = ('captured_count', 'captured_minor', 'refunded_to_date_minor', 'disputed_count')
                    if any(type(row.get(k)) is not int or row[k] < 0 for k in fields):
                        raise ValueError()
                    rows.append({k: row[k] for k in ('currency',) + fields})
                result['accounts'].append({'products': account.get('configured_product_ids', []),
                    'status': account.get('status', 'missing'), 'charges': rows,
                    'balance_arithmetic_valid': account.get('balance_arithmetic_valid') is True})
            result.update(status='fresh' if 0 <= age <= 86400 else 'stale', captured_at=source['captured_at'],
                          period_start=source.get('period_start'), period_end_exclusive=source.get('period_end_exclusive'),
                          missing=source.get('missing', []))
        except (ValueError, TypeError, KeyError, OSError):
            result.update(status='invalid', accounts=[])
        return result

    def overview(self):
        with self.s.db() as db:
            checks = {r['id']: r for r in self.s.rows(db, 'integration_checks')}
            products = self.s.rows(db, 'products')
            leads = self.s.rows(db, 'leads')
            keys = db.execute('SELECT product_id FROM api_keys').fetchall()
        modes = [
            ('llm', 'Local Kimi', 'local', 'Read-only model availability check; drafting never approves copy.'),
            ('email', 'Postmark', 'provider', 'Exact approved recipient and current consent are checked again at delivery.'),
            ('crm', 'Customer relationship management', 'built_in_csv', 'Product-scoped CSV exchange; imports never create marketing permission.'),
            ('github', 'GitHub', 'read_only_and_gated_delivery', 'Repository check; issue creation also requires live mode and exact approval.'),
            ('analytics', 'Website analytics', 'built_in_ingestion', 'Product API keys, idempotent actual events and attributed reports.'),
            ('payments', 'Payment analytics', 'read_only_snapshot', 'Protected aggregate snapshot; no payment or subscription mutation.'),
            ('social', 'Social publishing', 'approved_manual', 'LinkedIn, X and registered channels: review, approve, export, record receipt.'),
            ('research', 'Public web research', 'read_only', 'Public HTTPS evidence starts unverified; founder review is required.'),
            ('calendar', 'Meeting scheduling', 'approved_ics', 'Approved calendar file handoff; no automated invitation or availability claim.')]
        items = []
        for key, label, mode, note in modes:
            check = checks.get(key)
            if check:
                check = dict(check, stale=(dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(check['checked_at'])).total_seconds() > 86400)
            items.append(dict(id=key, name=label, mode=mode, note=note, check=check,
                              can_check=key in ('llm', 'email', 'github')))
        return {'integrations': items, 'payments': self.payments(),
                'crm': {'contacts': len(leads), 'import_columns': CRM_FIELDS, 'max_rows': 500},
                'analytics': {'products_with_keys': sorted({r[0] for r in keys}), 'endpoint': '/api/ingest'},
                'products': [{'id': p['id'], 'name': p['name'], 'public_launch': p['id'] not in INTERNAL_PRODUCTS} for p in products],
                'account_dependencies': ['External CRM, third-party website analytics and authenticated social/calendar accounts are not configured by this desk.'],
                'product_engineering': 'Separate product backlogs; this release changes AgentVire only.'}

    def check(self, connector, actor):
        if connector not in ('llm', 'email', 'github'):
            raise Invalid('Unsupported connection check')
        with self.s.db() as db:
            previous = next((r for r in self.s.rows(db, 'integration_checks') if r['id'] == connector), None)
            if previous and (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(previous['checked_at'])).total_seconds() < 60:
                raise Invalid('Wait 60 seconds before checking this provider again')
            result = {'id': connector, 'checked_at': now(), 'status': 'checking', 'external_mutations': 0}
            self.s.save(db, 'integration_checks', result)
        try:
            if connector == 'llm':
                model = os.environ.get('GROWTHPILOT_OLLAMA_MODEL', '')
                base = os.environ.get('GROWTHPILOT_OLLAMA_URL', '')
                if not model or 'kimi' not in model.lower() or ':cloud' in model or not base:
                    raise Invalid('Local Kimi is not configured')
                available = read_json(base.rstrip('/') + '/api/tags').get('models', [])
                if not any(m.get('name') == model or m.get('model') == model for m in available):
                    raise Invalid('Configured local model is not available')
                result.update(status='healthy', model=model, note='Availability verified; generation quality is evaluated separately.')
            elif connector == 'github':
                repo = os.environ.get('GROWTHPILOT_GITHUB_REPO', '')
                if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo):
                    raise Invalid('GitHub repository is not configured')
                token = os.environ.get('GROWTHPILOT_GITHUB_TOKEN', '')
                headers = {'Authorization': 'Bearer ' + token} if token else {}
                body = read_json('https://api.github.com/repos/' + repo, headers)
                if str(body.get('full_name', '')).lower() != repo.lower():
                    raise Invalid('Repository response does not match configuration')
                result.update(status='healthy', note='Repository readable; publishing permissions were not tested.')
            else:
                accounts = postmark.accounts()
                if not accounts:
                    raise Invalid('Postmark accounts are not configured')
                verified = []
                for name, account in accounts.items():
                    if account.get('status') != 'configured' or not account.get('token') or not account.get('stream'):
                        raise Invalid('Postmark account configuration is incomplete')
                    headers = {'X-Postmark-Server-Token': account['token']}
                    server = read_json('https://api.postmarkapp.com/server', headers)
                    if str(server.get('ID')) != str(account.get('server_id')):
                        raise Invalid('Postmark server identity changed')
                    stream = read_json('https://api.postmarkapp.com/message-streams/' + quote(account['stream'], safe=''), headers)
                    if stream.get('ID') != account['stream'] or stream.get('MessageStreamType') != 'Broadcasts' or stream.get('ArchivedAt') or str(stream.get('ServerID')) != str(account.get('server_id')) or stream.get('SubscriptionManagementConfiguration', {}).get('UnsubscribeHandlingType') != 'Postmark':
                        raise Invalid('Postmark broadcast stream does not match')
                    verified.append(name)
                result.update(status='healthy', accounts=verified, note='Server identities and broadcast streams verified; no email sent.')
        except Exception:
            # Provider bodies may include tokens (Postmark /server does). Never retain them or exception text.
            result.update(status='unavailable', note='Configuration or provider check failed. Inspect protected configuration; no external action was taken.')
        with self.s.db() as db:
            self.s.save(db, 'integration_checks', result)
            self.s.audit(db, 'integration_checked', connector, {'status': result['status'], 'external_mutations': 0}, actor)
        return result

    def import_crm(self, data, actor):
        if set(data) != {'product_id', 'csv', 'request_id', 'preview'} or type(data['preview']) is not bool:
            raise Invalid('Provide product_id, csv, request_id and boolean preview')
        raw = clean(data['csv'], 200000)
        request_id = clean(data['request_id'], 100)
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', request_id):
            raise Invalid('Import request ID must be 8–100 letters, digits, dashes or underscores')
        reader = csv.DictReader(io.StringIO(raw.lstrip('\ufeff')), strict=True)
        if reader.fieldnames != CRM_FIELDS:
            raise Invalid('CSV columns must be exactly: ' + ','.join(CRM_FIELDS))
        rows, emails = [], set()
        try:
            for row in reader:
                if len(rows) >= 500 or set(row) != set(CRM_FIELDS) or any(v is None for v in row.values()):
                    raise Invalid('Invalid CSV or more than 500 contacts')
                row = {k: clean(v, 500) for k, v in row.items()}
                row['email'] = row['email'].lower()
                if not row['name'] or not row['source'] or not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', row['email']):
                    raise Invalid('Each contact needs a name, valid email and provenance source')
                if row['pipeline'] not in ('customer', 'institutional', 'investor', 'partner', 'champion'):
                    raise Invalid('Invalid contact pipeline')
                if row['email'] in emails:
                    raise Invalid('Duplicate email in CSV')
                emails.add(row['email']); rows.append(row)
        except csv.Error:
            raise Invalid('Invalid CSV')
        if not rows:
            raise Invalid('CSV contains no contacts')
        pid = data['product_id']
        batch_id = digest({'product': pid, 'request': request_id})
        content_hash = digest({'product': pid, 'csv': raw})
        with self.s.db() as db:
            self.s.get(db, 'products', pid)
            previous = next((r for r in self.s.rows(db, 'crm_imports') if r['id'] == batch_id), None)
            if previous:
                if previous['content_hash'] != content_hash:
                    raise Invalid('Import request ID was already used for different content')
                return dict(previous['result'], replay=True)
            existing = {str(r.get('email', '')).lower() for r in self.s.rows(db, 'leads', pid)}
            suppressed = {str(r.get('email', '')).lower() for r in self.s.rows(db, 'suppressions')}
            from .marketing_registry import BrandRegistry
            from .marketing_consent import MarketingConsent
            brands = BrandRegistry(self.s).all(db)
            service = MarketingConsent(self.s, brands=brands)
            markers = {r['id'] for r in self.s.rows(db, 'marketing_erasure_suppressions', pid)}
            if markers and len(service.secret) < 32:
                raise Invalid('Restore the consent signing secret before importing contacts')
            accepted, blocked, duplicate = [], 0, 0
            for row in rows:
                erased = any(service.identifier(key, row['email']) in markers for key, b in brands.items() if b['product_id'] == pid) if markers else False
                if row['email'] in suppressed or erased:
                    blocked += 1
                elif row['email'] in existing:
                    duplicate += 1
                else:
                    accepted.append(row)
            result = {'product_id': pid, 'created': 0 if data['preview'] else len(accepted), 'eligible_to_import': len(accepted),
                      'skipped_existing': duplicate, 'skipped_suppressed': blocked, 'preview': data['preview'], 'marketing_permission_created': False}
            if not data['preview']:
                for row in accepted:
                    self.s.save(db, 'leads', dict(row, id=uuid.uuid4().hex, product_id=pid, consent='unknown', stage='research', created_at=now()))
                self.s.save(db, 'crm_imports', {'id': batch_id, 'product_id': pid, 'content_hash': content_hash, 'result': result, 'created_at': now()})
                self.s.audit(db, 'crm_imported', batch_id, result, actor)
            return result

    def export_crm(self, pid, actor):
        def cell(value):
            value = str(value or '')
            return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value
        with self.s.db() as db:
            self.s.get(db, 'products', pid)
            rows = self.s.rows(db, 'leads', pid)
            fields = CRM_FIELDS + ['consent', 'stage', 'suppressed']
            output = io.StringIO(newline=''); writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                if row.get('email'):
                    writer.writerow({k: cell(row.get(k)) for k in fields})
            self.s.audit(db, 'crm_exported', pid, {'records': sum(bool(r.get('email')) for r in rows)}, actor)
        return {'filename': 'agentvire-product-' + str(pid) + '-crm.csv', 'content': output.getvalue(), 'media_type': 'text/csv'}

    def prepare(self, data, actor):
        if set(data) - {'product_id', 'campaign_id', 'kind', 'destination', 'account', 'title', 'content', 'calendar_event', 'request_id'}:
            raise Invalid('Unsupported handoff field')
        kind = data.get('kind')
        if kind not in ('social', 'calendar'):
            raise Invalid('Select social or calendar handoff')
        request_id = clean(data.get('request_id', ''), 100)
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', request_id):
            raise Invalid('A stable handoff request ID is required')
        payload = {k: clean(data.get(k, ''), 10000 if k == 'content' else 500) for k in ('destination', 'account', 'title', 'content')}
        if any(not v for v in payload.values()):
            raise Invalid('Destination, account, title and content are required')
        url = urlsplit(payload['destination']); host = (url.hostname or '').removeprefix('www.')
        if url.scheme != 'https' or url.username or url.password or url.port not in (None, 443):
            raise Invalid('Use an exact HTTPS destination without credentials')
        with self.s.db() as db:
            if self.s.paused(db):
                raise Invalid('System paused')
            p = self.s.get(db, 'products', data.get('product_id'))
            if p['id'] in INTERNAL_PRODUCTS and kind == 'social':
                raise Invalid('This product is internal-only; public launch is not authorized')
            campaign = self.s.get(db, 'campaigns', data.get('campaign_id'))
            if campaign['product_id'] != p['id']:
                raise Invalid('Campaign belongs to another product')
            allowed = {c['domain'] for c in self.s.rows(db, 'channels')} | {'linkedin.com', 'x.com'}
            if kind == 'calendar':
                allowed = {'calendar.google.com', 'outlook.office.com', 'outlook.live.com'}
                payload['calendar_event'] = calendar_event(data.get('calendar_event'))
            elif 'calendar_event' in data:
                raise Invalid('Calendar details belong only to calendar handoffs')
            if host not in allowed:
                raise Invalid('Unsupported handoff destination')
            aid = digest({'product': p['id'], 'request': request_id, 'kind': 'handoff'})
            source_hash = digest(data)
            existing = next((r for r in self.s.rows(db, 'actions', p['id']) if r['id'] == aid), None)
            if existing:
                if existing.get('handoff_source_hash') != source_hash:
                    raise Invalid('Handoff request ID already used for different content')
                return existing
            payload.update(product_id=p['id'], campaign_id=campaign['id'], kind='calendar_handoff' if kind == 'calendar' else 'manual_launch',
                connector='manual', channel=host, recipient=None, sender='naren@vireoka.com' if p['id'] in (1, 2) else 'naren@atmakosh.com',
                cost_cents=0, claims=[], evidence=[{'source': 'founder_handoff', 'note': 'Draft; facts and destination require review.'}],
                requirements='Review exact content, account and destination. Calendar exports do not send invitations.',
                attestations={'product_facts': False, 'channel_rules': False, 'destination': False, 'founder_written': False})
            action = dict(id=aid, product_id=p['id'], campaign_id=campaign['id'], program_id='launch-learn', payload=payload,
                          payload_hash=digest(payload), version=1, status='pending', approval=None, receipt=None, created_at=now(), handoff_source_hash=source_hash)
            self.s.save(db, 'actions', action)
            self.s.audit(db, 'handoff_prepared', aid, {'product_id': p['id'], 'kind': kind}, actor)
            return action

    def export_calendar(self, action_id, actor):
        # Manager validates the current hash, version, expiry, pause and readiness together.
        package = self.s.transition(action_id, 'export', {}, actor=actor)
        payload = package['package']
        if payload.get('kind') != 'calendar_handoff':
            raise Invalid('Approved calendar handoff required')
        event = calendar_event(payload.get('calendar_event'))
        stamp = lambda value: dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AgentVire//Approved Meeting Handoff//EN', 'CALSCALE:GREGORIAN',
                 'METHOD:PUBLISH', 'BEGIN:VEVENT', 'UID:' + action_id + '@agentvire.com', 'DTSTAMP:' + stamp(now()),
                 'DTSTART:' + stamp(event['start']), 'DTEND:' + stamp(event['end']), 'SUMMARY:' + ics_text(payload['title']),
                 'DESCRIPTION:' + ics_text(payload['content']), 'LOCATION:' + ics_text(event['location']), 'END:VEVENT', 'END:VCALENDAR']
        return {'filename': 'agentvire-meeting-' + action_id[:12] + '.ics', 'media_type': 'text/calendar',
                'content': '\r\n'.join(fold(line) for line in lines) + '\r\n', 'payload_hash': package['payload_hash'],
                'external_delivery': False, 'note': 'Import into the reviewed calendar account yourself. No attendees have been invited.'}

    def dispatch(self, operation, data, actor):
        if operation == 'crm-import':
            return self.import_crm(data, actor)
        if operation == 'handoff':
            return self.prepare(data, actor)
        expected = {'check': {'connector'}, 'crm-export': {'product_id'}, 'calendar-export': {'action_id'}}
        if operation not in expected or set(data) != expected[operation]:
            raise Invalid('Invalid integration operation')
        if operation == 'check':
            return self.check(data['connector'], actor)
        if operation == 'crm-export':
            return self.export_crm(data['product_id'], actor)
        return self.export_calendar(data['action_id'], actor)
