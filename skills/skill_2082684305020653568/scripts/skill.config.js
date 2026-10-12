export default {
  "slug": "alice-broker-top-picks-tracker",
  "packageType": "skill",
  "alias": "abtpt",
  "skillNameZh": "券商金股追踪",
  "tagPrefix": "ALICE_BROKER_TOP_PICKS_TRACKER",
  "features": {
    "needsUserInput": false,
    "promptPrefix": true,
    "downloadVia": "fetch",
    "chartHtml": false,
    "attachProbeFallback": false,
    "rescanAgentResult": false
  },
  "help": {
    "headline": "<SLUG> — 调用万得 Alice Agent「<ZH>」，覆盖交易/策略/配置多视角与宏观流动性/曲线/技术情绪五大维度，用户原话直接透传给服务端",
    "promptExample": "2026年5月有哪些券商金股？医药生物有没有短线机会？",
    "etaText": "2-15 分钟",
    "noWaitRoundMin": 30,
    "noWaitTotalMin": 60,
    "examples": [
      "  Set-Location \"D:\\path\\to\\<SLUG>\"; node scripts/cli.mjs --prompt \"2026年5月有哪些券商金股？医药生物有没有短线机会？\"",
      "  node \"D:\\path\\to\\<SLUG>\\scripts\\cli.mjs\" --prompt \"最近券商推荐了哪些金股？热度排行如何？\"",
      "  <SLUG> -p \"2026年5月券商金股行业分布如何？\"",
      "  <SLUG> -p \"哪些个股被多家券商同时推荐？\"",
      "  <SLUG> -p \"重新统计本月券商金股推荐\" --new",
      "  <SLUG> -p \"今年券商金股推荐趋势怎么看？\" --no-wait              # 沙箱：CLI 内部自旋直到完成",
      "  <SLUG> -p \"上个月券商金股表现如何？\" --no-wait --once     # 脚本：单次探针",
      "  <SLUG> -p \"2026年5月有哪些券商金股？\" --detach           # 后台跑，立即返回，IDE 杀终端也不影响"
    ],
    "usageHeadline": "<SLUG> — 调用万得 Alice Agent「<ZH>」技能，汇总券商月度金股推荐、统计热度排行与行业分布",
    "etaNote": "",
    "deliverNoun": "评级",
    "reportNoun": "主体报告"
  },
  "runtime": {
    "noWaitSsePhaseTimeoutSec": 600,
    "noWaitSseIdleTimeoutSec": 120,
    "staleTaskThresholdMin": 30,
    "probeAccelTiers": [
      {
        "afterSec": 480,
        "intervalSec": 15
      },
      {
        "afterSec": 180,
        "intervalSec": 30
      },
      {
        "afterSec": 0,
        "intervalSec": 60
      }
    ]
  },
  "version": "1.0.11",
  "description": "CLI: 调用万得 Alice Agent「券商金股追踪」技能（A2A SSE），汇总券商月度金股推荐、统计热度排行与行业分布"
};
