from __future__ import annotations

import json
import subprocess


def run_node(script: str) -> str:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_gateway_client_reads_saved_login_token(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"access_token": "saved-token"}), encoding="utf-8")

    output = run_node(f"""
        process.env.PARQUET_GATEWAY_TOKEN = '';
        process.env.PARQUET_GATEWAY_TOKEN_PATH = {json.dumps(str(token_path))};
        const client = await import('./gateway-client.js');
        console.log(await client.resolveGatewayToken({{ autoLogin: false }}));
    """)

    assert output == "saved-token"


def test_auth_flow_discovers_feishu_authorize_url_from_gateway():
    output = run_node("""
        const calls = [];
        globalThis.fetch = async (url) => {
          calls.push(String(url));
          return {
            ok: true,
            status: 200,
            statusText: 'OK',
            text: async () => JSON.stringify({
              auth_url: 'https://open.feishu.cn/open-apis/authen/v1/authorize?app_id=cli_test',
            }),
          };
        };
        const auth = await import('./auth-flow.js');
        const url = await auth.discoverFeishuAuthUrl({
          gatewayUrl: 'http://gateway.example',
          redirectUri: 'http://127.0.0.1:8765/callback',
        });
        console.log(JSON.stringify({ url, called: calls[0] }));
    """)

    payload = json.loads(output)
    assert payload["url"].startswith("https://open.feishu.cn/")
    assert payload["called"] == (
        "http://gateway.example/auth/feishu/authorize-url?"
        "redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcallback"
    )


def test_gateway_request_sends_client_version_and_warns_on_outdated_response():
    output = run_node("""
        const calls = [];
        const warnings = [];
        process.env.PARQUET_GATEWAY_URL = 'http://gateway.example';
        process.env.PARQUET_GATEWAY_TOKEN = 'token';
        console.error = (message) => warnings.push(message);
        globalThis.fetch = async (url, options) => {
          calls.push({
            url: String(url),
            version: options.headers['X-Parquet-Client-Version'],
          });
          return {
            ok: true,
            status: 200,
            statusText: 'OK',
            headers: {
              get: (name) => ({
                'X-Parquet-Client-Version-Status': 'outdated',
                'X-Parquet-Client-Latest-Version': '0.2.0',
                'X-Parquet-Client-Download-Url': '/downloads/parquet-query-gateway-client.zip',
                'X-Parquet-Client-Guide-Url': '/client-installation-guide.md',
              }[name] || null),
            },
            text: async () => JSON.stringify({ status: 'ok' }),
          };
        };
        const client = await import('./gateway-client.js');
        const payload = await client.gatewayRequest('/health', { auth: false });
        console.log(JSON.stringify({ payload, calls, warnings }));
    """)

    payload = json.loads(output)
    assert payload["payload"] == {"status": "ok"}
    assert payload["calls"][0] == {
        "url": "http://gateway.example/health",
        "version": "0.1.1",
    }
    assert payload["warnings"] == [
        "Parquet Gateway client 0.1.1 is older than server latest 0.2.0. Update: http://gateway.example/downloads/parquet-query-gateway-client.zip (guide: http://gateway.example/client-installation-guide.md)"
    ]


def test_windows_browser_open_avoids_cmd_ampersand_truncation():
    source = open("auth-flow.js", encoding="utf-8").read()

    assert "Start-Process" in source
    assert "-FilePath" in source
    assert "-LiteralPath" not in source
    assert "'cmd'" not in source
    assert "'/c', 'start'" not in source


def test_login_prints_authorization_url_as_fallback():
    source = open("auth-flow.js", encoding="utf-8").read()

    assert "Open this Feishu authorization URL" in source
    assert "console.error" in source
