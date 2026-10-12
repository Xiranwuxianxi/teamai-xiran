import { existsSync, mkdirSync, readFileSync, writeFileSync, chmodSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import readline from "node:readline/promises";
import { stdin, stdout } from "node:process";
import crypto from "node:crypto";

export const AS = "https://market.windalice.com/Wind.AIMarket.Service";
export const CLIENT_ID = "wdp42vey4ksmt8pzr";
export const REDIRECT_URI = "workbuddy://workbuddy/mcp/connector:wind-finance/oauth/callback";

const CFG_DIR = join(homedir(), ".wind-alice");
const CFG_FILE = join(CFG_DIR, "config.env");
const LEGACY_FILE = join(CFG_DIR, "config");
const PKCE_FILE = join(CFG_DIR, "oauth_pkce.json");
const isTok = (l) => /^(WIND_ALICE_TOKEN|WIND_ALICE_REFRESH_TOKEN|WIND_ALICE_TOKEN_EXPIRES_AT)=/.test(l.trim());
const b64u = (b) => b.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

export function savePendingPkce(d) {
  try { mkdirSync(CFG_DIR, { recursive: true }); writeFileSync(PKCE_FILE, JSON.stringify(d), "utf8"); } catch {}
}
export function loadPendingPkce() {
  try { return JSON.parse(readFileSync(PKCE_FILE, "utf8")); } catch { return null; }
}

export function createPkce() {
  const verifier = b64u(crypto.randomBytes(48));
  const challenge = b64u(crypto.createHash("sha256").update(verifier).digest());
  const state = crypto.randomBytes(16).toString("hex");
  savePendingPkce({ state, verifier, challenge });
  return { verifier, challenge, state };
}

export function buildAuthorizeUrl({ challenge, state } = {}) {
  let c = challenge, s = state;
  if (!c || !s) { const p = createPkce(); c = p.challenge; s = p.state; }
  return "https://market.windalice.com/#/authorize?" + new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    state: s,
    code_challenge: c,
    code_challenge_method: "S256",
  }).toString();
}

export function parseCallbackUrl(s) {
  if (!s) return null;
  const str = String(s).trim();
  const m = str.match(/[?&]code=([\w.-]+)/) || str.match(/^([\w.-]+)$/);
  const st = str.match(/[?&]state=([\w.-]+)/);
  return m ? { code: m[1], state: st ? st[1] : null } : null;
}

