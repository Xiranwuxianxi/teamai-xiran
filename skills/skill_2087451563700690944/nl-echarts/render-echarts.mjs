#!/usr/bin/env node
/**
 * Render an ECharts option JSON to interactive HTML or static SVG.
 *
 * Usage:
 *   node scripts/render-echarts.mjs --input option.json --out chart.html --format html
 *   node scripts/render-echarts.mjs --input option.json --out chart.svg --format svg
 *
 * HTML 终态强制本地化：把 echarts.min.js 复制到 --out 同目录，script src 只用 ./echarts.min.js。
 * 禁止 CDN（jsdelivr/unpkg 等），避免离线/内网预览空白图。
 */

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

/** fintrust-deep-research skill root（含 package.json / node_modules） */
const SKILL_ROOT = path.resolve(__dirname, '..');

function parseArgs(argv) {
    const args = {
        input: null,
        out: null,
        format: null,
        width: 900,
        height: 520
    };
    for (let i = 2; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--input' || a === '-i') {
            args.input = argv[++i];
        }
        else if (a === '--out' || a === '-o') {
            args.out = argv[++i];
        }
        else if (a === '--format' || a === '-f') {
            args.format = argv[++i];
        }
        else if (a === '--width') {
            args.width = Number(argv[++i]);
        }
        else if (a === '--height') {
            args.height = Number(argv[++i]);
        }
        else if (a === '--help' || a === '-h') {
            args.help = true;
        }
    }
    return args;
}

function resolveFormat(outPath, format) {
    if (format) {
        return format.toLowerCase();
    }
    const ext = path.extname(outPath || '').toLowerCase();
    if (ext === '.html' || ext === '.htm') {
        return 'html';
    }
    return 'svg';
}

function findLocalEchartsMinJs() {
    if (process.env.ECHARTS_JS) {
        const p = path.resolve(process.env.ECHARTS_JS);
        if (fs.existsSync(p) && fs.statSync(p).isFile()) {
            return p;
        }
        throw new Error(`ECHARTS_JS not found: ${p}`);
    }

    const candidates = [];

    // 1) skill root node_modules（主路径）
    candidates.push(
        path.join(SKILL_ROOT, 'node_modules', 'echarts', 'dist', 'echarts.min.js')
    );
    candidates.push(
        path.join(SKILL_ROOT, 'node_modules', 'echarts', 'dist', 'echarts.js')
    );

    // 2) require.resolve（兼容 npm 提升/自定义路径）
    try {
        const pkgJson = require.resolve('echarts/package.json', { paths: [SKILL_ROOT, __dirname] });
        const distDir = path.join(path.dirname(pkgJson), 'dist');
        candidates.push(path.join(distDir, 'echarts.min.js'));
        candidates.push(path.join(distDir, 'echarts.js'));
    }
    catch {
        // fall through
    }

    // 3) 兼容在 Apache ECharts 源码仓内开发
    candidates.push(path.resolve(__dirname, '../../../../dist/echarts.min.js'));
    candidates.push(path.resolve(__dirname, '../../../../dist/echarts.js'));

    for (const p of candidates) {
        if (fs.existsSync(p) && fs.statSync(p).isFile()) {
            return p;
        }
    }
    return null;
}

/**
 * 将本地 echarts 复制到图表输出目录，返回相对 script src（永远 ./echarts.min.js）。
 * 同目录多图共享一份文件；已存在且大小一致则跳过复制。
 */
function vendorEchartsNextToOut(outPath) {
    const src = findLocalEchartsMinJs();
    if (!src) {
        throw new Error(
            '找不到本地 echarts.min.js。请在技能根目录执行：npm install\n'
            + `期望路径：${path.join(SKILL_ROOT, 'node_modules/echarts/dist/echarts.min.js')}`
        );
    }
    const outDir = path.dirname(path.resolve(outPath));
    fs.mkdirSync(outDir, { recursive: true });
    const dest = path.join(outDir, 'echarts.min.js');
    const srcStat = fs.statSync(src);
    let needCopy = true;
    if (fs.existsSync(dest)) {
        try {
            if (fs.statSync(dest).size === srcStat.size) {
                needCopy = false;
            }
        }
        catch {
            needCopy = true;
        }
    }
    if (needCopy) {
        fs.copyFileSync(src, dest);
    }
    return './echarts.min.js';
}

/** 把 option 里被写成字面 \\n/\\t 的字符串还原为真换行，避免饼图标签显示「\\n」。 */
function unescapeEchartsText(value) {
    if (typeof value === 'string') {
        if (value.includes('\\n') || value.includes('\\t') || value.includes('\\r')) {
            return value
                .replaceAll('\\r\\n', '\n')
                .replaceAll('\\n', '\n')
                .replaceAll('\\t', '\t')
                .replaceAll('\\r', '\r');
        }
        return value;
    }
    if (Array.isArray(value)) {
        return value.map(unescapeEchartsText);
    }
    if (value && typeof value === 'object') {
        const out = {};
        for (const [k, v] of Object.entries(value)) {
            out[k] = unescapeEchartsText(v);
        }
        return out;
    }
    return value;
}

