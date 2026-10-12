#!/usr/bin/env node
import { createHash } from "node:crypto";
import { once } from "node:events";
import { mkdirSync, openSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { ensureWindowsUtf8Stdio, writeUtf8BomToFd } from "./encoding.js";
import { resolveDataDir } from "./dataDir.js";
import cfg from "./skill.config.js";

// 逐技能差异全部来自 skill.config.js（构建期由 skill.config.json 生成）；
// 本文件 26 个包共用一份，见方案 §5 Step 2b。
const H = cfg.help;
/** 把配置文案里的 <SLUG> / <ZH> 占位符代入本技能的实际取值。 */
const R = (s) => s.split("<SLUG>").join(cfg.slug).split("<ZH>").join(cfg.skillNameZh);

// 稳定 CLI 入口：把参数转给 request.js（真正的请求 + SSE 解析在那边）。
// 必须 await 子进程退出，否则在某些 Windows / IDE 终端下父进程会先结束，
// 看到的只有 status/headers，后续流式正文被截断。

// 必须在所有 console 输出之前执行：在 Windows 沙箱 / 控制台中把代码页切到 UTF-8,
// 与 Node.js stdout 默认 UTF-8 写入对齐，避免中文提示文案被 GBK 等编码解码出现乱码。
ensureWindowsUtf8Stdio();

const requestEntrypoint = new URL("./request.js", import.meta.url);

// --- promptHash 计算 -------------------------------------------------------
// 必须与 request.js 的 computePromptHash 保持完全一致：
//   SHA256("<技能中文名>::" + 标准化prompt)
// 这样 --detach 模式下 cli.mjs 算出的 hash 与 request.js 写入 <工作目录>/temp/tasks.json
// 的 promptHash 严格相等；调用方可以仅根据 prompt 推算出对应的日志文件名。
// 如果未来 request.js 改动 hash 算法，这里必须同步修改。
//
// 说明：本 CLI **不会**在 prompt 文本里拼接「使用「XX」技能：」前缀（直接透传用户原话），
// 但 promptHash 仍然按 namespace 前缀哈希，避免与其它 skill 的同 prompt 记录混淆。
const ALICE_SKILL_NAME_ZH = cfg.skillNameZh;
function normalizePromptForHash(prompt) {
  return String(prompt ?? "").trim().replace(/\s+/g, " ");
}
function computePromptHash(prompt) {
  const normalized = normalizePromptForHash(prompt);
  const namespaced = `${ALICE_SKILL_NAME_ZH}::${normalized}`;
  return createHash("sha256").update(namespaced, "utf8").digest("hex");
}

// --- 参数解析 --------------------------------------------------------------
const rawArgs = process.argv.slice(2);
/** 部分 Agent 终端会把 JS undefined 字面量拼进 argv，过滤以免误解析。 */
const args = rawArgs.filter((a) => a !== "undefined" && a !== "null");

/**
 * 只读 / 配置类子命令清单：cli.mjs 透传给 request.js 即可，**不要**打主路径那句预计耗时
 * 提示文案，避免误导用户以为子命令也会跑那么久。
 * 必须与 request.js 中的 SUBCOMMANDS 保持一致。
 */
const SUBCOMMANDS = new Set([
  "apikey-set",
  "apikey-get",
  "apikey-clear",
  "status",
  "check-conflict",
  "login",
  "logout",
]);
const headArg = args[0];
const isSubcommand = typeof headArg === "string" && SUBCOMMANDS.has(headArg);

if (!isSubcommand && args.length !== 0 && !args.includes("--help") && !args.includes("-h")) {
  try {
    const { ensureFreshToken } = await import("./windOAuth.js");
    await ensureFreshToken();
  } catch {}
}

function readOptionValue(argv, longName, shortName) {
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === longName || a === shortName) {
      return argv[i + 1];
    }
    if (longName && a.startsWith(longName + "=")) {
      return a.slice(longName.length + 1);
    }
  }
  return undefined;
}

