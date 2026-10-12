// 统一的数据目录解析：避免多个文件各自重复实现。
//
// 状态目录 = <当前工作目录>/temp/（2026-08-28 变更）
//   tasks.json / results / logs / locks / submit-locks / watchers 全部落在这里，
//   与报告附件（落工作目录根）同处一棵树，宿主 present_files 与用户都能看见。
//
// 为什么以前固定在 ~/.wind-alice/、现在能改回工作区：
//   旧注释记录过一次回退——曾把状态落到 <-d>/.alice-data/，因宿主 WorkBuddy 的 -d 是
//   per-session 临时目录（~/WorkBuddy/<时间戳>/），换会话就读不到上次记录，导致
//   **去重 / replay / 续接失效、重复扣费**，故退回主目录。
//   现已明确不做重复判断（每次提问都新建任务），该顾虑不再成立；状态无需跨会话稳定，
//   放回工作区反而消掉了 WorkBuddy「工作空间外部文件修改」弹窗。
//
// 解析优先级：
//   1. 环境变量 ALICE_DATA_DIR：宿主或测试显式指定（绝对路径）
//   2. <process.cwd()>/temp
//
// 注意：凭据配置（config.env）**不由此处管理**，仍固定在 ~/.wind-aifinmarket/（兼容回退 ~/.wind-alice/），
// 避免随工作区被打包或提交而泄漏（见 request.js 的 KEY_CONFIG_DIR）。
import { join } from "node:path";

/** 工作目录下存放状态的子目录名。 */
export const STATE_SUBDIR = "temp";

/**
 * 解析数据目录。
 * @param {string} [subdir] 子目录名（如 "logs" / "submit-locks"），不传则返回数据根目录
 * @returns {string} 绝对路径
 */
export function resolveDataDir(subdir) {
  const override = process.env.ALICE_DATA_DIR;
  // cwd 在进程生命周期内可变（测试会 chdir），故每次调用重新求值，不做模块级缓存。
  const base = override && String(override).trim()
    ? String(override).trim()
    : join(process.cwd(), STATE_SUBDIR);
  return subdir ? join(base, subdir) : base;
}
