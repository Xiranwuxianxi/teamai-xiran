export default {
  "slug": "alice-deep-research",
  "packageType": "skill",
  "alias": "adr",
  "skillNameZh": "深度研究",
  "tagPrefix": "ALICE_DEEP_RESEARCH",
  "features": {
    "needsUserInput": false,
    "promptPrefix": true,
    "downloadVia": "fetch",
    "chartHtml": false,
    "attachProbeFallback": false,
    "rescanAgentResult": false
  },
  "help": {
    "headline": "<SLUG> — 调用万得 Alice Agent「<ZH>」技能，对任何主题进行结构化多阶段<ZH>（澄清->界定->并行调研->汇总报告）",
    "promptExample": "<ZH>固态电池技术的商业化进展",
    "etaText": "15-30 分钟",
    "noWaitRoundMin": 45,
    "noWaitTotalMin": 90,
    "examples": [
      "  Set-Location \"D:\\path\\to\\<SLUG>\"; node scripts/cli.mjs --prompt \"<ZH>固态电池技术的商业化进展\"",
      "  node \"D:\\path\\to\\<SLUG>\\scripts\\cli.mjs\" --prompt \"全面分析新能源汽车产业链投资机会\"",
      "  <SLUG> -p \"<ZH>东南亚电商市场前景\"",
      "  <SLUG> -p \"全球半导体行业竞争格局如何\"",
      "  <SLUG> -p \"重新<ZH>固态电池技术的商业化进展\" --new",
      "  <SLUG> -p \"<ZH>氢能产业发展现状\" --no-wait              # 沙箱：CLI 内部自旋直到完成",
      "  <SLUG> -p \"<ZH>元宇宙投资机会与风险\" --no-wait --once     # 脚本：单次探针",
      "  <SLUG> -p \"<ZH>固态电池技术的商业化进展\" --detach           # 后台跑，立即返回，IDE 杀终端也不影响"
    ],
    "usageHeadline": "<SLUG> — 调用万得 Alice Agent「<ZH>」技能，结构化多阶段<ZH>（澄清->界定->并行调研->汇总报告）",
    "etaNote": "（多代理并行调研）",
    "deliverNoun": "评级",
    "reportNoun": "主体报告"
  },
  "runtime": {
    "noWaitSsePhaseTimeoutSec": 600,
    "noWaitSseIdleTimeoutSec": 120,
    "staleTaskThresholdMin": 60,
    "probeAccelTiers": [
      {
        "afterSec": 1200,
        "intervalSec": 15
      },
      {
        "afterSec": 600,
        "intervalSec": 30
      },
      {
        "afterSec": 300,
        "intervalSec": 45
      },
      {
        "afterSec": 0,
        "intervalSec": 60
      }
    ]
  },
  "version": "1.0.8",
  "description": "CLI: 调用万得 Alice Agent「深度研究」技能（A2A SSE），对任何主题进行结构化多阶段深度研究（澄清->界定->并行调研->汇总报告）"
};
