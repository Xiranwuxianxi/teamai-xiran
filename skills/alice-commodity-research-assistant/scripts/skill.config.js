export default {
  "slug": "alice-commodity-research-assistant",
  "packageType": "skill",
  "alias": "acra",
  "skillNameZh": "商品智研助手",
  "tagPrefix": "ALICE_COMMODITY_RESEARCH_ASSISTANT",
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
    "promptExample": "沪铜日报？铁矿石有没有短线机会？",
    "etaText": "2-15 分钟",
    "noWaitRoundMin": 30,
    "noWaitTotalMin": 60,
    "examples": [
      "  Set-Location \"D:\\path\\to\\<SLUG>\"; node scripts/cli.mjs --prompt \"沪铜日报？铁矿石有没有短线机会？\"",
      "  node \"D:\\path\\to\\<SLUG>\\scripts\\cli.mjs\" --prompt \"螺纹钢期货近期走势如何？库存压力大不大？\"",
      "  <SLUG> -p \"当前原油远期曲线如何？库存怎么变化？\"",
      "  <SLUG> -p \"黄金近期价格驱动因素有哪些？\"",
      "  <SLUG> -p \"重新分析沪铜走势\" --new",
      "  <SLUG> -p \"今年商品市场配置方向怎么看？\" --no-wait              # 沙箱：CLI 内部自旋直到完成",
      "  <SLUG> -p \"铁矿石未来一个月会怎么走？\" --no-wait --once     # 脚本：单次探针",
      "  <SLUG> -p \"沪铜日报\" --detach           # 后台跑，立即返回，IDE 杀终端也不影响"
    ],
    "usageHeadline": "<SLUG> — 调用万得 Alice Agent「<ZH>」技能，输入期货品种名称或 Wind Code 流式输出商品智能研报",
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
  "description": "CLI: 调用万得 Alice Agent「商品智研助手」技能（A2A SSE），输入期货品种名称或 Wind Code 生成多维度商品智能研报"
};
