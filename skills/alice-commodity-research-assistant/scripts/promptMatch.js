// prompt 归一与相似度匹配原语。纯函数，无副作用，便于单测。
// core 版：26 个包共用一份，由 tools/migrate-core-duplicateguard.mjs 从各包 duplicateGuard.js
// 中「26/26 逐字相同」的部分抽出（方案 §9.7）。逐技能的意图逻辑在同目录 intentHooks.js。

/** 最小可比较长度：避免极短 prompt 误判（"分析" 这种 2 字命中所有任务）。 */
export const MIN_LEN_FOR_COMPARE = 8;

/** Jaccard 相似度阈值：bigram 集合的 |A∩B|/|A∪B| ≥ 该值视为相似。 */
export const JACCARD_THRESHOLD = 0.7;

/** trim + 折叠所有连续空白为单空格；与 computePromptHash 的归一化保持一致。 */
export function normalizePromptForGuard(value) {
  return String(value ?? "").trim().replace(/\s+/g, " ");
}

/** 把字符串拆成字符 bigram 集合；中英文混合 prompt 都按字符级处理。 */
function buildBigrams(text) {
  const set = new Set();
  const len = text.length;
  if (len === 0) return set;
  if (len === 1) {
    set.add(text);
    return set;
  }
  for (let i = 0; i < len - 1; i++) {
    set.add(text.slice(i, i + 2));
  }
  return set;
}

function jaccardSimilarity(a, b) {
  if (a.size === 0 && b.size === 0) return 0;
  const [small, large] = a.size <= b.size ? [a, b] : [b, a];
  let inter = 0;
  for (const token of small) {
    if (large.has(token)) inter += 1;
  }
  const union = a.size + b.size - inter;
  return union === 0 ? 0 : inter / union;
}

/**
 * 对两个 normalized prompt 做相似度判定。
 *
 * @param {string} a normalized prompt（调用方应先用 normalizePromptForGuard 处理）
 * @param {string} b normalized prompt
 * @returns {{kind: "identical"|"prefix"|"contained"|"jaccard"|"none", score: number}}
 */
export function compareNormalizedPrompts(a, b) {
  if (typeof a !== "string" || typeof b !== "string") {
    return { kind: "none", score: 0 };
  }
  if (a === b) {
    return { kind: "identical", score: 1 };
  }
  const longer = a.length >= b.length ? a : b;
  const shorter = a.length >= b.length ? b : a;
  if (shorter.length < MIN_LEN_FOR_COMPARE) {
    return { kind: "none", score: 0 };
  }
  if (longer.startsWith(shorter)) {
    return { kind: "prefix", score: 1 };
  }
  if (longer.includes(shorter)) {
    return { kind: "contained", score: 1 };
  }
  const score = jaccardSimilarity(buildBigrams(a), buildBigrams(b));
  if (score >= JACCARD_THRESHOLD) {
    return { kind: "jaccard", score };
  }
  return { kind: "none", score };
}
