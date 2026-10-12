// 本技能的意图/检索 hint 逻辑。artifactGuard.js（core）只提供外壳，
// 这里的四个导出决定它在**本技能**上怎么认主体。
// 逐技能一份、互不共享——见方案 §1.7：专家包整份继承别的技能的意图逻辑正是缺陷来源。
import { normalizePromptForGuard, compareNormalizedPrompts } from "./promptMatch.js";

/** 过短的通用词，不作为 download/ 文件名匹配 hint。 */
export const genericHints = [
  "分析",
  "请对",
  "主体",
  "信用",
  "资质",
  "风险",
  "报告",
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
  "房地产",
  "行业",
  "财务",
  "健康度",
  "现金流",
  "违约",
  "概率",
  "提示",
  "重点关注",
  "主体信用",
  "券商金股追踪",
  "信用资质",
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
  for (const m of normalized.matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    const raw = m[0].toUpperCase();
    hints.add(raw);
    hints.add(raw.slice(0, 6));
  }
}
// ---- 以下由 duplicateGuard.js 拆出（方案 §9.7）：本技能的主体识别与 replay 比对 ----

/** 券商金股追踪 replay 预检用的通用词（不作为主体 token）。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "券商",
  "金股",
  "追踪",
  "推荐",
  "热门",
  "热度",
  "排行",
  "名单",
  "汇总",
  "统计",
  "分析",
  "报告",
  "本月",
  "上月",
  "近月",
  "哪些",
  "什么",
  "帮我",
  "查询",
  "找出",
  "梳理",
  "对比",
  "行业",
  "主线",
  "分布",
  "逻辑",
  "理由",
  "摘要",
  "趋势",
  "变化",
  "券商金股",
  "券商金股追踪",
  "金股推荐",
  "金股名单",
  "热门金股",
  "给我一份",
  "给我做一份",
  "帮我做一份",
  "帮我分析",
  "的",
  "了",
  "做",
  "给",
  "帮",
  "看",
  "出",
  "一份",
  "下",
  "重点",
  "关注",
  "A股",
  "港股",
  "美股",
]);

/** 常见券商机构识别（key 用于主体锁）。 */
const BROKER_FIRMS = [
  { key: "中信证券", patterns: [/中信证券/, /中信建投/] },
  { key: "华泰证券", patterns: [/华泰证券/] },
  { key: "国泰君安", patterns: [/国泰君安/] },
  { key: "海通证券", patterns: [/海通证券/] },
  { key: "招商证券", patterns: [/招商证券/] },
  { key: "广发证券", patterns: [/广发证券/] },
  { key: "申万宏源", patterns: [/申万宏源/] },
  { key: "中金公司", patterns: [/中金公司/, /中国国际金融/] },
];

/** 常见行业关键词（key 用于主体锁）。 */
const INDUSTRY_TOPICS = [
  { key: "医药生物", patterns: [/医药生物/, /医药/, /生物医药/] },
  { key: "科技", patterns: [/科技/, /科技股/] },
  { key: "新能源", patterns: [/新能源/] },
  { key: "消费", patterns: [/消费/] },
  { key: "金融", patterns: [/金融/] },
  { key: "半导体", patterns: [/半导体/] },
];

/**
 * 从 prompt 提取券商机构 key 集合。
 * @param {string} text
 * @returns {Set<string>}
 */
export function extractBrokerFirms(text) {
  const found = new Set();
  const t = String(text);
  for (const broker of BROKER_FIRMS) {
    for (const p of broker.patterns) {
      if (p.test(t)) {
        found.add(broker.key);
        break;
      }
    }
  }
  return found;
}

/**
 * 从 prompt 提取行业 key 集合。
 * @param {string} text
 * @returns {Set<string>}
 */
export function extractIndustryTopics(text) {
  const found = new Set();
  const t = String(text);
  for (const topic of INDUSTRY_TOPICS) {
    for (const p of topic.patterns) {
      if (p.test(t)) {
        found.add(topic.key);
        break;
      }
    }
  }
  return found;
}

/**
 * 提取时间范围标识（月份 / 近 N 个月）。
 * @param {string} text
 * @returns {string|null}
 */
export function extractTimeScope(text) {
  const t = String(text);
  const ym = t.match(/(\d{4})\s*年\s*(\d{1,2})\s*月/);
  if (ym) return `${ym[1]}-${ym[2].padStart(2, "0")}`;
  if (/本月|这个月|当月/.test(t)) return "current-month";
  if (/上月|上个月/.test(t)) return "last-month";
  const recent = t.match(/近\s*(\d+)\s*个?月/);
  if (recent) return `recent-${recent[1]}m`;
  if (/近半年|半年/.test(t)) return "recent-6m";
  if (/今年|本年度/.test(t)) return "current-year";
  return null;
}

