#!/usr/bin/env python3
"""校验 八平台发布文案-v<N>.md 是否符合固定模板（2026-09-15 定版）。
用法: check-publish-copy.py <文案.md>
检查：顶部"对应："与"共用免责段"块；八个平台顺序固定为 抖音、快手、B站、视频号、小红书（弱化品牌名）、YouTube、知乎、公众号；
每个平台含 主推标题/备选标题/正文/（共用免责段）；标题字数硬限制（含标点）：小红书≤20，抖音/快手/视频号/公众号≤30，B站/YouTube/知乎≤40；顶部须有"标题公式（dbs-xhs-title）："行；B站与 YouTube 含"章节："；B站含"本期结构："；抖音/快手/B站/视频号/小红书含"置顶评论："；公众号含"摘要："。
"""
import sys,re
if len(sys.argv)<2 or sys.argv[1] in('-h','--help'):print('用法: python3 check-publish-copy.py <八平台发布文案.md>');sys.exit(2)
s=open(sys.argv[1]).read();bad=[];warn=[]
if not re.search(r'^对应：',s,re.M): bad.append('缺顶部"对应："说明块')
if '共用免责段（各平台正文末尾）' not in s: bad.append('缺顶部"共用免责段（各平台正文末尾）"')
if '标题公式（dbs-xhs-title）：' not in s: bad.append('缺顶部"标题公式（dbs-xhs-title）："行，标题必须先过 /dbs-xhs-title 公式')
order=['抖音','快手','B站','视频号','小红书（弱化品牌名）','YouTube','知乎','公众号']
heads=re.findall(r'^## (.+)$',s,re.M)
if heads!=order: bad.append(f'平台顺序/集合不对: {heads}')
secs=re.split(r'^## .+$',s,flags=re.M)[1:]
for name,body in zip(heads,secs):
    for f in ['主推标题：','备选标题：']:
        if f not in body: bad.append(f'{name} 缺 {f}')
    if name!='公众号':
        if '正文：' not in body: bad.append(f'{name} 缺 正文：')
        if '（共用免责段）' not in body: bad.append(f'{name} 缺 （共用免责段）')
    if name in ['B站','YouTube'] and '章节：' not in body: bad.append(f'{name} 缺 章节：')
    if name=='B站' and '本期结构：' not in body: bad.append('B站 缺 本期结构：')
    if name in ['抖音','快手','B站','视频号','小红书（弱化品牌名）'] and '置顶评论：' not in body: bad.append(f'{name} 缺 置顶评论：')
    if name=='公众号' and '摘要：' not in body: bad.append('公众号 缺 摘要：')
    for m in re.finditer(r'(主推标题|备选标题)：(.+)',body):
        L=len(m.group(2).strip())
        lim={'抖音':30,'快手':30,'视频号':30,'小红书（弱化品牌名）':20,'公众号':30,'B站':40,'YouTube':40,'知乎':40}[name]
        if L>lim: bad.append(f'{name} {m.group(1)} {L}字 > {lim}（硬限制，含标点）')
print('COPY_OK' if not bad else 'COPY_FAIL\n  '+'\n  '.join(bad))
if warn: print('标题超长提示:\n  '+'\n  '.join(warn))
sys.exit(1 if bad else 0)
