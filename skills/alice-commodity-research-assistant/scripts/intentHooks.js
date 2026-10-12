// 本技能的意图/检索 hint 逻辑。artifactGuard.js（core）只提供外壳，
// 这里的四个导出决定它在**本技能**上怎么认主体。
// 逐技能一份、互不共享——见方案 §1.7：专家包整份继承别的技能的意图逻辑正是缺陷来源。
import { normalizePromptForGuard, compareNormalizedPrompts } from "./promptMatch.js";

/** 过短的通用词，不作为 download/ 文件名匹配 hint。 */
export const genericHints = [
  "分析",
  "请对",
  "主体",
  "日报",
  "报告",
  "期货",
  "品种",
  "商品",
  "智研",
  "助手",
  "系统",
  "公司",
  "集团",
  "股份",
  "有限",
  "企业",
  "建设",
  "发展",
  "投资",
  "控股",
  "行业",
  "基差",
  "库存",
  "基本面",
  "远期曲线",
  "沉淀资金",
  "仓单",
  "宏观",
  "现货价格",
  "商品智研助手",
  "系统分析",
  "做系统",
];
/** 公共中文片段的取词正则（core 用它切 prompt）。 */
export const subjectSegmentPattern = /[\u4e00-\u9fff]{3,16}/g;
/** artifact-guard 警告文案里"或 XX 猜报告"的那个名词。 */
export const subjectNoun = "公司名";
/**
 * 领域专属的 hint 抽取：证券代码 / 期货合约 / 宏观指标 / 市场名 / 日期等，
 * 由本技能自行决定往 hints 里放什么。core 在切中文片段**之前**调用它。
 * @param {string} normalized 已过 normalizePromptForGuard 的 prompt
 * @param {Set<string>} hints  就地写入
 */
export function collectDomainHints(normalized, hints) {
  for (const token of extractCommoditySubjectTokens(normalized)) {
    hints.add(token);
  }

  for (const m of normalized.matchAll(/\b[A-Z]{1,3}\d{0,4}\.(?:SHF|DCE|ZCE|INE|CFFEX|GFEX|CMX|NYM|CBT|ICE|SGX|LME|TOCOM|BMD)\b/gi)) {
    hints.add(m[0].toUpperCase());
  }

  for (const m of normalized.matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    const raw = m[0].toUpperCase();
    hints.add(raw);
    hints.add(raw.slice(0, 6));
  }
}
// ---- 以下由 duplicateGuard.js 拆出（方案 §9.7）：本技能的主体识别与 replay 比对 ----

/** 商品智研助手 replay 预检用的通用词（不作为主体 token）。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "分析",
  "日报",
  "报告",
  "期货",
  "品种",
  "商品",
  "智研",
  "助手",
  "日报报告",
  "分析报告",
  "商品智研助手报告",
  "daily",
  "report",
  "outlook",
  "analysis",
  "帮我",
  "帮我分析",
  "分析一下",
  "最近怎么样",
  "如何",
  "走势",
  "情况",
  "给我一份",
  "给我做一份",
  "帮我做一份",
  "的",
  "了",
  "做",
  "给",
  "帮",
  "看",
  "出",
  "一份",
  "下",
  "一下",
  "重点",
  "关注",
  "基差",
  "库存",
  "基本面",
  "远期曲线",
  "沉淀资金",
  "仓单",
  "宏观",
  "现货价格",
]);

/** Wind 期货品种代码（如 CU.SHF、I.DCE、AU.CMX）。 */
const WIND_COMMODITY_CODE_PATTERN =
  /\b([A-Z]{1,3}\d{0,4}\.(?:SHF|DCE|ZCE|INE|CFFEX|GFEX|CMX|NYM|CBT|ICE|SGX|LME|TOCOM|BMD))\b/i;

const WIND_COMMODITY_CODE_RE = new RegExp(WIND_COMMODITY_CODE_PATTERN.source, "gi");

/**
 * 从 prompt 提取可用于 replay 判定的主体 token（公司名片段 / 证券代码）。
 * @param {string} text normalized prompt
 * @returns {Set<string>}
 */
function extractReplaySubjectTokens(text) {
  const tokens = new Set();
  for (const m of String(text).matchAll(WIND_COMMODITY_CODE_RE)) {
    tokens.add(m[1].toUpperCase());
  }
  for (const m of String(text).matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const seg = m[0];
    if (REPLAY_SUBJECT_STOPWORDS.has(seg)) continue;
    tokens.add(seg);
    if (seg.length >= 5) {
      for (let i = 0; i <= seg.length - 4; i++) {
        const sub = seg.slice(i, i + 4);
        if (!REPLAY_SUBJECT_STOPWORDS.has(sub)) tokens.add(sub);
      }
    }
  }
  return tokens;
}