async function postToken(params) {
  const r = await fetch(`${AS}/api/oauth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
      Origin: "https://market.windalice.com",
      Referer: "https://market.windalice.com/",
    },
    body: new URLSearchParams(params),
  });
  const t = await r.text();
  let j = {}; try { j = JSON.parse(t); } catch {}
  if (!r.ok || j.error) throw new Error(j.error_description || j.errorMessage || j.message || `Token 失败 (HTTP ${r.status})`);
  const d = j.data || j;
  const tok = d.access_token || d.accessToken;
  if (!tok) throw new Error("无 Token");
  return { access_token: tok, refresh_token: d.refresh_token || d.refreshToken || params.refresh_token || null, expires_in: Number(d.expires_in || 7200) };
}

export async function exchangeToken({ code, verifier, state }) {
  let v = verifier;
  if (!v) { const p = loadPendingPkce(); if (p?.verifier) v = p.verifier; }
  const params = { grant_type: "authorization_code", client_id: CLIENT_ID, code, redirect_uri: REDIRECT_URI };
  if (v) params.code_verifier = v;
  return postToken(params);
}

export async function refreshToken({ refreshToken }) {
  return postToken({ grant_type: "refresh_token", client_id: CLIENT_ID, refresh_token: refreshToken });
}

function readEnvLines() {
  if (!existsSync(CFG_FILE)) return [];
  try { return readFileSync(CFG_FILE, "utf8").split(/\r?\n/); } catch { return []; }
}
function writeEnvLines(lines) {
  mkdirSync(CFG_DIR, { recursive: true });
  writeFileSync(CFG_FILE, lines.filter(Boolean).join("\n") + "\n", "utf8");
  if (process.platform !== "win32") { try { chmodSync(CFG_FILE, 0o600); } catch {} }
}

export function saveToken({ accessToken, refreshToken, expiresAt }) {
  const lines = readEnvLines().filter((l) => !isTok(l));
  lines.push(`WIND_ALICE_TOKEN=${accessToken}`, ...(refreshToken ? [`WIND_ALICE_REFRESH_TOKEN=${refreshToken}`] : []), ...(expiresAt ? [`WIND_ALICE_TOKEN_EXPIRES_AT=${expiresAt}`] : []));
  writeEnvLines(lines);
}

export function loadToken() {
  if (!existsSync(CFG_FILE)) return null;
  try {
    const text = readFileSync(CFG_FILE, "utf8");
    const m = text.match(/^\s*WIND_ALICE_TOKEN\s*=\s*([^\r\n]+)/m);
    if (!m) return null;
    const mr = text.match(/^\s*WIND_ALICE_REFRESH_TOKEN\s*=\s*([^\r\n]+)/m);
    const me = text.match(/^\s*WIND_ALICE_TOKEN_EXPIRES_AT\s*=\s*([^\r\n]+)/m);
    return { accessToken: m[1].trim().replace(/^["']|["']$/g, ""), refreshToken: mr ? mr[1].trim() : null, expiresAt: me ? Number(me[1].trim()) : null };
  } catch { return null; }
}

export function isTokenValid(tokens) {
  if (!tokens || !tokens.accessToken) return false;
  return !tokens.expiresAt || Date.now() < tokens.expiresAt - 60000;
}

export async function ensureFreshToken() {
  const tokens = loadToken();
  if (isTokenValid(tokens)) return tokens;
  if (tokens && tokens.refreshToken) {
    try {
      const res = await refreshToken({ refreshToken: tokens.refreshToken });
      const expiresAt = Date.now() + (res.expires_in || 7200) * 1000;
      saveToken({
        accessToken: res.access_token,
        refreshToken: res.refresh_token || tokens.refreshToken,
        expiresAt,
      });
      return loadToken();
    } catch {}
  }
  try {
    const { resolveTokenFromConnector } = await import("./connectorAuth.js");
    const fresh = await resolveTokenFromConnector();
    if (fresh && fresh.accessToken) {
      const expiresAt = fresh.expiresAt || Date.now() + 7200000;
      saveToken({
        accessToken: fresh.accessToken,
        refreshToken: fresh.refreshToken || null,
        expiresAt,
      });
      return loadToken();
    }
  } catch {}
  return null;
}

export async function ensureValidToken() {
  const fresh = await ensureFreshToken();
  return fresh ? fresh.accessToken : null;
}

export function clearToken() {
  if (existsSync(CFG_FILE)) writeEnvLines(readEnvLines().filter((l) => !isTok(l)));
}

async function finishLogin({ code, verifier, state }) {
  const t = await exchangeToken({ code, verifier, state });
  const expiresAt = Date.now() + t.expires_in * 1000;
  saveToken({ accessToken: t.access_token, refreshToken: t.refresh_token, expiresAt });
  console.log(JSON.stringify({ ok: true, action: "login", message: "登录成功", expiresAt }, null, 2));
}

export async function runLogin(cliArgs = process.argv.slice(2)) {
  const args = Array.isArray(cliArgs) && cliArgs.length > 0 ? cliArgs : process.argv.slice(2);
  const flags = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq !== -1) flags[a.slice(2, eq)] = a.slice(eq + 1);
      else { const k = a.slice(2), next = args[i + 1]; if (next && !next.startsWith("-")) { flags[k] = next; i++; } else flags[k] = true; }
    }
  }

  if (flags["send-code"] || flags.phone || flags.code || flags.open || flags.callback || flags.url) {
    console.log(JSON.stringify({
      ok: false,
      error: "LOGIN_METHOD_DISABLED",
      message: "手机验证码登录与网页授权登录已下线。当前唯一支持的登录方式是复用 WorkBuddy 连接器凭据。",
      howTo: [
        "WorkBuddy →「连接器」→「Wind Alice 万得金融数据」(wind-finance) → 连接并完成授权",
        "node scripts/cli.mjs login --from-connector 复验",
      ],
    }, null, 2));
    process.exitCode = 2;
    return;
  }

  if (flags["from-connector"] || flags.connector || (Object.keys(flags).length === 0 && stdin.isTTY)) {
    const { resolveTokenFromConnector } = await import("./connectorAuth.js");
    const res = await resolveTokenFromConnector();
    if (!res || !res.accessToken) {
      throw new Error("未在本机 WorkBuddy 连接器仓库中找到 wind-finance 凭据；请先在 WorkBuddy「连接器」中绑定 wind-finance 后重试");
    }
    const expiresAt = res.expiresAt || Date.now() + 7200000;
    saveToken({ accessToken: res.accessToken, refreshToken: res.refreshToken || null, expiresAt });
    console.log(JSON.stringify({ ok: true, action: "login", source: res.source, expiresAt }, null, 2));
    return;
  }

  if (flags.status) {
    const tok = loadToken(), v = isTokenValid(tok);
    console.log(JSON.stringify({ ok: v, status: v ? "configured" : "missing", authType: "oauth_token", expiresAt: tok?.expiresAt || null }, null, 2));
    if (!v) process.exitCode = 1;
    return;
  }

  if (flags.logout) {
    clearToken();
    return console.log(JSON.stringify({ ok: true, action: "logout" }));
  }

  if (!stdin.isTTY) {
    return console.log(JSON.stringify({
      ok: false,
      error: "NON_INTERACTIVE",
      hint: "login --from-connector | login --status | logout",
    }, null, 2));
  }
}
