"""Keep strategy decisions and cost evidence separate from a processor refresh."""
import copy
from .core import Invalid

PRESERVE = ('statement_cost_evidence','statement_cost_evidence_sha256','provisional_margin_run','commercial_pricing_plan')

def merge_actual_finance(existing,observed):
    if not isinstance(existing,dict) or not isinstance(observed,dict):
        raise Invalid('Finance snapshots must be objects')
    if any(k in observed for k in PRESERVE):
        raise Invalid('A processor refresh cannot replace strategy or statement evidence')
    if len(observed.get('product_status',[]))!=17 or not observed.get('captured_at'):
        raise Invalid('Complete product-status envelope required')
    result=copy.deepcopy(observed)
    for key in PRESERVE:
        if key in existing:result[key]=copy.deepcopy(existing[key])
    return result
