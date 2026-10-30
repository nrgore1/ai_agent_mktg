"""Small same-origin preference UI; no account cookies or trackers."""
from html import escape
from .marketing_consent import BRANDS, VERSION, PREFIX, notice

def page(brand, action=''):
    b=BRANDS[brand]
    common=f'<a href="/">{escape(b["name"])}</a><h1>Email updates, by choice</h1><p>Optional updates from {escape(b["name"])}. Your account and access to tools do not depend on subscribing.</p>'
    if action in ('confirm','withdraw'):
        word='Confirm subscription' if action=='confirm' else 'Unsubscribe'
        body=f'<p>{"Confirm your email to activate the permission you chose." if action=="confirm" else "Stop marketing emails from this product. Account and service emails are unaffected."}</p><button id="token-action" data-action="{action}">{word}</button>'
    else:
        body=f'''<form id="subscribe"><label>Email address<input name="email" type="email" autocomplete="email" maxlength="254" required></label><div class="trap" aria-hidden="true"><label>Company<input name="company" tabindex="-1" autocomplete="off"></label></div><label class="choice"><input name="consent" type="checkbox" required> {escape(notice(brand))}</label><input type="hidden" name="notice_version" value="{VERSION}"><button>Send confirmation email</button></form><p>Check your inbox and confirm within 24 hours. This does not subscribe you to other Atmakosh products.</p><details><summary>Already subscribed? Manage or stop emails</summary><form id="manage"><label>Email address<input name="email" type="email" autocomplete="email" maxlength="254" required></label><button>Send a preference link</button></form></details>'''
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>{escape(b["name"])} email preferences</title><link rel="stylesheet" href="{PREFIX}form.css"><script src="{PREFIX}form.js" defer></script></head><body><main>{common}{body}<p id="status" role="status" aria-live="polite"></p><p id="next"></p><footer><a href="{escape(b["privacy"])}">Privacy information</a> · <a href="mailto:{b["reply_to"]}">Contact us</a><p>Atmakosh LLC · Email preferences are securely recorded in AgentVire for this product.</p></footer></main></body></html>').encode()
