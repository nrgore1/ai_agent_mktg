"""Build product-specific audiences from reviewed consent evidence; never send."""
from datetime import datetime, timezone
import hashlib
import re


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def build_audience(records, *, product_id, suppressions=(), checked_at=None):
    """Input records must be independently reviewed, not inferred from signups.

    Withdrawal and malformed latest evidence fail closed. A matching email
    never extends permission across products or brands. Caller must refresh
    source consent and provider suppression immediately before any dispatch.
    """
    now = checked_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('checked_at must be timezone aware')
    denied = {str(email).strip().lower() for email in suppressions}
    grouped = {}
    for row in records:
        if row.get('product_id') != product_id or row.get('purpose') != 'product_marketing':
            continue
        email = str(row.get('email') or '').strip().lower()
        grouped.setdefault(email, []).append(row)
    eligible, excluded = [], []
    for email, events in sorted(grouped.items()):
        reasons = []
        dated = [(timestamp(r.get('occurred_at')), r) for r in events]
        if any(t is None or t > now for t, _ in dated):
            reasons.append('invalid_or_future_consent_time')
            row = events[-1]
        else:
            latest = max(t for t, _ in dated)
            latest_rows = [r for t, r in dated if t == latest]
            row = latest_rows[0]
            if any(r != row for r in latest_rows):
                reasons.append('conflicting_latest_evidence')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            reasons.append('invalid_email')
        if email in denied or row.get('suppressed') is not False:
            reasons.append('suppressed_or_suppression_unknown')
        if row.get('status') != 'confirmed' or row.get('basis') != 'explicit':
            reasons.append('explicit_marketing_permission_missing_or_withdrawn')
        if row.get('channel') != 'email':
            reasons.append('email_scope_missing')
        if row.get('source_verified') is not True:
            reasons.append('source_evidence_unverified')
        if row.get('source_kind') not in {'signup_checkbox', 'privacy_center', 'double_optin', 'recorded_request'}:
            reasons.append('affirmative_action_unproven')
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('source_reference', 'notice_version', 'notice_text')):
            reasons.append('consent_notice_or_reference_missing')
        if row.get('email_confirmed') is not True or row.get('account_active') is not True:
            reasons.append('recipient_not_confirmed_active')
        if row.get('synthetic') is not False or email.endswith(('.invalid', '@example.com', '@example.org', '@example.net')):
            reasons.append('synthetic_or_unclassified_record')
        if row.get('expires_at'):
            expiry = timestamp(row['expires_at'])
            if expiry is None or expiry <= now:
                reasons.append('consent_expired_or_invalid')
        if reasons:
            excluded.append({'recipient_sha256': hashlib.sha256(email.encode()).hexdigest(), 'reasons': reasons})
        else:
            eligible.append({'email': email, 'product_id': product_id,
                             'source_reference': row['source_reference'],
                             'consented_at': row['occurred_at'], 'notice_version': row['notice_version']})
    return {'product_id': product_id, 'checked_at': now.isoformat(), 'eligible': eligible,
            'excluded': excluded, 'requires_live_recheck_before_send': True,
            'dispatch_authorized': False}