/**
 * 提取目标市场（A股/港股/美股）。
 * @param {string} text
 * @returns {string|null}
 */
export function extractTargetMarket(text) {
  const t = String(text);
  if (/A股|沪深|A 股/.test(t)) return "A股";
  if (/港股|H股|香港/.test(t)) return "港股";
  if (/美股|纳斯达克|NYSE/i.test(t)) return "美股";
  return null;
}

function isPlausibleStockName(name) {
  if (!name || name.length < 2) return false;
  if (REPLAY_SUBJECT_STOPWORDS.has(name)) return false;
  if (/[年月哪些券商推荐热门排行月份]/.test(name)) return false;
  return true;
}

function extractStockName(text) {
  let m = text.match(/([\u4e00-\u9fff]{2,4})最近/);
  if (m && isPlausibleStockName(m[1])) return m[1];
  m = text.match(/([\u4e00-\u9fff]{2,4})(?:被哪些券商|被选为金股|被哪家券商)/);
  if (m && isPlausibleStockName(m[1])) return m[1];
  m = text.match(/(?:查询|查|看|帮)([\u4e00-\u9fff]{2,4})(?:的)?金股/);
  if (m && isPlausibleStockName(m[1])) return m[1];
  return null;
}

function hasBrokerTopPicksIntent(text) {
  const t = String(text);
  if (/金股|券商.*推荐|热门.*股|推荐次数|热度排行|券商观点/.test(t)) return true;
  if (/券商金股追踪|券商金股|月度金股|金股名单/.test(t)) return true;
  return /券商/.test(t) && /推荐|热门|排行|名单|追踪/.test(t);
}

/**
 * 从券商金股追踪 prompt 提取稳定的主体键（时间 + 券商/行业/个股，跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取（如多维度对比）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized || !hasBrokerTopPicksIntent(normalized)) return null;

  const time = extractTimeScope(normalized) || "default-6m";
  const brokers = [...extractBrokerFirms(normalized)];
  const industries = [...extractIndustryTopics(normalized)];
  const market = extractTargetMarket(normalized) || "unspecified";

  if (brokers.length === 1) return `broker:${brokers[0]}:${time}:${market}`;
  if (industries.length === 1) return `industry:${industries[0]}:${time}:${market}`;
  if (brokers.length >= 2 || industries.length >= 2) return null;

  for (const m of normalized.matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    return `code:${m[0].slice(0, 6).toUpperCase()}:${time}`;
  }

  const stockName = extractStockName(normalized);
  if (stockName) return `stock:${stockName}:${time}`;

  if (/金股|券商.*推荐|热门|排行|名单|追踪/.test(normalized)) {
    return `overview:${time}:${market}`;
  }

  return null;
}

/**
 * completed 任务 replay 预检用的相似度（比 running 防护略宽，捕获措辞差异）。
 *
 * @param {string} a normalized prompt
 * @param {string} b normalized prompt
 * @returns {{kind: string, score: number}}
 */
export function comparePromptsForReplay(a, b) {
  const direct = compareNormalizedPrompts(a, b);
  if (direct.kind !== "none") return direct;

  if (!hasBrokerTopPicksIntent(a) || !hasBrokerTopPicksIntent(b)) {
    return { kind: "none", score: direct.score };
  }

  const keyA = computeSubjectKey(a);
  const keyB = computeSubjectKey(b);
  if (keyA && keyB && keyA === keyB) {
    return { kind: "subject", score: 0.85 };
  }

  const timeA = extractTimeScope(a) || "default-6m";
  const timeB = extractTimeScope(b) || "default-6m";
  if (timeA !== timeB) return { kind: "none", score: direct.score };

  const brokersA = extractBrokerFirms(a);
  const brokersB = extractBrokerFirms(b);
  for (const key of brokersA) {
    if (brokersB.has(key)) return { kind: "subject", score: 0.85 };
  }

  const industriesA = extractIndustryTopics(a);
  const industriesB = extractIndustryTopics(b);
  for (const key of industriesA) {
    if (industriesB.has(key)) return { kind: "subject", score: 0.85 };
  }

  return { kind: "none", score: direct.score };
}

/** 本技能不需要「补充输入」提示（features.needsUserInput=false），给个恒 false 的实现供 core 静态导入。 */
export function detectNeedsUserInput() {
  return { needsInput: false, reason: null };
}
