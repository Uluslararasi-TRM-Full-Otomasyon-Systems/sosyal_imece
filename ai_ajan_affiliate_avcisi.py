"""Discover official affiliate programs and published API integration metadata.

The scanner only makes bounded HTTPS GET requests to its source allowlist. It
never reads credential files, requests private partner APIs, or enables live
publishing. Generated environment files are templates with live flags disabled.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


SOURCE_REGISTRY = (
    {
        "id": "trendyol_influencer",
        "name": "Trendyol Influencer Affiliate Program",
        "program_type": "affiliate",
        "official_hosts": ("influencer.trendyol.com", "developers.trendyol.com", "integration-documentation-udwy.readme.io"),
        "pages": (
            {"kind": "program", "url": "https://influencer.trendyol.com/"},
            {"kind": "marketplace_documentation", "url": "https://developers.trendyol.com/docs/getting-started"},
            {"kind": "marketplace_authentication", "url": "https://developers.trendyol.com/docs/authentication"},
        ),
        "known_application_links": [
            {"label": "Trendyol Influencer application", "url": "https://influencer.trendyol.com/forms"},
        ],
        "api_separate": {
            "docs_url": "https://developers.trendyol.com/docs",
            "kind": "marketplace_seller_api_not_affiliate_api",
            "note": "Marketplace seller integration is separate from the influencer affiliate program.",
            "documented_pages": [
                "https://developers.trendyol.com/docs/getting-started",
                "https://developers.trendyol.com/docs/authentication",
            ],
            "affiliate_api_status": "No public affiliate API endpoint identified; these are marketplace seller integration docs.",
        },
    },
    {
        "id": "magazanolsun",
        "name": "Mağazanolsun",
        "program_type": "managed_store_and_referral",
        "official_hosts": ("www.magazanolsun.com", "magazanolsun.com"),
        "pages": (
            {"kind": "program", "url": "https://www.magazanolsun.com/"},
            {"kind": "application", "url": "https://www.magazanolsun.com/paketler"},
            {"kind": "how_it_works", "url": "https://www.magazanolsun.com/nasil-calisir"},
        ),
        "api_separate": None,
    },
    {
        "id": "cj_publisher",
        "name": "CJ Publisher Network",
        "program_type": "affiliate_network",
        "official_hosts": ("developers.cj.com", "www.cj.com", "cj.com"),
        "pages": (
            {"kind": "documentation", "url": "https://developers.cj.com/"},
            {"kind": "authentication", "url": "https://developers.cj.com/authentication/overview"},
            {"kind": "product_api", "url": "https://developers.cj.com/graphql/reference/Product%20Feed"},
            {"kind": "application", "url": "https://www.cj.com/join"},
        ),
        "api_separate": None,
        "verified_metadata": {
            "api_base_urls": ["https://ads.api.cj.com/query"],
            "auth_schemes": ["Bearer personal access token"],
            "credential_creation_urls": ["https://developers.cj.com/account/personal-access-tokens"],
            "integration_parameters": ["companyId", "partnerIds", "advertiserId", "adId", "pid"],
            "evidence_urls": [
                "https://developers.cj.com/graphql/reference/Product%20Feed",
                "https://developers.cj.com/authentication/overview",
            ],
            "token_endpoint_status": "No OAuth token endpoint; personal access token is created in the logged-in developer portal.",
        },
    },
    {
        "id": "awin_publisher",
        "name": "Awin Publisher Network",
        "program_type": "affiliate_network",
        "official_hosts": ("help.awin.com", "www.awin.com", "awin.com", "ui.awin.com"),
        "pages": (
            {"kind": "documentation", "url": "https://help.awin.com/apis"},
            {"kind": "api_docs", "url": "https://help.awin.com/apidocs/introduction-1"},
            {"kind": "authentication", "url": "https://help.awin.com/apidocs/api-authentication"},
            {"kind": "link_builder", "url": "https://help.awin.com/apidocs/generatelink"},
            {"kind": "commission_details", "url": "https://help.awin.com/apidocs/get-program-information-details-for-publisher"},
            {"kind": "application", "url": "https://www.awin.com/us/publishers"},
        ),
        "api_separate": None,
        "verified_metadata": {
            "api_base_urls": ["https://api.awin.com"],
            "auth_schemes": ["OAuth 2.0 Bearer token (personal token created in Awin UI)"],
            "credential_creation_urls": ["https://ui.awin.com/awin-api"],
            "integration_parameters": ["publisherId", "advertiserId", "accessToken", "relationship"],
            "evidence_urls": [
                "https://help.awin.com/apidocs/introduction-1",
                "https://help.awin.com/apidocs/api-authentication",
                "https://help.awin.com/apidocs/generatelink",
                "https://help.awin.com/apidocs/get-program-information-details-for-publisher",
            ],
            "token_endpoint_status": "No OAuth token endpoint documented; personal API token is created in the Awin user interface.",
        },
    },
    {
        "id": "amazon_associates",
        "name": "Amazon Associates",
        "program_type": "affiliate_program",
        "official_hosts": ("affiliate-program.amazon.com", "webservices.amazon.com"),
        "pages": (
            {"kind": "application", "url": "https://affiliate-program.amazon.com/"},
            {"kind": "legacy_api_status", "url": "https://webservices.amazon.com/paapi5/documentation/"},
        ),
        "api_separate": None,
    },
)


MAX_RESPONSE_BYTES = 1_500_000
USER_AGENT = "TRM-AffiliateResearch/1.0 (+public documentation scanner)"
API_URL_RE = re.compile(r"https://[A-Za-z0-9.-]*(?:api|developer)[A-Za-z0-9.-]*(?:/[A-Za-z0-9_./%{}?=&-]*)?", re.IGNORECASE)
TOKEN_URL_RE = re.compile(r"https://[A-Za-z0-9.-]+/(?:[A-Za-z0-9_./%-]*(?:oauth|token|auth)[A-Za-z0-9_./?=%&{}-]*)", re.IGNORECASE)
AUTH_BEARER_RE = re.compile(r"authorization.{0,32}bearer|bearer.{0,32}token", re.IGNORECASE | re.DOTALL)
AUTH_BASIC_RE = re.compile(r"basic\s+auth|authorization.{0,24}basic", re.IGNORECASE)
PARTNER_PARAM_RE = re.compile(r"\b(companyId|partnerIds?|publisherId|advertiserId|adId|pid|partner_id|publisher_id)\b", re.IGNORECASE)
COMMISSION_RE = re.compile(
    r"(?:"
    r"(?:up\s+to|upto|varan|kadar)\s+(?P<rate_up_to>\d{1,3}(?:\.\d{1,2})?)\s*%"
    r"|(?P<rate_after>\d{1,3}(?:\.\d{1,2})?)\s*%\s*(?:commission|kazanç|komisyon)(?:\s+oranı)?"
    r"|%\s*(?P<rate_before>\d{1,3}(?:\.\d{1,2})?)\s*(?:kazanç|komisyon)(?:\s+oranı)?"
    r")",
    re.IGNORECASE,
)


def _host_allowed(url, allowed_hosts):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").casefold()
        return parsed.scheme == "https" and any(
            host == allowed.casefold() or host.endswith("." + allowed.casefold())
            for allowed in allowed_hosts
        ) and not parsed.username and not parsed.password
    except ValueError:
        return False


def _safe_link_text(soup, source_url, allowed_hosts):
    links = []
    for anchor in soup.find_all("a", href=True):
        target = urljoin(source_url, anchor["href"].strip())
        if not _host_allowed(target, allowed_hosts):
            continue
        label = anchor.get_text(" ", strip=True)
        lowered = label.casefold()
        if any(term in lowered for term in ("apply", "join", "sign up", "başvur", "affiliate", "partner", "publisher", "influencer", "developer", "api", "application")):
            if target not in [item["url"] for item in links]:
                links.append({"label": label[:160], "url": target})
    return links


def _commission_claims(text, source_url, network_id=None):
    claims = []
    for match in COMMISSION_RE.finditer(text):
        rate_text = match.group("rate_up_to") or match.group("rate_after") or match.group("rate_before")
        rate = float(rate_text)
        if rate > 100:
            continue
        start = max(0, match.start() - 120)
        end = min(len(text), match.end() + 120)
        excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
        around = excerpt.casefold()
        if not any(term in around for term in ("commission", "kazanç", "komisyon", "affiliate", "partner")):
            continue
        claims.append({
            "advertised_percent": rate,
            "classification": "package_earnings_claim_requires_terms_verification" if network_id == "magazanolsun" else "public_commission_claim_requires_program_terms_verification",
            "evidence_excerpt": excerpt[:360],
            "source_url": source_url,
        })
    unique = {}
    for claim in claims:
        key = (claim["advertised_percent"], claim["source_url"])
        if key not in unique or len(claim["evidence_excerpt"]) > len(unique[key]["evidence_excerpt"]):
            unique[key] = claim
    return list(unique.values())


def _json_ld_products(soup, source_url):
    products = []

    def visit(value):
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            kind = value.get("@type")
            if kind == "Product" or (isinstance(kind, list) and "Product" in kind):
                offer = value.get("offers") or {}
                products.append({
                    "name": value.get("name"),
                    "description": str(value.get("description") or "")[:500],
                    "category": value.get("category"),
                    "price": (offer.get("price") if isinstance(offer, dict) else None),
                    "currency": (offer.get("priceCurrency") if isinstance(offer, dict) else None),
                    "product_url": (offer.get("url") if isinstance(offer, dict) else None) or value.get("url"),
                    "source_url": source_url,
                    "commission_rate": None,
                })
            for child in value.values():
                if isinstance(child, (dict, list)):
                    visit(child)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            visit(json.loads(script.string or script.get_text()))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return products


class AffiliateApiScout:
    """Scan official public program/API pages and write non-secret research artifacts."""

    def __init__(self, session=None, timeout=12, sources=None):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.sources = tuple(sources or SOURCE_REGISTRY)
        self.errors = []

    def _fetch(self, url, allowed_hosts):
        if not _host_allowed(url, allowed_hosts):
            raise ValueError("Source URL is outside the HTTPS host allowlist")
        response = self.session.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=self.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        final_url = getattr(response, "url", url)
        if not _host_allowed(final_url, allowed_hosts):
            raise ValueError("Redirect left the official host allowlist")
        content = response.content
        if len(content) > MAX_RESPONSE_BYTES:
            raise ValueError("Response exceeds configured maximum size")
        return response, final_url

    @staticmethod
    def _blank_network(source):
        return {
            "id": source["id"],
            "name": source["name"],
            "program_type": source["program_type"],
            "status": "scanned",
            "sources": [],
            "application_links": [],
            "api_documentation_links": [],
            "api_base_urls": [],
            "token_endpoints": [],
            "auth_schemes": [],
            "integration_parameters": [],
            "products": [],
            "metadata_evidence": [],
            "credential_creation_urls": [],
            "token_endpoint_status": None,
            "commission_claims": [],
            "official_api_separation": source.get("api_separate"),
            "commission_route_candidates": [],
            "warnings": [],
        }

    def scan_network(self, source):
        result = self._blank_network(source)
        hosts = source["official_hosts"]
        full_texts = []
        api_urls = set()
        token_urls = set()
        auth_schemes = set()
        parameters = set()
        application_links = {}
        documentation_links = {}
        commission_claims = []
        products = []
        successful_pages = 0

        for link in source.get("known_application_links", []):
            if _host_allowed(link.get("url", ""), hosts):
                application_links[link["url"]] = link

        for page in source["pages"]:
            page_record = {"kind": page["kind"], "url": page["url"], "status": "ok"}
            if page["kind"] == "application" and _host_allowed(page["url"], hosts):
                application_links[page["url"]] = {"label": f"Official {source['name']} application", "url": page["url"]}
            if page["kind"] in {"documentation", "api_docs", "product_api", "authentication", "link_builder", "commission_details", "marketplace_documentation", "marketplace_authentication"} and _host_allowed(page["url"], hosts):
                documentation_links[page["url"]] = {"label": f"Official {source['name']} {page['kind']}", "url": page["url"]}
            try:
                response, final_url = self._fetch(page["url"], hosts)
                soup = BeautifulSoup(response.content, "html.parser")
                text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
                full_texts.append(text)
                page_record["url"] = final_url
                page_record["title"] = (soup.title.get_text(" ", strip=True) if soup.title else "")[:200]
                page_record["links_found"] = len(soup.find_all("a", href=True))
                page_token_urls = {
                    candidate.rstrip(".,);]")
                    for candidate in TOKEN_URL_RE.findall(text)
                    if _host_allowed(candidate.rstrip(".,);]"), hosts)
                }
                token_urls.update(page_token_urls)
                for candidate in API_URL_RE.findall(text):
                    cleaned_candidate = candidate.rstrip(".,);]")
                    host = (urlsplit(cleaned_candidate).hostname or "").casefold()
                    host_parts = host.split(".")
                    has_api_host_label = "api" in host_parts
                    if (
                        _host_allowed(cleaned_candidate, hosts)
                        and cleaned_candidate not in page_token_urls
                        and has_api_host_label
                        and not host.startswith("developers.")
                    ):
                        api_urls.add(cleaned_candidate)
                if AUTH_BEARER_RE.search(text):
                    auth_schemes.add("Bearer personal/access token (documented)")
                if AUTH_BASIC_RE.search(text):
                    auth_schemes.add("HTTP Basic (documented)")
                parameters.update(match.group(1) for match in PARTNER_PARAM_RE.finditer(text))
                links = _safe_link_text(soup, final_url, hosts)
                for link in links:
                    lowered = link["label"].casefold()
                    if any(term in lowered for term in ("apply", "join", "sign up", "başvur", "application")):
                        application_links[link["url"]] = link
                    if any(term in lowered for term in ("developer", "api", "documentation", "docs")):
                        documentation_links[link["url"]] = link
                commission_claims.extend(_commission_claims(text, final_url, source["id"]))
                products.extend(_json_ld_products(soup, final_url))
                successful_pages += 1
            except (requests.RequestException, OSError, ValueError) as exc:
                self.errors.append({"network_id": source["id"], "url": page["url"], "error": f"{exc.__class__.__name__}: {exc}"})
                page_record["status"] = "error"
                page_record["error"] = f"{exc.__class__.__name__}: {exc}"
                result["status"] = "partial" if successful_pages else "error"
            except Exception as exc:
                logger.exception("Affiliate source parser failed: %s", source["id"])
                self.errors.append({"network_id": source["id"], "url": page["url"], "error": f"{exc.__class__.__name__}: {exc}"})
                page_record["status"] = "error"
                page_record["error"] = f"{exc.__class__.__name__}: {exc}"
                result["status"] = "partial" if successful_pages else "error"
            result["sources"].append(page_record)

        combined_text = " ".join(full_texts)
        # CJ documents its exact GraphQL URL and bearer scheme in request examples.
        if source["id"] == "cj_publisher":
            documented_endpoint = "https://ads.api.cj.com/query"
            if documented_endpoint in combined_text:
                api_urls.add(documented_endpoint)
            if "Authorization: Bearer" in combined_text:
                auth_schemes.add("Bearer personal access token (documented)")

        verified = source.get("verified_metadata", {})
        api_urls.update(verified.get("api_base_urls", []))
        auth_schemes.update(verified.get("auth_schemes", []))
        parameters.update(verified.get("integration_parameters", []))
        if source["id"] == "amazon_associates" and any("deprecation" in text.casefold() for text in full_texts):
            result["warnings"].append("Legacy Product Advertising API documentation indicates deprecation; verify current Creators API status before integration.")
        if source["id"] == "trendyol_influencer":
            result["warnings"].append("Affiliate application page is separate from Trendyol Marketplace seller API docs; no public affiliate API endpoint was established by this scan.")
        if source["id"] == "magazanolsun" and not api_urls:
            result["warnings"].append("Public pages exposed application/package details but no official API base URL or token endpoint.")
        if not commission_claims:
            result["warnings"].append("No public commission percentage verified; rates can be account-, advertiser-, category-, or campaign-specific.")

        result["application_links"] = sorted(application_links.values(), key=lambda item: item["url"])
        result["api_documentation_links"] = sorted(documentation_links.values(), key=lambda item: item["url"])
        result["api_base_urls"] = sorted(api_urls)
        result["token_endpoints"] = sorted(token_urls)
        result["auth_schemes"] = sorted(auth_schemes)
        result["integration_parameters"] = sorted(parameters)
        result["commission_claims"] = commission_claims
        result["commission_route_candidates"] = sorted(
            [claim for claim in commission_claims if "commission_claim" in claim["classification"]],
            key=lambda claim: claim["advertised_percent"],
            reverse=True,
        )
        unique_products = {}
        for product in products:
            key = (product.get("name"), product.get("product_url"))
            unique_products[key] = product
        result["products"] = list(unique_products.values())
        result["metadata_evidence"] = verified.get("evidence_urls", [])
        result["credential_creation_urls"] = verified.get("credential_creation_urls", [])
        result["token_endpoint_status"] = verified.get("token_endpoint_status")
        if result["status"] not in {"error", "partial"} and not result["commission_claims"]:
            result["status"] = "scanned_no_public_rate"
        return result

    def scan_all(self):
        self.errors = []
        networks = [self.scan_network(source) for source in self.sources]
        local_partners = self._load_local_partner_metadata()
        route_candidates = sorted(
            [
                {"network_id": network["id"], **claim}
                for network in networks
                for claim in network["commission_route_candidates"]
            ],
            key=lambda item: item["advertised_percent"],
            reverse=True,
        )
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent": "AffiliateApiScout",
            "live_configuration_enabled": False,
            "secrets_read": False,
            "networks": networks,
            "local_partner_metadata": local_partners,
            "highest_public_commission_claims": route_candidates,
            "errors": list(self.errors),
            "safety": {
                "live_flags_modified": False,
                "secret_values_written": False,
                "api_endpoints_inferred_without_evidence": False,
                "commission_claims_are_not_payout_guarantees": True,
            },
        }

    @staticmethod
    def _load_local_partner_metadata():
        path = Path(__file__).resolve().with_name("affiliate_partners.json")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        partners = data.get("recruited_partners", []) if isinstance(data, dict) else []
        return [
            {
                "partner_id": str(item.get("partner_id", "")),
                "firm_name": str(item.get("firm_name", "")),
                "market_type": str(item.get("market_type", "")),
                "status": str(item.get("status", "")),
                "api_credentials_configured": False,
            }
            for item in partners
            if isinstance(item, dict)
        ]

    @staticmethod
    def render_env_template(report):
        lines = [
            "# Generated by ai_ajan_affiliate_avcisi.py; template only, not production credentials.",
            "# Review official program terms and enter credentials locally after approval.",
            "TRM_AFFILIATE_SCOUT_ENABLED=0",
            "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED=0",
            "TRM_MAGAZA_API_ENABLED=0",
            "TRM_STORE_SIMULATE=1",
            "TRM_DISTRIBUTION_MODE=simulate",
            "TRM_STORE_API_BASE_URL=",
            "TRM_STORE_TOKEN_URL=",
            "TRM_STORE_CLIENT_ID=",
            "TRM_STORE_CLIENT_SECRET=",
            "TRM_STORE_ACCESS_TOKEN=",
            "TELEGRAM_BOT_TOKEN=",
            "TELEGRAM_CHAT_ID=",
            "TRM_SOCIAL_DISTRIBUTION_WEBHOOK_URL=",
            "TRM_EXTERNAL_API_WEBHOOK_URL=",
            "",
            "# Network-specific public metadata. These are not TRM_STORE_API_* settings.",
        ]
        for network in report.get("networks", []):
            lines.append(f"# {network['name']}: {network['id']}")
            separate = network.get("official_api_separation")
            if separate:
                lines.append(f"# Separate API scope: {separate.get('kind', 'not specified')}")
                lines.append(f"# API scope note: {separate.get('note', '')}")
                for doc_url in separate.get("documented_pages", []):
                    lines.append(f"# Official separate API docs: {doc_url}")
            for endpoint in network.get("api_base_urls", []):
                lines.append(f"# Documented API URL: {endpoint}")
            if network.get("auth_schemes"):
                lines.append("# Auth: " + "; ".join(network["auth_schemes"]))
            if network.get("integration_parameters"):
                lines.append("# Account-specific parameters: " + ", ".join(network["integration_parameters"]))
            for url in network.get("credential_creation_urls", []):
                lines.append(f"# Credential management: {url}")
            for url in network.get("metadata_evidence", []):
                lines.append(f"# Metadata evidence: {url}")
            if network.get("token_endpoints"):
                for endpoint in network["token_endpoints"]:
                    lines.append(f"# Documented token endpoint: {endpoint}")
            else:
                lines.append("# Token endpoint: not publicly established; request official partner docs.")
            lines.append("# Partner/company IDs and personal access tokens are account-specific; not auto-filled.")
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_integration_guide(report):
        networks = {item.get("id"): item for item in report.get("networks", [])}
        trendyol = networks.get("trendyol_influencer", {})
        magazanolsun = networks.get("magazanolsun", {})
        lines = [
            "# Affiliate and API Integration Setup",
            "",
            "Generated from official public pages. This guide does not contain credentials and does not activate live mode.",
            "",
            "## Current Findings",
            "",
            f"- Mağazanolsun public API base URLs found: {', '.join(magazanolsun.get('api_base_urls', [])) or 'none'}.",
            f"- Mağazanolsun public token endpoints found: {', '.join(magazanolsun.get('token_endpoints', [])) or 'none'}.",
            f"- Trendyol Influencer affiliate API base URLs found: {', '.join(trendyol.get('api_base_urls', [])) or 'none'}.",
            f"- Trendyol Influencer token endpoints found: {', '.join(trendyol.get('token_endpoints', [])) or 'none'}.",
            "- A zero-result API field means the official public scan found no such integration detail; no URL or auth flow has been guessed.",
            "",
            "## Mağazanolsun",
            "",
            "1. Apply through the official store/application route:",
            "   https://www.magazanolsun.com/Magaza",
            "2. Request partner-only API documentation for the exact program/account. Ask for production and sandbox API base URLs; supported product/order/link endpoints; authentication method; token endpoint if OAuth is used; required scopes; partner/store ID format; rate limits; webhook format; and the current signed affiliate/commission terms.",
            "3. Ask whether the integration is an affiliate/referral API or a store-owner/seller API. They are different products and need different credentials.",
            "4. Do not use the generic `/v1/oauth/token` or `/v1/products` defaults in `magaza_api_koprusu.py` until Mağazanolsun confirms those exact URLs and request schema in writing.",
            "",
            "## Trendyol",
            "",
            "1. Apply to the official Influencer Affiliate Program:",
            "   https://influencer.trendyol.com/forms",
            "2. Request the affiliate link/deep-link API specification, partner/publisher ID, approved token or key flow, scopes, commission schedule by category, and payout/return attribution terms from the program after account approval. The public scan did not find an affiliate API endpoint or token endpoint.",
            "3. Trendyol Marketplace seller integration docs are separate from the influencer affiliate program:",
            "   https://developers.trendyol.com/docs/getting-started",
            "   https://developers.trendyol.com/docs/authentication",
            "Use seller API credentials only for an approved seller account; do not map them into the affiliate flow.",
            "",
            "## Local Configuration Gate",
            "",
            "The project loader uses the root `secrets.env` when `.env` is not a regular file. Keep actual values local; do not paste them into chat, reports, or generated artifacts.",
            "Set the following only after receiving the exact values and API contract from the provider:",
            "",
            "```dotenv",
            "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED=0",
            "TRM_MAGAZA_API_ENABLED=0",
            "TRM_STORE_SIMULATE=1",
            "TRM_DISTRIBUTION_MODE=simulate",
            "TRM_STORE_API_BASE_URL=",
            "TRM_STORE_TOKEN_URL=",
            "TRM_STORE_CLIENT_ID=",
            "TRM_STORE_CLIENT_SECRET=",
            "TRM_STORE_ACCESS_TOKEN=",
            "```",
            "",
            "After verifying a documented HTTPS endpoint, approved account ID, valid token, and affiliate link attribution, fill the matching values locally and enable live flags as a separate deployment change. Run `python trm_live_config.py`; proceed only when `live_production_ready` is true.",
            "",
            "Commission rates discovered in public marketing material are claims, not guaranteed payout rates. Verify the current account-specific terms before using them to rank campaigns.",
            "",
        ]
        return "\n".join(lines)

    def scan_and_write(self, output_dir=None):
        output_path = Path(output_dir) if output_dir else Path(__file__).resolve().parent / "affiliate_scout_output"
        output_path.mkdir(parents=True, exist_ok=True)
        report = self.scan_all()
        report_path = output_path / "affiliate_api_research.json"
        template_path = output_path / "affiliate_secrets.env.example"
        guide_path = output_path / "affiliate_integration_setup.md"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        template_path.write_text(self.render_env_template(report), encoding="utf-8")
        guide_path.write_text(self.render_integration_guide(report), encoding="utf-8")
        report["artifacts"] = {
            "report": str(report_path),
            "safe_template": str(template_path),
            "integration_guide": str(guide_path),
        }
        return report


def run_affiliate_api_scout(output_dir=None, session=None, sources=None):
    return AffiliateApiScout(session=session, sources=sources).scan_and_write(output_dir)


def main():
    report = run_affiliate_api_scout()
    safe_summary = {
        "network_count": len(report["networks"]),
        "scanned": sum(network["status"] != "error" for network in report["networks"]),
        "public_commission_claim_count": len(report["highest_public_commission_claims"]),
        "api_metadata_found": sum(bool(network["api_base_urls"]) for network in report["networks"]),
        "errors": report["errors"],
        "artifacts": report["artifacts"],
        "live_flags_modified": report["safety"]["live_flags_modified"],
        "secrets_read": report["secrets_read"],
    }
    print(json.dumps(safe_summary, ensure_ascii=False, indent=2))
    return 0 if report["networks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