export function extractCommoditySubjectFromPrompt(normalized) {
  for (const m of String(normalized).matchAll(WIND_COMMODITY_CODE_RE)) {
    return { type: "code", value: m[1].toUpperCase() };
  }

  const namePatterns = [
    /分析一下([\u4e00-\u9fff]{2,8})的/,
    /分析([\u4e00-\u9fff]{2,8})的/,
    /([\u4e00-\u9fff]{2,8})日报/,
    /([\u4e00-\u9fff]{2,8})基差/,
    /([\u4e00-\u9fff]{2,8})基本面/,
    /([\u4e00-\u9fff]{2,8})价格走势/,
    /([\u4e00-\u9fff]{2,8})最近怎么样/,
    /([\u4e00-\u9fff]{2,8})沉淀资金/,
    /请对([\u4e00-\u9fff]{2,8})[（(]/,
  ];
  for (const pattern of namePatterns) {
    const m = String(normalized).match(pattern);
    if (m?.[1] && isLikelyCommodityCoreName(m[1]) && !REPLAY_SUBJECT_STOPWORDS.has(m[1])) {
      return { type: "name", value: m[1] };
    }
  }
  return null;
}

/** 提取 prompt 中所有品种 token（代码 + 中文名），供 artifact hint 使用。 */
export function extractCommoditySubjectTokens(normalized) {
  const tokens = new Set();
  for (const m of String(normalized).matchAll(WIND_COMMODITY_CODE_RE)) {
    tokens.add(m[1].toUpperCase());
  }
  const namePatterns = [
    /分析一下([\u4e00-\u9fff]{2,8})的/,
    /分析([\u4e00-\u9fff]{2,8})的/,
    /([\u4e00-\u9fff]{2,8})日报/,
    /([\u4e00-\u9fff]{2,8})基差/,
    /([\u4e00-\u9fff]{2,8})基本面/,
    /([\u4e00-\u9fff]{2,8})价格走势/,
    /([\u4e00-\u9fff]{2,8})最近怎么样/,
    /([\u4e00-\u9fff]{2,8})沉淀资金/,
    /请对([\u4e00-\u9fff]{2,8})[（(]/,
  ];
  for (const pattern of namePatterns) {
    const m = String(normalized).match(pattern);
    if (m?.[1] && isLikelyCommodityCoreName(m[1]) && !REPLAY_SUBJECT_STOPWORDS.has(m[1])) {
      tokens.add(m[1]);
    }
  }
  return tokens;
}

function hasCommodityResearchIntent(text) {
  const t = String(text);
  if (WIND_COMMODITY_CODE_PATTERN.test(t)) return true;
  return /日报|报告|分析|outlook|daily\s*report|基差|库存|基本面|远期曲线|沉淀资金|仓单|宏观|现货|期货|品种|走势|怎么样/.test(
    t,
  );
}

function isLikelyCommodityCoreName(name) {
  if (!name || name.length < 2) return false;
  if (/^[和与及]/.test(name)) return false;
  if (/和|与|及/.test(name)) return false;
  if (/^(分析|对比|报告|日报|期货|商品|走势|情况)/.test(name)) return false;
  return true;
}

/**
 * 从商品智研助手 prompt 提取稳定的主体键（跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取（如对比多个品种）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized || !hasCommodityResearchIntent(normalized)) return null;

  // 对比多个品种的 prompt 不做主体锁
  if (/对比|比较|二者|两个品种|两者/.test(normalized)) return null;
  if (/(?:对比|比较).{0,24}[\u4e00-\u9fff]{2,8}和[\u4e00-\u9fff]{2,8}/.test(normalized)) return null;

  const codes = new Set();
  for (const m of normalized.matchAll(WIND_COMMODITY_CODE_RE)) {
    codes.add(m[1].toUpperCase());
  }

  const explicit = extractCommoditySubjectFromPrompt(normalized);
  if (explicit?.type === "code") return `code:${explicit.value}`;

  const coreNames = new Set();
  if (explicit?.type === "name") {
    coreNames.add(explicit.value);
  }
  for (const m of normalized.matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const stripped = stripStopwordBorders(m[0]);
    if (stripped && isLikelyCommodityCoreName(stripped) && !REPLAY_SUBJECT_STOPWORDS.has(stripped)) {
      coreNames.add(stripped);
    }
  }

  if (codes.size === 0 && coreNames.size === 0) return null;

  const nameList = [...coreNames].sort((a, b) => b.length - a.length);
  const independentNames = nameList.filter(
    (n, i) => !nameList.some((other, j) => i !== j && (n.includes(other) || other.includes(n))),
  );
  if (independentNames.length >= 2) return null;

  if (codes.size === 1) return `code:${[...codes][0]}`;
  if (nameList.length >= 1) return `name:${nameList[0]}`;
  if (codes.size >= 1) return `code:${[...codes][0]}`;
  return null;
}

/**
 * 只提取正则完整匹配的主体段（公司名连续中文段 / 证券代码），不含滑窗子串。
 * 同时，对较长段去掉前缀/后缀的停用词后提取核心主体名（如「给我一份泰山石油的信用报告」→「泰山石油」）。
 * 用于 comparePromptsForReplay 的 subject 匹配，避免 4 字滑窗片段跨不同主体误匹配。
 * @param {string} text normalized prompt
 * @returns {Set<string>}
 */
function extractReplaySubjectFullSegments(text) {
  const tokens = new Set();
  for (const m of String(text).matchAll(WIND_COMMODITY_CODE_RE)) {
    tokens.add(m[1].toUpperCase());
  }

  const explicit = extractCommoditySubjectFromPrompt(String(text));
  if (explicit?.type === "code") tokens.add(explicit.value);
  if (explicit?.type === "name") tokens.add(explicit.value);
  for (const token of extractCommoditySubjectTokens(String(text))) {
    tokens.add(token);
  }

  for (const m of String(text).matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const seg = m[0];
    if (!REPLAY_SUBJECT_STOPWORDS.has(seg)) {
      tokens.add(seg);
    }
    // Strip leading/trailing stopword runs to extract the core subject name.
    // E.g. "帮我分析一下沪铜的基差" → "沪铜"
    const stripped = stripStopwordBorders(seg);
    if (stripped && stripped.length >= 2 && !REPLAY_SUBJECT_STOPWORDS.has(stripped)) {
      tokens.add(stripped);
    }
  }
  return tokens;
}

/**
 * 去掉中文段首尾的停用词边界，提取核心主体名。
 * 例如：「帮我分析一下沪铜的基差」→「沪铜」
 * @param {string} seg
 * @returns {string|null}
 */
function stripStopwordBorders(seg) {
  // Build a sorted list of stopwords by length (longest first) for greedy matching
  let remaining = seg;
  // Strip leading stopwords
  let changed = true;
  while (changed && remaining.length >= 2) {
    changed = false;
    for (const sw of SORTED_STOPWORDS_BY_LEN) {
      if (remaining.startsWith(sw)) {
        remaining = remaining.slice(sw.length);
        changed = true;
        break;
      }
    }
  }
  // Strip trailing stopwords
  changed = true;
  while (changed && remaining.length >= 2) {
    changed = false;
    for (const sw of SORTED_STOPWORDS_BY_LEN) {
      if (remaining.endsWith(sw)) {
        remaining = remaining.slice(0, remaining.length - sw.length);
        changed = true;
        break;
      }
    }
  }
  return remaining.length >= 2 ? remaining : null;
}

/** REPLAY_SUBJECT_STOPWORDS 按长度降序排列，用于贪心去前缀/后缀。 */
const SORTED_STOPWORDS_BY_LEN = [...REPLAY_SUBJECT_STOPWORDS].sort(
  (a, b) => b.length - a.length,
);

/**
 * completed 任务 replay 预检用的相似度（比 running 防护略宽，捕获「沪铜日报」vs「CU.SHF daily report」等措辞差异）。
 *
 * @param {string} a normalized prompt
 * @param {string} b normalized prompt
 * @returns {{kind: string, score: number}}
 */
export function comparePromptsForReplay(a, b) {
  const direct = compareNormalizedPrompts(a, b);
  if (direct.kind !== "none") return direct;

  if (!hasCommodityResearchIntent(a) || !hasCommodityResearchIntent(b)) {
    return { kind: "none", score: direct.score };
  }

  // Only match on full subject segments (from the regex match, not sliding-window subs).
  // Sliding-window 4-char subs easily appear across different commodity prompts
  // and cause false positives. a.includes(token) is a self-reference tautology.
  const fullSegsA = extractReplaySubjectFullSegments(a);
  const fullSegsB = extractReplaySubjectFullSegments(b);
  for (const seg of fullSegsA) {
    if (seg.length < 2) continue;
    if (fullSegsB.has(seg) || b.includes(seg)) {
      return { kind: "subject", score: 0.85 };
    }
  }
  for (const seg of fullSegsB) {
    if (seg.length < 2) continue;
    if (fullSegsA.has(seg) || a.includes(seg)) {
      return { kind: "subject", score: 0.85 };
    }
  }
  return { kind: "none", score: direct.score };
}

/** 本技能不需要「补充输入」提示（features.needsUserInput=false），给个恒 false 的实现供 core 静态导入。 */
export function detectNeedsUserInput() {
  return { needsInput: false, reason: null };
}
