#!/usr/bin/env python3
"""Smoke-test all app-defined HTTP APIs with one email/password pair."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import date, timedelta
from typing import Any
from urllib import error, parse, request


AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://127.0.0.1:8000")
TRANSACTION_BASE_URL = os.getenv("TRANSACTION_BASE_URL", "http://127.0.0.1:8002")
BUDGET_BASE_URL = os.getenv("BUDGET_BASE_URL", "http://127.0.0.1:8081")
REPORT_BASE_URL = os.getenv("REPORT_BASE_URL", "http://127.0.0.1:8003")
TIMEOUT_SECONDS = float(os.getenv("API_SMOKE_TIMEOUT", "10"))


class SmokeClient:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def request(
        self,
        name: str,
        method: str,
        base_url: str,
        path: str,
        *,
        token: str | None = None,
        json_body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        expected: set[int] | None = None,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> dict[str, Any] | None:
        expected = expected or {200}
        url = base_url.rstrip("/") + path
        if query:
            clean_query = {key: value for key, value in query.items() if value is not None}
            url += "?" + parse.urlencode(clean_query)

        req_headers = {"Accept": "application/json"}
        if token:
            req_headers["Authorization"] = f"Bearer {token}"
        if headers:
            req_headers.update(headers)

        data = body
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = request.Request(url, data=data, headers=req_headers, method=method)
        started_at = time.monotonic()
        status_code = 0
        response_body = ""
        parsed_body: dict[str, Any] | None = None

        try:
            with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                status_code = response.status
                response_body = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            status_code = exc.code
            response_body = exc.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - this is a diagnostic script.
            response_body = str(exc)

        elapsed_ms = round((time.monotonic() - started_at) * 1000)
        try:
            parsed = json.loads(response_body) if response_body else None
            parsed_body = parsed if isinstance(parsed, dict) else {"data": parsed}
        except json.JSONDecodeError:
            parsed_body = None

        ok = status_code in expected
        self.results.append(
            {
                "ok": ok,
                "name": name,
                "method": method,
                "path": path,
                "url": url,
                "status": status_code,
                "expected": sorted(expected),
                "elapsed_ms": elapsed_ms,
                "body": parsed_body if parsed_body is not None else response_body[:500],
            }
        )

        icon = "PASS" if ok else "FAIL"
        print(f"{icon} {method:<6} {name:<42} {status_code:<3} {elapsed_ms:>5}ms")
        if not ok:
            print(f"     URL: {url}")
            print(f"     Expected: {sorted(expected)}")
            print(f"     Body: {response_body[:500]}")

        return parsed_body

    def summary(self) -> int:
        passed = sum(1 for result in self.results if result["ok"])
        total = len(self.results)
        failed = total - passed
        print()
        print("API Report:")
        print(f"{'Works':<7} {'Method':<6} {'API':<60} Name")
        print("-" * 95)
        for result in self.results:
            works = "true" if result["ok"] else "false"
            print(f"{works:<7} {result['method']:<6} {result['path']:<60} {result['name']}")
        print()
        print(f"Summary: {passed}/{total} passed, {failed} failed")
        return 0 if failed == 0 else 1


def data_id(response: dict[str, Any] | None) -> str | None:
    if not response:
        return None
    data = response.get("data")
    if isinstance(data, dict):
        value = data.get("id")
        return str(value) if value else None
    return None


def auth_tokens(response: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if not response:
        return None, None
    tokens = response.get("tokens")
    if not isinstance(tokens, dict):
        data = response.get("data")
        tokens = data.get("tokens") if isinstance(data, dict) else None
    if not isinstance(tokens, dict):
        return None, None
    return tokens.get("access"), tokens.get("refresh")


def multipart_file(field: str, filename: str, content: bytes, content_type: str) -> tuple[bytes, str]:
    boundary = f"----api-smoke-{uuid.uuid4().hex}"
    lines = [
        f"--{boundary}\r\n".encode(),
        (
            f'Content-Disposition: form-data; name="{field}"; '
            f'filename="{filename}"\r\n'
        ).encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        content,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(lines), f"multipart/form-data; boundary={boundary}"


def run(args: argparse.Namespace) -> int:
    client = SmokeClient()
    suffix = uuid.uuid4().hex[:8]
    today = date.today()
    next_month = today + timedelta(days=30)

    register_body = {
        "email": args.email,
        "username": args.email.split("@", 1)[0][:80] + "_" + suffix,
        "password": args.password,
        "first_name": "Smoke",
        "last_name": "Tester",
    }
    client.request(
        "auth register",
        "POST",
        args.auth_url,
        "/auth/register",
        json_body=register_body,
        expected={201, 400},
    )

    login = client.request(
        "auth login",
        "POST",
        args.auth_url,
        "/auth/login",
        json_body={"email": args.email, "password": args.password},
        expected={200},
    )
    access_token, refresh_token = auth_tokens(login)
    if not access_token:
        print("Cannot continue without an access token from /auth/login.")
        return client.summary() or 1

    if refresh_token:
        refresh = client.request(
            "auth refresh",
            "POST",
            args.auth_url,
            "/auth/refresh",
            json_body={"refresh": refresh_token},
            expected={200},
        )
        refreshed_access, refreshed_refresh = auth_tokens(refresh)
        access_token = refreshed_access or access_token
        refresh_token = refreshed_refresh or refresh_token

    client.request("auth me", "GET", args.auth_url, "/auth/me", token=access_token)
    client.request(
        "auth update me",
        "PATCH",
        args.auth_url,
        "/auth/me",
        token=access_token,
        json_body={
            "first_name": "Smoke",
            "last_name": "Tester",
            "profile": {
                "phone": "+8801000000000",
                "country": "Bangladesh",
                "currency_code": "BDT",
                "timezone": "Asia/Dhaka",
            },
        },
    )

    client.request("transaction health", "GET", args.transaction_url, "/health")
    client.request("transaction db health", "GET", args.transaction_url, "/health/db")
    client.request("transaction storage health", "GET", args.transaction_url, "/health/storage")
    client.request("transaction hello", "GET", args.transaction_url, "/hello", token=access_token)

    wallet = client.request(
        "create wallet",
        "POST",
        args.transaction_url,
        "/api/wallets",
        token=access_token,
        json_body={
            "name": f"Smoke Cash {suffix}",
            "type": "CASH",
            "currency_code": "BDT",
            "opening_balance": "10000.00",
            "is_default": False,
        },
        expected={201},
    )
    wallet_id = data_id(wallet)
    client.request("list wallets", "GET", args.transaction_url, "/api/wallets", token=access_token)
    if wallet_id:
        client.request("get wallet", "GET", args.transaction_url, f"/api/wallets/{wallet_id}", token=access_token)
        client.request(
            "update wallet",
            "PATCH",
            args.transaction_url,
            f"/api/wallets/{wallet_id}",
            token=access_token,
            json_body={"name": f"Smoke Cash Updated {suffix}", "is_active": True},
        )

    category = client.request(
        "create category",
        "POST",
        args.transaction_url,
        "/api/categories",
        token=access_token,
        json_body={
            "name": f"Smoke Food {suffix}",
            "type": "EXPENSE",
            "icon": "receipt",
            "color": "#2f80ed",
        },
        expected={201},
    )
    category_id = data_id(category)
    client.request("list categories", "GET", args.transaction_url, "/api/categories", token=access_token)
    if category_id:
        client.request("get category", "GET", args.transaction_url, f"/api/categories/{category_id}", token=access_token)
        client.request(
            "update category",
            "PATCH",
            args.transaction_url,
            f"/api/categories/{category_id}",
            token=access_token,
            json_body={"name": f"Smoke Food Updated {suffix}", "color": "#27ae60"},
        )

    payment_method = client.request(
        "create payment method",
        "POST",
        args.transaction_url,
        "/api/payment-methods",
        token=access_token,
        json_body={"name": f"Smoke Cash PM {suffix}", "type": "CASH"},
        expected={201},
    )
    payment_method_id = data_id(payment_method)
    client.request("list payment methods", "GET", args.transaction_url, "/api/payment-methods", token=access_token)
    if payment_method_id:
        client.request(
            "update payment method",
            "PATCH",
            args.transaction_url,
            f"/api/payment-methods/{payment_method_id}",
            token=access_token,
            json_body={"name": f"Smoke Cash PM Updated {suffix}"},
        )

    tag = client.request(
        "create tag",
        "POST",
        args.transaction_url,
        "/api/tags",
        token=access_token,
        json_body={"name": f"smoke-{suffix}"},
        expected={201},
    )
    tag_id = data_id(tag)
    client.request("list tags", "GET", args.transaction_url, "/api/tags", token=access_token)

    transaction_id = None
    if wallet_id and category_id and payment_method_id:
        transaction = client.request(
            "create transaction",
            "POST",
            args.transaction_url,
            "/api/transactions",
            token=access_token,
            json_body={
                "wallet_id": wallet_id,
                "category_id": category_id,
                "payment_method_id": payment_method_id,
                "type": "EXPENSE",
                "amount": "125.50",
                "currency_code": "BDT",
                "title": f"Smoke transaction {suffix}",
                "description": "Created by api_smoke_test.py",
                "transaction_date": today.isoformat(),
                "tags": [f"smoke-{suffix}"],
            },
            expected={201},
        )
        transaction_id = data_id(transaction)

    client.request("list transactions", "GET", args.transaction_url, "/api/transactions", token=access_token)
    client.request(
        "monthly summary",
        "GET",
        args.transaction_url,
        "/api/transactions/summary/monthly",
        token=access_token,
        query={"year": today.year, "month": today.month},
    )
    client.request(
        "yearly summary",
        "GET",
        args.transaction_url,
        "/api/transactions/summary/yearly",
        token=access_token,
        query={"year": today.year},
    )
    client.request(
        "category-wise summary",
        "GET",
        args.transaction_url,
        "/api/transactions/summary/category-wise",
        token=access_token,
        query={"year": today.year, "month": today.month, "type": "EXPENSE"},
    )
    client.request(
        "wallet-wise summary",
        "GET",
        args.transaction_url,
        "/api/transactions/summary/wallet-wise",
        token=access_token,
        query={"year": today.year, "month": today.month},
    )

    attachment_id = None
    if transaction_id:
        client.request(
            "get transaction",
            "GET",
            args.transaction_url,
            f"/api/transactions/{transaction_id}",
            token=access_token,
        )
        client.request(
            "update transaction",
            "PATCH",
            args.transaction_url,
            f"/api/transactions/{transaction_id}",
            token=access_token,
            json_body={
                "amount": "130.75",
                "title": f"Smoke transaction updated {suffix}",
                "transaction_date": today.isoformat(),
                "tags": [f"smoke-{suffix}", "smoke-updated"],
            },
        )
        multipart_body, content_type = multipart_file(
            "file",
            f"smoke-{suffix}.txt",
            b"smoke test attachment\n",
            "text/plain",
        )
        attachment = client.request(
            "upload attachment",
            "POST",
            args.transaction_url,
            f"/api/transactions/{transaction_id}/attachments",
            token=access_token,
            body=multipart_body,
            headers={"Content-Type": content_type},
            expected={201},
        )
        attachment_id = data_id(attachment)
        client.request(
            "list attachments",
            "GET",
            args.transaction_url,
            f"/api/transactions/{transaction_id}/attachments",
            token=access_token,
        )

    recurring_id = None
    if wallet_id and category_id:
        recurring = client.request(
            "create recurring transaction",
            "POST",
            args.transaction_url,
            "/api/recurring-transactions",
            token=access_token,
            json_body={
                "wallet_id": wallet_id,
                "category_id": category_id,
                "type": "EXPENSE",
                "amount": "500.00",
                "currency_code": "BDT",
                "title": f"Smoke recurring {suffix}",
                "description": "Created by api_smoke_test.py",
                "frequency": "MONTHLY",
                "start_date": today.isoformat(),
                "end_date": next_month.isoformat(),
                "next_run_date": next_month.isoformat(),
                "is_active": True,
            },
            expected={201},
        )
        recurring_id = data_id(recurring)
    client.request(
        "list recurring transactions",
        "GET",
        args.transaction_url,
        "/api/recurring-transactions",
        token=access_token,
    )
    if recurring_id:
        client.request(
            "update recurring transaction",
            "PATCH",
            args.transaction_url,
            f"/api/recurring-transactions/{recurring_id}",
            token=access_token,
            json_body={"title": f"Smoke recurring updated {suffix}", "amount": "550.00"},
        )

    if attachment_id and transaction_id:
        client.request(
            "delete attachment",
            "DELETE",
            args.transaction_url,
            f"/api/transactions/{transaction_id}/attachments/{attachment_id}",
            token=access_token,
        )
    if recurring_id:
        client.request(
            "delete recurring transaction",
            "DELETE",
            args.transaction_url,
            f"/api/recurring-transactions/{recurring_id}",
            token=access_token,
        )
    if transaction_id:
        client.request(
            "delete transaction",
            "DELETE",
            args.transaction_url,
            f"/api/transactions/{transaction_id}",
            token=access_token,
        )
    if tag_id:
        client.request("delete tag", "DELETE", args.transaction_url, f"/api/tags/{tag_id}", token=access_token)
    if payment_method_id:
        client.request(
            "delete payment method",
            "DELETE",
            args.transaction_url,
            f"/api/payment-methods/{payment_method_id}",
            token=access_token,
        )
    if category_id:
        client.request("delete category", "DELETE", args.transaction_url, f"/api/categories/{category_id}", token=access_token)
    if wallet_id:
        client.request("delete wallet", "DELETE", args.transaction_url, f"/api/wallets/{wallet_id}", token=access_token)

    client.request("budget health", "GET", args.budget_url, "/health")
    client.request("budget hello", "GET", args.budget_url, "/hello", token=access_token)

    smoke_budget_year = 3000 + int(suffix[:3], 16) % 5000
    smoke_budget_month = int(suffix[3:5], 16) % 12 + 1
    budget = client.request(
        "create budget",
        "POST",
        args.budget_url,
        "/api/budgets",
        token=access_token,
        json_body={
            "name": f"Smoke Budget {suffix}",
            "year": smoke_budget_year,
            "month": smoke_budget_month,
            "total_budget_amount": 50000,
            "currency_code": "BDT",
        },
        expected={201},
    )
    budget_id = data_id(budget)
    client.request(
        "list budgets",
        "GET",
        args.budget_url,
        "/api/budgets",
        token=access_token,
        query={"page": 1, "page_size": 20, "year": smoke_budget_year, "month": smoke_budget_month, "status": "ACTIVE"},
    )

    budget_category_id = None
    alert_rule_id = None
    if budget_id:
        client.request("get budget", "GET", args.budget_url, f"/api/budgets/{budget_id}", token=access_token)
        client.request(
            "update budget",
            "PATCH",
            args.budget_url,
            f"/api/budgets/{budget_id}",
            token=access_token,
            json_body={"name": f"Smoke Budget Updated {suffix}", "total_budget_amount": 55000, "status": "ACTIVE"},
        )

        budget_category = client.request(
            "create budget category",
            "POST",
            args.budget_url,
            f"/api/budgets/{budget_id}/categories",
            token=access_token,
            json_body={
                "category_id": str(uuid.uuid4()),
                "category_name_snapshot": "Smoke Food",
                "budget_amount": 12000,
                "alert_threshold_percentage": 80,
            },
            expected={201},
        )
        budget_category_id = data_id(budget_category)
        client.request(
            "list budget categories",
            "GET",
            args.budget_url,
            f"/api/budgets/{budget_id}/categories",
            token=access_token,
        )
        if budget_category_id:
            client.request(
                "update budget category",
                "PATCH",
                args.budget_url,
                f"/api/budgets/{budget_id}/categories/{budget_category_id}",
                token=access_token,
                json_body={
                    "category_name_snapshot": "Smoke Food Updated",
                    "budget_amount": 15000,
                    "alert_threshold_percentage": 85,
                },
            )

        alert_rule = client.request(
            "create alert rule",
            "POST",
            args.budget_url,
            f"/api/budgets/{budget_id}/alert-rules",
            token=access_token,
            json_body={"rule_type": "PERCENTAGE_USED", "threshold_percentage": 80, "is_enabled": True},
            expected={201},
        )
        alert_rule_id = data_id(alert_rule)
        client.request(
            "list alert rules",
            "GET",
            args.budget_url,
            f"/api/budgets/{budget_id}/alert-rules",
            token=access_token,
        )
        if alert_rule_id:
            client.request(
                "update alert rule",
                "PATCH",
                args.budget_url,
                f"/api/budgets/{budget_id}/alert-rules/{alert_rule_id}",
                token=access_token,
                json_body={"threshold_percentage": 85, "is_enabled": True},
            )

        client.request(
            "monthly budget status",
            "GET",
            args.budget_url,
            "/api/budgets/status/monthly",
            token=access_token,
            query={"year": smoke_budget_year, "month": smoke_budget_month},
            expected={200, 502},
        )
        client.request(
            "category-wise budget status",
            "GET",
            args.budget_url,
            "/api/budgets/status/category-wise",
            token=access_token,
            query={"year": smoke_budget_year, "month": smoke_budget_month},
            expected={200, 502},
        )
        client.request(
            "budget usage",
            "GET",
            args.budget_url,
            f"/api/budgets/{budget_id}/usage",
            token=access_token,
            expected={200, 502},
        )

        if alert_rule_id:
            client.request(
                "delete alert rule",
                "DELETE",
                args.budget_url,
                f"/api/budgets/{budget_id}/alert-rules/{alert_rule_id}",
                token=access_token,
            )
        if budget_category_id:
            client.request(
                "delete budget category",
                "DELETE",
                args.budget_url,
                f"/api/budgets/{budget_id}/categories/{budget_category_id}",
                token=access_token,
            )
        client.request("delete budget", "DELETE", args.budget_url, f"/api/budgets/{budget_id}", token=access_token)

    report_year = smoke_budget_year
    report_month = smoke_budget_month
    client.request("report health", "GET", args.report_url, "/health")
    client.request("report db health", "GET", args.report_url, "/health/db")
    client.request("report hello", "GET", args.report_url, "/hello")
    client.request(
        "monthly report",
        "GET",
        args.report_url,
        "/api/reports/monthly",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "yearly report",
        "GET",
        args.report_url,
        "/api/reports/yearly",
        token=access_token,
        query={"year": report_year},
    )
    client.request(
        "income vs expense report",
        "GET",
        args.report_url,
        "/api/reports/income-vs-expense",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "category-wise report",
        "GET",
        args.report_url,
        "/api/reports/category-wise",
        token=access_token,
        query={"year": report_year, "month": report_month, "type": "EXPENSE"},
    )
    client.request(
        "wallet-wise report",
        "GET",
        args.report_url,
        "/api/reports/wallet-wise",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "budget performance report",
        "GET",
        args.report_url,
        "/api/reports/budget-performance",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "savings report",
        "GET",
        args.report_url,
        "/api/reports/savings",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "dashboard report",
        "GET",
        args.report_url,
        "/api/reports/dashboard",
        token=access_token,
        query={"year": report_year, "month": report_month},
    )
    client.request(
        "dashboard monthly summary",
        "GET",
        args.report_url,
        "/api/reports/dashboard/monthly-summary",
        token=access_token,
        query={"year": report_year},
    )
    export_job = client.request(
        "create report export",
        "POST",
        args.report_url,
        "/api/reports/export",
        token=access_token,
        json_body={
            "report_type": "MONTHLY",
            "export_type": "PDF",
            "year": report_year,
            "month": report_month,
        },
        expected={201},
    )
    export_job_id = None
    if export_job:
        data = export_job.get("data")
        if isinstance(data, dict):
            export_job_id = data.get("export_job_id")
    client.request(
        "list report export jobs",
        "GET",
        args.report_url,
        "/api/reports/export-jobs",
        token=access_token,
        query={"page": 1, "page_size": 20, "status": "PENDING", "export_type": "PDF"},
    )
    if export_job_id:
        client.request(
            "get report export job",
            "GET",
            args.report_url,
            f"/api/reports/export-jobs/{export_job_id}",
            token=access_token,
        )
    client.request(
        "download missing report file",
        "GET",
        args.report_url,
        f"/api/reports/files/{uuid.uuid4()}/download",
        token=access_token,
        expected={404},
    )

    if refresh_token:
        client.request(
            "auth logout",
            "POST",
            args.auth_url,
            "/auth/logout",
            token=access_token,
            json_body={"refresh": refresh_token},
            expected={204},
        )

    return client.summary()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call every app-defined API with hard-coded smoke-test values.")
    parser.add_argument("--email", required=True, help="User email for register/login.")
    parser.add_argument("--password", required=True, help="User password for register/login. Must satisfy auth validation.")
    parser.add_argument("--auth-url", default=AUTH_BASE_URL, help=f"Auth service URL. Default: {AUTH_BASE_URL}")
    parser.add_argument(
        "--transaction-url",
        default=TRANSACTION_BASE_URL,
        help=f"Transaction service URL. Default: {TRANSACTION_BASE_URL}",
    )
    parser.add_argument("--budget-url", default=BUDGET_BASE_URL, help=f"Budget service URL. Default: {BUDGET_BASE_URL}")
    parser.add_argument("--report-url", default=REPORT_BASE_URL, help=f"Report service URL. Default: {REPORT_BASE_URL}")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
