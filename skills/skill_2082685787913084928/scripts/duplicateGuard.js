// 重复提交 / 重放防护的对外 API 外壳。
// core 版：26 个包共用一份，由 tools/migrate-core-duplicateguard.mjs 从各包 duplicateGuard.js
// 中「26/26 逐字相同」的部分抽出（方案 §9.7）。逐技能的意图逻辑在同目录 intentHooks.js。
//
// 注意 findSimilarRunning / findSimilarCompleted：2026-08-28 取消重复判断后（§8.2）它们是
// **无条件早返回**，原函数体整段不可达。本次合并把死代码删了——terser 本来也会 dead_code 掉，
// 留着只会让 26 份副本继续各自漂移。行为不变：调用方拿到的仍是 null / []。
import { compareNormalizedPrompts, normalizePromptForGuard } from "./promptMatch.js";

// 原样再导出，模块 API 不能变：合并前这些名字**全部**挂在 duplicateGuard.js 上，
// request.js / artifactGuard.js / 各包 __tests__ / tools/verify-build.mjs 都按老名字引用。
// 钩子那边用 export * ——除了 computeSubjectKey / comparePromptsForReplay，还有 9 个包的
// extract*（extractTradingDate / extractMacroIndicators / extractTargetMarket …）也被各自的
// 测试直接引用，逐个列名字迟早漏。
export { compareNormalizedPrompts, normalizePromptForGuard };
export * from "./intentHooks.js";

/** 默认相似度检查时间窗口（毫秒）。 */
export const DEFAULT_DUPLICATE_GUARD_WINDOW_MS = 10 * 60 * 1000;

/** check-conflict 对 completed 任务的「可重放」检查窗口（毫秒）。 */
export const DEFAULT_REPLAY_GUARD_WINDOW_MS = 24 * 60 * 60 * 1000;

/**
 * 曾用于命中「时间窗口内实质相同的 running 任务」。§8.2 起恒返回 null——
 * 用户提问就执行，不做任何相似度判断。
 */
export function findSimilarRunning() {
  return null;
}

/**
 * 曾用于命中「24h 内实质相同的已完成任务」（replay）。§8.2 起恒返回 []。
 */
export function findSimilarCompleted() {
  return [];
}

/**
 * 构造命中重复提交防护时输出到 stderr 的引导文案。pure 函数便于单测断言。
 *
 * @param {object} ctx
 * @param {string} ctx.prompt 本次要提交的原始 prompt
 * @param {object} ctx.existing registry record（含 taskId、promptPreview 等）
 * @param {{kind: string, score: number}} ctx.match compareNormalizedPrompts 返回值
 * @param {number} [ctx.now] 用于计算已运行多久
 * @returns {string[]} 待按顺序写入 stderr 的多行字符串
 */
export function buildDuplicateGuardMessage({ prompt, existing, match, now = Date.now() }) {
  const elapsedMs = Math.max(0, now - (existing?.startedAt ?? now));
  const elapsedSec = Math.round(elapsedMs / 1000);
  const elapsed =
    elapsedSec < 60
      ? `${elapsedSec}s`
      : elapsedSec < 3600
        ? `${Math.floor(elapsedSec / 60)}m${elapsedSec % 60}s`
        : `${Math.floor(elapsedSec / 3600)}h${Math.floor((elapsedSec % 3600) / 60)}m`;
  const existingPrompt =
    existing?.promptNormalized || existing?.promptPreview || "(无 prompt 预览)";
  const lines = [
    "[CLI][重复提交防护] 检测到时间窗口内已有"
      + "实质相同"
      + "的 running 任务，疑似 Agent 换 prompt 重试，已拒绝提交：",
    `  匹配方式     = ${match?.kind ?? "?"}（score=${(match?.score ?? 0).toFixed(2)}）`,
    `  已有任务     = taskId=${existing?.taskId ?? "?"} 已运行 ${elapsed}`,
    `  已有 prompt = ${existingPrompt}`,
    `  本次 prompt = ${prompt}`,
    "",
    "[CLI][重复提交防护] 正确做法（任选其一）：",
    "  ① 用相同 prompt 续接已有任务（推荐，最省额度）：",
    `       node scripts/cli.mjs --prompt \"${existingPrompt}\" --no-wait`,
    "  ② 若确认就是要新建独立任务，请加 --new：",
    `       node scripts/cli.mjs --prompt \"${prompt}\" --new --no-wait`,
    "",
    "[CLI][重复提交防护] 退出码 76 = EXIT_DUPLICATE_LIKELY；不消耗任何服务端额度。",
  ];
  return lines;
}

/**
 * 构造 check-conflict 命中「相似已完成任务」时的 stderr 引导文案。
 *
 * @param {object} ctx
 * @param {string} ctx.prompt 本次 prompt
 * @param {Array<{record: object, match: object}>} ctx.candidates
 * @returns {string[]}
 */
export function buildReplayGuardMessage({ prompt, candidates }) {
  const hasExact = candidates.some((c) => c.match?.kind === "exact");
  const lines = [
    "[CLI][conflict-check] 检测到 24h 内已有实质相同的已完成任务（疑似另一 Agent 已跑完）。",
  ];
  if (hasExact) {
    lines.push(
      "[CLI][conflict-check] 其中含 matchKind=exact（本地**完全相同 prompt**）：直接 --no-wait = 重放（0 额度、不发请求）；--new --no-wait = 新建扣费。",
    );
  }
  lines.push(
    "[CLI][conflict-check] 禁止读取 download/ 同名报告或 tasks.json 里其它 taskId——promptHash 不同则不是本次结果。",
    "[CLI][conflict-check] Agent 必须把下列候选项列给用户、由用户三选一：",
    "  ① 用已有任务的**原 prompt** 重放（推荐，0 次新额度）：",
  );
  const top = candidates[0]?.record;
  const replayPrompt = top?.promptNormalized || top?.promptPreview || prompt;
  lines.push(`       node scripts/cli.mjs --prompt ${JSON.stringify(replayPrompt)} --no-wait`);
  lines.push("  ② 用户确认要用**当前措辞**重新分析（将按积分扣费，须加 --new）：");
  lines.push(`       node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --new --no-wait`);
  lines.push("  ③ 取消本次提问。");
  lines.push("");
  lines.push(
    "[CLI][conflict-check] exit=12 = 可重放已完成任务；未发起任何服务端请求，不扣积分。",
  );
  return lines;
}
