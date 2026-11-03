"""Optional, read-only Tally Prime XML export adapter for BillSync.

Does not modify BillSync's existing master creation / XML voucher process.
Requires a running Tally instance with its XML HTTP server enabled.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

KINDS = {
    "ledgers": "Ledger",
    "groups": "Group",
    "stock_items": "StockItem",
    "stock_groups": "StockGroup",
    "stock_categories": "StockCategory",
    "units": "Unit",
}

class TallyConnectionError(RuntimeError):
    pass


def _request_xml(url: str, request: str, timeout: int = 12) -> ET.Element:
    if not (url.startswith('http://127.0.0.1:') or url.startswith('http://localhost:')):
        raise ValueError('This read-only adapter only accepts local Tally HTTP endpoints.')
    req = urllib.request.Request(url, data=request.encode('utf-8'), headers={'Content-Type':'application/xml'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(20_000_000)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TallyConnectionError(f'Could not reach Tally at {url}: {exc}') from exc
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise TallyConnectionError('Tally did not return valid XML') from exc


def _request(collection: str, company: str | None = None) -> str:
    company_xml = f'<SVCURRENTCOMPANY>{_xml_escape(company)}</SVCURRENTCOMPANY>' if company else ''
    return (f'<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>'
            f'<TYPE>Collection</TYPE><ID>{collection}</ID></HEADER><BODY><DESC><STATICVARIABLES>'
            f'<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>{company_xml}'
            f'</STATICVARIABLES></DESC></BODY></ENVELOPE>')


def _xml_escape(value: str) -> str:
    return (value.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            .replace('"','&quot;').replace("'",'&apos;'))


def test_connection(url='http://127.0.0.1:9000', company=None) -> dict:
    root = _request_xml(url, _request('List of Companies', company))
    error = root.findtext('.//LINEERROR')
    if error:
        raise TallyConnectionError(error)
    return {'reachable': True, 'root_tag': root.tag, 'url': url,
            'note': 'Connection only; does not prove a particular master collection is available.'}


def import_masters_and_units(url='http://127.0.0.1:9000', company=None, *, destination: str | Path):
    """Export collection snapshots only; no Tally creation and no existing BillSync overwrite.

    Tally versions vary in collection support. A missing/empty collection is
    explicitly reported; it must not be interpreted as proof there are no masters.
    """
    target = Path(destination)
    if target.exists():
        raise FileExistsError(f'Refusing to overwrite snapshot: {target}')
    snapshots = {}
    issues = []
    for kind, tally_type in KINDS.items():
        # Built-in 'List of ...' collections are available in common Tally releases.
        # Verify each collection in user's installed edition before claiming completeness.
        collection = {
            'ledgers':'List of Ledgers', 'groups':'List of Groups',
            'stock_items':'List of Stock Items','stock_groups':'List of Stock Groups',
            'stock_categories':'List of Stock Categories','units':'List of Units',
        }[kind]
        try:
            root = _request_xml(url, _request(collection, company))
            error = root.findtext('.//LINEERROR')
            if error:
                raise TallyConnectionError(error)
            matches = []
            for node in root.iter():
                tag = node.tag.upper().split('}')[-1]
                if tag in {tally_type.upper(), tally_type.upper().replace('ITEM', ' ITEM')}:
                    matches.append(ET.tostring(node, encoding='unicode'))
            if not matches:
                issues.append(f'{kind}: no matching elements returned; verify collection in Tally')
            snapshots[kind] = {'collection':collection,'count':len(matches), 'raw_master_xml':matches}
        except TallyConnectionError as exc:
            snapshots[kind] = {'collection':collection, 'error':str(exc)}
            issues.append(f'{kind}: {exc}')
    payload = {'company_requested':company, 'exported_at_utc':datetime.now(timezone.utc).isoformat(),
               'source_url':url, 'mode':'READ_ONLY_UNVERIFIED', 'snapshots':snapshots,
               'issues':issues, 'note':'Separate storage only; not used to create/import masters or XML.'}
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload
