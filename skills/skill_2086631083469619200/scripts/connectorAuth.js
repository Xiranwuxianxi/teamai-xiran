/**
 * connectorAuth.js — 复用 WorkBuddy「连接器」中 wind-finance 的 OAuth 令牌。
 *
 * 背景（为什么需要它）
 * --------------------
 * 万得 Alice 的 OAuth 应用（client_id = wdp42vey4ksmt8pzr）只把回调白名单放行给
 *   workbuddy://workbuddy/mcp/connector:wind-finance/oauth/callback
 * 这一个地址，且该地址由 **WorkBuddy 客户端**接管，技能自身收不到授权码；
 * 本机回环地址不在白名单，因此「技能自己发起网页授权并回调」这条路走不通。
 * 而万得站点唯一的账号登录方式是「手机号 + 短信验证码 + 滑块验证码」，
 * 滑块验证码无法在无头环境自动完成 —— 所以技能也无法独立完成登录。
 *
 * 但是：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，
 * 用户在 WorkBuddy「连接器中心」完成过一次授权后，令牌就落在本机
 *   ~/.workbuddy/connectors/<userId>/.credentials.v3.json
 * （AES-256-GCM 加密，密钥由同目录 .master.key 经 HKDF-SHA256 派生）。
 * 本模块只读地解析该仓库、解出 wind-finance 的 access/refresh token，
 * 再用标准 refresh_token 流程换取一个**属于同一账号**的有效 access token。
 * 该 token 对技能使用的 Alice Agent 接口（alice.wind.com.cn/Weaver/ChatAgent）有效。
 *
 * 安全与边界
 * ----------
 * - 只读：绝不写入、不修改、不删除连接器仓库中的任何文件。
 * - 只取 wind-finance 一个 server 的凭据，其余连接器一律忽略。
 * - 校验失败（master.key 不匹配 / userId 不匹配 / 解密失败）时静默放弃，交给上层回退。
 * - 换来的 token 仍写入技能自己的 ~/.wind-alice/config.env（与 login 一致）。
 * - 依赖 WorkBuddy 连接器仓库格式（v3）；格式变化时本模块会返回 null，不影响其它登录方式。
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";

const HKDF_INFO = Buffer.from("workbuddy-oauth-credentials-v1", "utf8");
const CHECK_BYTES = 16;
const KEY_BYTES = 32;
const SALT_BYTES = 16;

const TOKEN_ENDPOINT = "https://market.windalice.com/Wind.AIMarket.Service/api/oauth/token";
const CLIENT_ID = "wdp42vey4ksmt8pzr";
const WIND_SERVER_PREFIX = "wind-finance";

const fsp = fs;

function sha256PrefixHex(uid) {
  return crypto.createHash("sha256").update(uid, "utf8").digest().subarray(0, 16).toString("hex");
}

function computeCheck(input, salt) {
  return crypto
    .createHash("sha256")
    .update(input)
    .update(salt)
    .digest()
    .subarray(0, CHECK_BYTES)
    .toString("base64");
}

function deriveAesKey(masterKey, userId, salt) {
  return Buffer.from(
    crypto.hkdfSync("sha256", Buffer.concat([masterKey, Buffer.from(userId, "utf8")]), salt, HKDF_INFO, KEY_BYTES)
  );
}

function decryptField(envelope, userId, serverKey, fieldName, aesKey) {
  if (!envelope || typeof envelope !== "object") return null;
  if (typeof envelope.iv !== "string" || typeof envelope.tag !== "string" || typeof envelope.ct !== "string") return null;
  const iv = Buffer.from(envelope.iv, "base64");
  const tag = Buffer.from(envelope.tag, "base64");
  const ct = Buffer.from(envelope.ct, "base64");
  const decipher = crypto.createDecipheriv("aes-256-gcm", aesKey, iv);
  decipher.setAAD(Buffer.from(`${userId}|${serverKey}|${fieldName}`, "utf8"));
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ct), decipher.final()]).toString("utf8");
}

function readFileSafe(p) {
  try {
    return fsp.readFileSync(p);
  } catch {
    return null;
  }
}

/** 连接器仓库根目录（可用 WORKBUDDY_HOME 覆盖，便于测试）。 */
export function connectorRoot() {
  const home = process.env.WORKBUDDY_HOME || path.join(os.homedir(), ".workbuddy");
  return path.join(home, "connectors");
}

/** master.key 候选位置：primary 在连接器目录内，backup 在独立根目录下。 */
function masterKeyCandidates(workbuddyHome, userId) {
  const name = sha256PrefixHex(userId) + ".key";
  return [
    path.join(workbuddyHome, "connectors", userId, ".master.key"),
    path.join(workbuddyHome, "app", "connector-keys", name),
    path.join(os.homedir(), ".workbuddy-key-fallback", "connector-keys", name),
  ];
}

