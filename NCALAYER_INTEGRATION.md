# NCALayer integration

Date: 2026-06-01

## Official path

For Kazakhstan EDS signing from a web app, use NCALayer on the user's computer. The web app connects from the browser to local NCALayer over WebSocket:

```text
wss://127.0.0.1:13579/
```

This is safer than uploading `.p12` and password to the Flask server. The private key stays on the user's device and NCALayer asks the user to choose/authorize the key.

Official sources:

- https://pki.gov.kz/ru/ncalayer/
- https://pki.gov.kz/docs/ncalayer/
- https://pki.gov.kz/docs/ncalayer/ncalayer/

## Current implementation

Added in `templates/invoice_view.html`:

- Button: `Подписать XML через NCALayer`.
- Browser JS fetches XML from `/esf/xml/<invoice_id>`.
- Browser sends it to NCALayer:

```json
{
  "module": "kz.gov.pki.knca.commonUtils",
  "method": "signXml",
  "args": ["PKCS12", "SIGNATURE", "<xml>", "", ""]
}
```

- The signed XML is downloaded as `SIGNED_ESF_<number>_<date>.xml`.

Added in `app.py`:

- `build_esf_xml(invoice)` - shared XML builder.
- `/esf/xml/<id>` - returns generated ESF XML as JSON for browser signing.
- `/esf/export/<id>` now uses the shared builder.

## Next checks

1. Install/start NCALayer on the user's Windows machine.
2. Open an invoice in the app.
3. Click `Подписать XML через NCALayer`.
4. Select the EDS key in NCALayer.
5. Verify downloaded signed XML.
6. Only after this, connect real ESF test-contour sending.

## Not done yet

Real ESF submission is intentionally not enabled as a trusted production flow. The existing SOAP client is a prototype and must be verified against the official ESF test contour before sending real documents.