async function loadEcharts() {
    if (process.env.ECHARTS_PATH) {
        const p = path.resolve(process.env.ECHARTS_PATH);
        if (fs.existsSync(p)) {
            const mod = await import(pathToFileURL(
                fs.statSync(p).isDirectory() ? path.join(p, 'index.js') : p
            ).href);
            return mod.default || mod;
        }
        throw new Error(`ECHARTS_PATH not found: ${p}`);
    }

    try {
        return require(require.resolve('echarts', { paths: [SKILL_ROOT, __dirname] }));
    }
    catch {
        // fall through
    }

    const minJs = findLocalEchartsMinJs();
    if (minJs) {
        return require(minJs);
    }

    throw new Error(
        'Cannot load echarts. 请在技能根目录执行 npm install，或设置 ECHARTS_PATH / ECHARTS_JS。'
    );
}

function cleanHtmlTitle(title) {
    return Array.from(String(title || 'ECharts'))
        .filter((char) => !'<>&'.includes(char))
        .join('');
}

function isRemoteScriptSource(scriptSrc) {
    const source = String(scriptSrc).toLowerCase();
    return source.startsWith('http://')
        || source.startsWith('https://')
        || source.includes('cdn.')
        || source.includes('jsdelivr')
        || source.includes('unpkg');
}

function wrapInteractiveHtml(option, title, scriptSrc, width, height) {
    const safeTitle = cleanHtmlTitle(title);
    const optionJson = JSON.stringify(option, null, 2);
    if (isRemoteScriptSource(scriptSrc)) {
        throw new Error(`拒绝 CDN script src：${scriptSrc}；必须使用本地 ./echarts.min.js`);
    }
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${safeTitle}</title>
<script src="${scriptSrc}"></script>
<style>
  html, body { margin: 0; height: 100%; background: #fff; }
  #main { width: 100%; height: ${height}px; min-height: 420px; }
</style>
</head>
<body>
<div id="main"></div>
<script>
  var option = ${optionJson};
  var chart = echarts.init(document.getElementById('main'), null, {
    width: ${width},
    height: ${height}
  });
  chart.setOption(option);
  window.addEventListener('resize', function () { chart.resize(); });
</script>
</body>
</html>
`;
}

async function main() {
    const args = parseArgs(process.argv);
    if (args.help || !args.input || !args.out) {
        console.log(`Usage:
  node scripts/render-echarts.mjs --input option.json --out chart.html --format html
  node scripts/render-echarts.mjs --input option.json --out chart.svg --format svg
  Optional: --width 900 --height 520
  Env: ECHARTS_JS=/path/to/echarts.min.js  ECHARTS_PATH=/path/to/echarts`);
        process.exit(args.help ? 0 : 1);
    }

    const inputPath = path.resolve(args.input);
    const outPath = path.resolve(args.out);
    const format = resolveFormat(outPath, args.format);

    if (!fs.existsSync(inputPath)) {
        throw new Error(`Input not found: ${inputPath}`);
    }

    const option = unescapeEchartsText(JSON.parse(fs.readFileSync(inputPath, 'utf8')));
    fs.mkdirSync(path.dirname(outPath), { recursive: true });

    if (format === 'html') {
        const title = option?.title?.text || 'ECharts 图表';
        const scriptSrc = vendorEchartsNextToOut(outPath);
        const html = wrapInteractiveHtml(option, title, scriptSrc, args.width, args.height);
        fs.writeFileSync(outPath, html, 'utf8');
        console.log(JSON.stringify({
            ok: true,
            format: 'html',
            interactive: true,
            out: outPath,
            scriptSrc,
            echartsLocal: path.join(path.dirname(outPath), 'echarts.min.js'),
            bytes: fs.statSync(outPath).size
        }));
        return;
    }

    if (format !== 'svg') {
        throw new Error(`Unsupported format: ${format} (use svg or html)`);
    }

    const echarts = await loadEcharts();
    const chart = echarts.init(null, null, {
        renderer: 'svg',
        ssr: true,
        width: args.width,
        height: args.height
    });
    chart.setOption(option);
    const svg = chart.renderToSVGString();
    chart.dispose();

    if (typeof svg !== 'string' || !svg.includes('<svg')) {
        throw new Error('ECharts SSR did not return valid SVG');
    }

    fs.writeFileSync(outPath, svg, 'utf8');
    console.log(JSON.stringify({
        ok: true,
        format: 'svg',
        interactive: false,
        out: outPath,
        bytes: fs.statSync(outPath).size
    }));
}

main().catch((err) => {
    console.error(String(err && err.stack || err));
    process.exit(1);
});