/** 列出本机所有可用的连接器仓库（供诊断输出）。 */
export function listConnectorStores() {
  const home = process.env.WORKBUDDY_HOME || path.join(os.homedir(), ".workbuddy");
  const root = path.join(home, "connectors");
  let entries = [];
  try {
    entries = fsp.readdirSync(root, { withFileTypes: true });
  } catch {
    return [];
  }
  const out = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const dir = path.join(root, e.name);
    const hasCred = fsp.existsSync(path.join(dir, ".credentials.v3.json"));
    const hasKey = masterKeyCandidates(home, e.name).some((p) => fsp.existsSync(p));
    if (hasCred) out.push({ userId: e.name, dir, hasMasterKey: hasKey });
  }
  return out;
}

/**
 * 从 WorkBuddy 连接器仓库读取 wind-finance 的令牌。
 * @returns {{accessToken:string|null, refreshToken:string|null, expiresAt:number|null, serverKey:string, serverUrl:string|null, userId:string}|null}
 */
export function readConnectorWindToken() {
  const home = process.env.WORKBUDDY_HOME || path.join(os.homedir(), ".workbuddy");
  for (const store of listConnectorStores()) {
    const { userId, dir } = store;
    const credBuf = readFileSafe(path.join(dir, ".credentials.v3.json"));
    if (!credBuf) continue;
    let cred;
    try {
      cred = JSON.parse(credBuf.toString("utf8"));
    } catch {
      continue;
    }
    const header = cred.encryption || {};
    if (header.scheme !== "aes-256-gcm" || header.kdf !== "hkdf-sha256" || typeof header.salt !== "string") continue;
    let salt;
    try {
      salt = Buffer.from(header.salt, "base64");
    } catch {
      continue;
    }
    if (salt.length !== SALT_BYTES) continue;

    for (const keyPath of masterKeyCandidates(home, userId)) {
      const masterKey = readFileSafe(keyPath);
      if (!masterKey || masterKey.length !== KEY_BYTES) continue;
      // 双重自检：master.key 与 userId 都必须与文件头匹配，否则不是这一份
      if (computeCheck(masterKey, salt) !== header.keyCheck) continue;
      if (computeCheck(Buffer.from(userId, "utf8"), salt) !== header.userIdCheck) continue;

      const aesKey = deriveAesKey(masterKey, userId, salt);
      const mcp = cred.mcpOAuth || {};
      for (const [serverKey, info] of Object.entries(mcp)) {
        if (!serverKey.startsWith(WIND_SERVER_PREFIX)) continue;
        if (!info || typeof info !== "object") continue;
        let accessToken = null;
        let refreshToken = null;
        try {
          accessToken = decryptField(info.accessToken, userId, serverKey, "accessToken", aesKey);
        } catch {
          accessToken = null;
        }
        try {
          refreshToken = decryptField(info.refreshToken, userId, serverKey, "refreshToken", aesKey);
        } catch {
          refreshToken = null;
        }
        if (!accessToken && !refreshToken) continue;
        return {
          accessToken,
          refreshToken,
          expiresAt: typeof info.expiresAt === "number" ? info.expiresAt : null,
          serverKey,
          serverUrl: info.serverUrl || null,
          userId,
        };
      }
    }
  }
  return null;
}

/** 用 refresh_token 换取新的 access_token。 */
export async function refreshConnectorToken(refreshToken, { clientId = CLIENT_ID, endpoint = TOKEN_ENDPOINT } = {}) {
  if (!refreshToken) throw new Error("缺少 refresh_token");
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: clientId,
    refresh_token: refreshToken,
  });
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
      Origin: "https://market.windalice.com",
      Referer: "https://market.windalice.com/",
    },
    body,
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`刷新令牌响应非 JSON（HTTP ${res.status}）：${text.slice(0, 200)}`);
  }
  const data = json.data || json;
  if (!data.access_token) {
    throw new Error(
      `刷新令牌失败（HTTP ${res.status}）：${data.error_description || data.errorMessage || data.message || data.error || text.slice(0, 200)}`
    );
  }
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token || data.refreshToken || refreshToken,
    expiresIn: Number(data.expires_in || data.expiresIn || 7200),
  };
}

/**
 * 解析出一个可用的令牌：优先用未过期的 access token，否则用 refresh_token 换新。
 * 全部失败返回 null（调用方应回退到其它登录方式）。
 */
export async function resolveTokenFromConnector() {
  const found = readConnectorWindToken();
  if (!found) return null;

  const now = Date.now();
  const stillValid =
    found.accessToken && (found.expiresAt === null || found.expiresAt === undefined || now < found.expiresAt - 60_000);
  if (stillValid) {
    return {
      accessToken: found.accessToken,
      refreshToken: found.refreshToken,
      expiresAt: found.expiresAt || now + 7200_000,
      source: "connector",
    };
  }

  if (found.refreshToken) {
    const fresh = await refreshConnectorToken(found.refreshToken);
    return {
      accessToken: fresh.accessToken,
      refreshToken: fresh.refreshToken,
      expiresAt: now + fresh.expiresIn * 1000,
      source: "connector-refresh",
    };
  }

  if (found.accessToken) {
    // 无 refresh_token 且已过期：宁可返回也可能已被服务端拒绝的旧 token，交由上层判定
    return { accessToken: found.accessToken, refreshToken: null, expiresAt: now + 7200_000, source: "connector-stale" };
  }
  return null;
}
