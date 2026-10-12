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
  "按主题选股",
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

/** 按主题选股 replay 预检用的通用词（不作为主题 token）。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "如何",
  "参与",
  "布局",
  "挖掘",
  "筛选",
  "投资",
  "机会",
  "标的",
  "股票",
  "概念股",
  "主题",
  "赛道",
  "概念",
  "产业链",
  "受益",
  "选股",
  "有哪些",
  "什么",
  "哪些",
  "上游",
  "下游",
  "中游",
  "材料",
  "制造",
  "应用",
  "真受益",
  "核心",
  "推荐",
  "关注",
  "值得",
  "买入",
  "配置",
  "分析",
  "报告",
  "投资建议",
  "交易",
  "按主题选股",
  "按主题选股报告",
  "主题选股",
  "主题热点",
  "帮我筛选",
  "帮我分析",
  "我想布局",
  "想布局",
  "给我一份",
  "给我做一份",
  "帮我做一份",
  "的",
  "了",
  "做",
  "给",
  "帮",
  "我",
  "看",
  "出",
  "一份",
  "下",
  "重点",
  "A股",
  "港股",
  "美股",
]);

/** 常见投资主题识别规则（key 用于主体锁）。 */
const THEMATIC_TOPICS = [
  { key: "AI算力", patterns: [/AI算力/i, /人工智能算力/, /算力主题/, /算力产业链/] },
  { key: "低空经济", patterns: [/低空经济/] },
  { key: "人形机器人", patterns: [/人形机器人/] },
  { key: "固态电池", patterns: [/固态电池/] },
  { key: "半导体设备", patterns: [/半导体设备/, /设备国产化/, /半导体设备国产化/] },
];

/**
 * 从 prompt 提取投资主题 key 集合。
 * @param {string} text
 * @returns {Set<string>}
 */
export function extractThematicTopics(text) {
  const found = new Set();
  const t = String(text);
  for (const topic of THEMATIC_TOPICS) {
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
 * 提取目标市场（A股/港股/美股），用于区分同一主题不同市场的筛选任务。
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

function hasThematicScreeningIntent(text) {
  const t = String(text);
  const topics = extractThematicTopics(t);
  if (topics.size > 0) {
    return /主题|赛道|概念|产业链|受益|选股|布局|参与|挖掘|投资|标的|股票/.test(t);
  }
  return /主题选股|赛道投资|概念股|主题热点|按主题/.test(t);
}

/**
 * 从按主题选股 prompt 提取稳定的主体键（主题 + 市场，跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取（如多主题对比）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized || !hasThematicScreeningIntent(normalized)) return null;

  const topics = [...extractThematicTopics(normalized)].sort();
  if (topics.length === 0) return null;

  if (topics.length >= 2 && /对比|比较|和|与|及/.test(normalized)) return null;

  const market = extractTargetMarket(normalized) || "unspecified";
  return `theme:${topics[0]}:${market}`;
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

  if (!hasThematicScreeningIntent(a) || !hasThematicScreeningIntent(b)) {
    return { kind: "none", score: direct.score };
  }

  const topicsA = extractThematicTopics(a);
  const topicsB = extractThematicTopics(b);
  for (const key of topicsA) {
    if (topicsB.has(key)) {
      const marketA = extractTargetMarket(a);
      const marketB = extractTargetMarket(b);
      if (!marketA || !marketB || marketA === marketB) {
        return { kind: "subject", score: 0.85 };
      }
    }
  }

  return { kind: "none", score: direct.score };
}

/** 本技能不需要「补充输入」提示（features.needsUserInput=false），给个恒 false 的实现供 core 静态导入。 */
export function detectNeedsUserInput() {
  return { needsInput: false, reason: null };
}
