export default {
  "slug": "alice-thematic-stock-screening",
  "packageType": "skill",
  "alias": "atss",
  "skillNameZh": "按主题选股",
  "tagPrefix": "ALICE_THEMATIC_STOCK_SCREENING",
  "features": {
    "needsUserInput": false,
    "promptPrefix": true,
    "downloadVia": "fetch",
    "chartHtml": false,
    "attachProbeFallback": false,
    "rescanAgentResult": false
  },
  "help": {
    "headline": "<SLUG> — 调用万得 Alice Agent「<ZH>」，支持 主题逻辑拆解、受益标的筛选、估值对比与交易建议，用户原话直接透传给服务端",
    "promptExample": "如何参与AI算力主题？有哪些真受益标的？",
    "etaText": "2-15 分钟",
    "noWaitRoundMin": 30,
    "noWaitTotalMin": 60,
    "examples": [
      "  Set-Location \"D:\\path\\to\\<SLUG>\"; node scripts/cli.mjs --prompt \"如何参与AI算力主题？有哪些真受益标的？\"",
      "  node \"D:\\path\\to\\<SLUG>\\scripts\\cli.mjs\" --prompt \"人形机器人方向买什么股票？\"",
      "  <SLUG> -p \"低空经济产业链有哪些投资机会？\"",
      "  <SLUG> -p \"半导体设备国产化有哪些标的值得关注？\"",
      "  <SLUG> -p \"重新筛选低空经济受益标的\" --new",
      "  <SLUG> -p \"固态电池概念股哪些是真受益？侧重产业链上游\" --no-wait              # 沙箱：CLI 内部自旋直到完成",
      "  <SLUG> -p \"AI算力主题里光模块环节有哪些标的？\" --no-wait --once     # 脚本：单次探针",
      "  <SLUG> -p \"帮我做一份低空经济的<ZH>？\" --detach           # 后台跑，立即返回，IDE 杀终端也不影响"
    ],
    "usageHeadline": "<SLUG> — 调用万得 Alice Agent「<ZH>」技能，支持主题逻辑拆解、受益标的筛选、估值对比与交易建议",
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
  "version": "1.0.13",
  "description": "CLI: 调用万得 Alice Agent「按主题选股」技能（A2A SSE），按主题拆解投资逻辑、筛选受益标的并输出估值与交易建议"
};