const isHelp = args.length === 0 || args.includes("--help") || args.includes("-h");
if (isHelp) {
  console.log(
    [
      R(H.headline),
      "",
      "Usage:",
      `  ${cfg.slug} --prompt <QUESTION> [--download-dir <DIR>] [--new]`,
      `  ${cfg.slug} --prompt <QUESTION> --detach                        # 后台跑：立刻返回 PID 与日志路径`,
      `  ${cfg.slug} --prompt <QUESTION> --no-wait                       # 沙箱推荐：CLI 内部自旋直到完成（默认）`,
      `  ${cfg.slug} --prompt <QUESTION> --no-wait --once                # 单次探针：几秒内返回`,
      `  ${cfg.slug} login --status                                    # 查看登录状态`,
      `  ${cfg.slug} login --from-connector                          # 复用 WorkBuddy 连接器凭据（唯一支持的登录方式）`,
      `  ${cfg.slug} logout                                            # 退出登录（清除 token）`,
      `  ${cfg.slug} --help`,
      "",
      "Options:",
      `  --prompt,       -p <QUESTION>   用户提问，例如"${R(H.promptExample)}"（必填）`,
      "  --download-dir, -d <DIR>        保留兼容；附件统一落当前工作空间 process.cwd()",
      "  --new                           用户明确要求并行新建：清除该 prompt 全部本地记录后新建",
      "  --context-id <ID>               【推荐续接】从上一轮 DONE 行的 contextId= 取值原样传回",
      "  --new-session                   显式强制新建会话上下文（切话题时加）",
      "  --detach                        启动后台子进程跑完整任务，父进程立即退出",
      `  --no-wait                       CLI 内部自旋 tasks/get 直到完成（全程默认 ${H.noWaitTotalMin}min）`,
      "  --once                          （配合 --no-wait）单次探针",
      "  --watch-interval <SEC>          两次 probe 间隔（默认 60s）",
      `  --watch-timeout  <SEC>          每轮自旋上限（默认 ${H.noWaitRoundMin * 60}s）`,
      `  --watch-absolute-max <SEC>      单次进程全程上限（默认 ${H.noWaitTotalMin * 60}s）`,
      "  --no-strict                     关闭 strict 模式",
      "  --help,         -h              查看帮助",
      "",
      "账号授权子命令（复用 WorkBuddy 连接器凭据）:",
      "  login --status                  查看当前登录状态",
      "  login --from-connector          复用 WorkBuddy 连接器 wind-finance 凭据（唯一支持的登录方式，零交互）",
      "  logout                          退出登录并清除授权令牌",
      "",
      "退出码:",
      `  0 成功（必定伴随 ${cfg.tagPrefix}_DONE）  1 失败  2 参数错误/未配置凭据  4 自旋超时  6 进程中断未完成  75 服务端繁忙`,
      "",
      "Examples (PowerShell):",
      ...H.examples.map(R),
      "",
      "凭据配置位置:",
      "  ~/.wind-aifinmarket/config.env (WIND_ALICE_TOKEN)（兼容旧路径 ~/.wind-alice）",
    ].join("\n"),
  );
  process.exitCode = args.length === 0 ? 2 : 0;
} else {
  const nodePath = process.execPath;
  const { spawn } = await import("node:child_process");

  const isNoWait = args.includes("--no-wait");
  const isOnce = args.includes("--once");
  const isDetach = args.includes("--detach");

  // --detach 与 --no-wait 互斥：detach 是"丢出去后台跑"，no-wait 是"单次探针查"，
  // 两者并用语义不明确。
  if (isDetach && isNoWait) {
    console.error("[CLI] --detach 与 --no-wait 互斥：detach 是后台跑完整任务，no-wait 是单次探针。");
    process.exitCode = 2;
  } else if (isDetach) {
    const prompt = readOptionValue(args, "--prompt", "-p");
    if (!prompt || typeof prompt !== "string" || !prompt.trim()) {
      console.error("[CLI] --detach 模式必须显式提供 --prompt / -p（非空字符串）。");
      process.exitCode = 2;
    } else {
      // 透传给 request.js 的参数：去掉 --detach（其它选项原样保留）
      const childArgs = args.filter((a) => a !== "--detach");

      // 日志目录：resolveDataDir("logs") -> <工作目录>/temp/logs/<promptHash[:12]>.log / .err
      // （跨会话稳定，与 tasks.json / results 同一根目录，便于一次性清理）。
      // 文件名只取 hash 前 12 位：足够避免不同 prompt 碰撞，又便于人眼比对。
      const logDir = resolveDataDir("logs");
      const dataRoot = resolveDataDir();
      try {
        mkdirSync(logDir, { recursive: true });
      } catch (err) {
        console.error(`[CLI] 无法创建日志目录 ${logDir}: ${err.message}`);
        process.exitCode = 1;
        process.exit();
      }

      const hashShort = computePromptHash(prompt).slice(0, 12);
      const promptHash = computePromptHash(prompt);
      const logFile = join(logDir, `${hashShort}.log`);
      const errFile = join(logDir, `${hashShort}.err`);

      // 用 'w' 而非 'a'：同一 prompt 重跑直接覆盖旧日志，避免无限累积；
      // 历史输出本来就由服务端 tasks.json + <工作目录>/temp/results/<hash>.md 兜底，
      // 不依赖日志做归档。
      let outFd;
      let errFd;
      try {
        outFd = openSync(logFile, "w");
        errFd = openSync(errFile, "w");
        // PowerShell Get-Content 默认按 GBK 读无 BOM 的 UTF-8 会乱码；写入 BOM 便于识别
        writeUtf8BomToFd(outFd);
        writeUtf8BomToFd(errFd);
      } catch (err) {
        console.error(`[CLI] 无法打开日志文件: ${err.message}`);
        process.exitCode = 1;
        process.exit();
      }

      // detached: true + stdio: ['ignore', fd, fd] + child.unref()
      // 在 Windows / *nix 上都能让父进程立即退出而子进程继续在后台跑。
      // windowsHide: true 避免在 Windows 上闪一下控制台窗口。
      const child = spawn(
        nodePath,
        [fileURLToPath(requestEntrypoint), ...childArgs],
        {
          detached: true,
          stdio: ["ignore", outFd, errFd],
          windowsHide: true,
          env: { ...process.env, ALICE_DETACH_LOG: logFile },
        },
      );

      child.once("error", (err) => {
        console.error(`[CLI] 后台子进程启动失败: ${err.message}`);
        process.exitCode = 1;
      });

      // 让父进程不再持有子进程引用，从而可以立即退出
      child.unref();

      console.log(
        [
          "[CLI] --detach 已启动后台子进程，可立即关闭本终端 / 切换会话。",
          "[CLI] 分析在后台进行中；可读上面的日志路径查看进度，或用**完全相同**的 prompt 加 --no-wait 接回。",
          `  pid       = ${child.pid ?? "(unknown)"}`,
          `  prompt    = ${prompt}`,
          `  PROMPT_HASH=${promptHash}`,
          `  hash[:12] = ${hashShort}`,
          `  stdout    = ${logFile}`,
          `  stderr    = ${errFile}`,
          "",
          "查看进度（任选其一）：",
          `  · PowerShell:  Get-Content -Path "${logFile}" -Encoding UTF8 -Tail 200 -Wait`,
          `  · *nix:        tail -n 200 -f "${logFile}"`,
          `  · 轮询结果:    ${cfg.slug} -p "${prompt}" --no-wait`,
          `  · 查落盘路径:  ${cfg.slug} status -p "${prompt}"`,
          "",
          "完成后报告位置：",
          `  · 兜底摘要:    ${join(dataRoot, "results", `${promptHash}.md`)}`,
          `  · 任务状态:    ${join(dataRoot, "tasks.json")}`,
          "  · 本地附件:    CLI 输出的 REPORT_FULL_FILE=（静默落盘，Agent 不要展示给用户）",
        ].join("\n"),
      );
      // 不 await child；进程会在控制权返回事件循环后自然退出（child 已 unref）。
    }
  } else if (headArg === "login") {
    const { runLogin } = await import("./windOAuth.js");
    try {
      await runLogin(args.slice(1));
    } catch (e) {
      console.error(JSON.stringify({
        ok: false,
        error: "LOGIN_FAILED",
        message: String((e && e.message) || e),
      }, null, 2));
      process.exitCode = 1;
    }
  } else if (headArg === "logout") {
    const { clearToken } = await import("./windOAuth.js");
    clearToken();
    console.log(JSON.stringify({
      ok: true,
      action: "logout",
      message: "登录令牌已清除。",
    }, null, 2));
  } else {
    // 子命令（login / status / check-conflict 等）只是只读 / 配置操作，几秒内返回；
    // 不应套用主路径那句预计耗时提示文案，否则会误导用户。
    if (isSubcommand) {
      // 静默透传，子命令本身的输出已经足够清晰。
    } else if (isNoWait && !isOnce) {
      console.error(
        `[CLI] --no-wait 内部自旋：默认每 60s 探针、每轮最长 ${H.noWaitRoundMin}min、全程最长 ${H.noWaitTotalMin}min；到轮次上限 CLI 自动续轮，Agent 勿外层连发。`,
      );
    } else if (isNoWait && isOnce) {
      console.error(
        "[CLI] --no-wait --once 单次探针：几秒内返回；禁止 Agent 用此模式在外层循环。",
      );
    } else {
      console.error(
        `[CLI] 子进程即将启动；父进程将阻塞等待直至任务完成（通常 ${H.etaText}），请勿提前结束本命令。`,
      );
      console.error(
        "[CLI] 若在 Trae / 沙箱终端被强制结束，请 `--detach` 后台跑，再用 `--no-wait` 轮询（CLI 内部自旋，无需 --watch）。",
      );
    }
    const child = spawn(
      nodePath,
      [fileURLToPath(requestEntrypoint), ...args],
      { stdio: "inherit" },
    );
    child.once("error", (err) => {
      console.error("spawn failed:", err.message);
      process.exitCode = 1;
    });
    const [code, signal] = await once(child, "exit");
    process.exitCode = signal ? 1 : (code ?? 1);
  }
}
