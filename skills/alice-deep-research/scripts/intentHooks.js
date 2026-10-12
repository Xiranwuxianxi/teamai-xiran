// 本技能的意图/检索 hint 逻辑。artifactGuard.js（core）只提供外壳，
// 这里的四个导出决定它在**本技能**上怎么认主体。
// 逐技能一份、互不共享——见方案 §1.7：专家包整份继承别的技能的意图逻辑正是缺陷来源。
import { MIN_LEN_FOR_COMPARE, normalizePromptForGuard, compareNormalizedPrompts } from "./promptMatch.js";

/** 过短的通用词，不作为 download/ 文件名匹配 hint。 */
export const genericHints = [
  "分析",
  "报告",
  "研究",
  "调研",
  "调查",
  "深度",
  "全面",
  "深入",
  "详细",
  "综合",
  "结构化",
  "多阶段",
  "数据",
  "市场",
  "内容",
  "方面",
  "维度",
  "现状",
  "趋势",
  "前景",
  "进展",
  "机会",
  "风险",
  "格局",
  "影响",
  "背景",
  "生成",
  "查看",
  "今日",
  "今天",
  "最近",
  "最新",
  "帮我",
  "给我",
  "一份",
  "深度研究",
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

  const ymd = normalized.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (ymd) {
    const y = ymd[1];
    const mo = ymd[2].padStart(2, "0");
    const d = ymd[3].padStart(2, "0");
    hints.add(`${y}${mo}${d}`);
    hints.add(`${y}年${Number(ymd[2])}月${Number(ymd[3])}日`);
    hints.add(`${Number(ymd[2])}月${Number(ymd[3])}日`);
  }
}
// ---- 以下由 duplicateGuard.js 拆出（方案 §9.7）：本技能的主体识别与 replay 比对 ----

/** 深度研究 replay 预检用的通用词（不作为主体 token）。
 *  研究类 prompt 常带「深度研究/全面分析/调研」等动词词与「的/了/下」等虚词，
 *  这些都不应作为主体键的一部分。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "深度",
  "研究",
  "调研",
  "调查",
  "分析",
  "全面",
  "深入",
  "详细",
  "综合",
  "结构化",
  "多阶段",
  "报告",
  "主题",
  "问题",
  "内容",
  "方面",
  "维度",
  "现状",
  "趋势",
  "前景",
  "进展",
  "机会",
  "风险",
  "格局",
  "影响",
  "背景",
  "帮我",
  "给我",
  "做一份",
  "出一份",
  "一份",
  "看看",
  "了解",
  "一下",
  "关于",
  "对于",
  "对",
  "的",
  "了",
  "和",
  "与",
  "及",
  "等",
  "下",
  "进行",
  "开展",
]);

/** trim + 折叠空白（仅通用文本归一，无领域专有规范化）。 */
function normalizeResearchIntentText(text) {
  return normalizePromptForGuard(text);
}

/**
 * 判定是否为深度研究意图（通用：含「研究/调研/分析/调查」等关键词即视为研究意图）。
 * @param {string} text
 * @returns {boolean}
 */
function hasDeepResearchIntent(text) {
  return /深度研究|全面分析|深入分析|调研|调查研究|综合研究|深度调研|帮我研究|研究一下/.test(text);
}

/**
 * 从深度研究 prompt 提取稳定的主体键（研究主题，跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取。
 *
 * 算法：去掉停用词与单字后，取剩余显著词拼接（按出现顺序去重），最长截断 32 字符。
 * 例如「深度研究固态电池商业化进展」-> deep-research:固态电池商业化进展
 *      「调研固态电池产业现状」    -> deep-research:固态电池产业现状（与上例不同主体键，
 *        但 comparePromptsForReplay 会用 bigram 相似度兜底捕获措辞差异）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizeResearchIntentText(prompt);
  if (!normalized) return null;

  // 按非汉字/字母/数字分割成 token，过滤停用词与过短 token
  const tokens = normalized
    .split(/[^一-鿿A-Za-z0-9]+/)
    .filter((t) => t && t.length >= 2 && !REPLAY_SUBJECT_STOPWORDS.has(t));
  if (tokens.length === 0) return null;

  const subject = tokens.join("");
  if (subject.length < MIN_LEN_FOR_COMPARE) return null;
  return `deep-research:${subject.slice(0, 32)}`;
}

/**
 * completed 任务 replay 预检用的相似度（比 running 防护略宽，捕获措辞差异）。
 *
 * 深度研究通用策略：
 *   1. 先用 compareNormalizedPrompts 做直接相似度（identical/prefix/contained/jaccard）；
 *   2. 命中即返回；未命中则比较主体键，相同视为 subject 匹配（score 0.85）。
 *
 * @param {string} a normalized prompt
 * @param {string} b normalized prompt
 * @returns {{kind: string, score: number}}
 */
export function comparePromptsForReplay(a, b) {
  const direct = compareNormalizedPrompts(a, b);
  if (direct.kind !== "none") return direct;

  const keyA = computeSubjectKey(a);
  const keyB = computeSubjectKey(b);
  if (keyA && keyB && keyA === keyB) {
    return { kind: "subject", score: 0.85 };
  }

  return { kind: "none", score: direct.score };
}

/** 本技能不需要「补充输入」提示（features.needsUserInput=false），给个恒 false 的实现供 core 静态导入。 */
export function detectNeedsUserInput() {
  return { needsInput: false, reason: null };
}
