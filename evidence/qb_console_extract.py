#!/usr/bin/env python3
"""Rebuild QB console line indexes, keyword hits, packing tails, and forensic report.
Reads the five user-provided logs without changing them. No network/root/build calls.
"""
from pathlib import Path
import hashlib, json, re
ROOT = Path(__file__).resolve().parents[1]
KEYS = ['df','free','No space','ENOSPC','Killed','signal','oom','timeout','abort','cancel','returned exit code','rc=']
META = {}; LOGS = {}
def ts(s):
    m = re.match(r'(\d\d):(\d\d):(\d\d),(\d{3})',s)
    return sum(int(x)*f for x,f in zip(m.groups(),[3600,60,1,.001]))
def elapsed(lines,a,b): return f'{ts(lines[b-1])-ts(lines[a-1]):.3f}'
def ref(name,*numbers): return f'`{name}.txt` L'+ '、'.join(map(str,numbers))
def ranges(ns):
    chunks=[]
    for n in ns:
        if chunks and n==chunks[-1][-1]+1: chunks[-1].append(n)
        else: chunks.append([n])
    return '、'.join(str(c[0]) if len(c)==1 else f'{c[0]}–{c[-1]}' for c in chunks) or '无'
for p in sorted((ROOT/'downloads/logs').glob('*full-log.txt')):
    data=p.read_bytes(); lines=data.decode().splitlines(); name=p.stem; LOGS[name]=lines
    matches={k:[i for i,s in enumerate(lines,1) if k.casefold() in s.casefold()] for k in KEYS}
    hitset=sorted({i for v in matches.values() for i in v})
    (ROOT/'evidence'/f'qb-{name}-keyword_hits.txt').write_text('\n'.join(f'{i}: {lines[i-1]}' for i in hitset)+'\n')
    # Selected concise lines are supplementary; full logs and keyword hits are never truncated.
    rx=re.compile(r'Pack all loop|Running command: (?:tar|gzip|pigz)|Traceback|FileNotFoundError|mic returned|mic.conf|starting mic|Running step|Step .*is failed|Finished\.|The build was successful|trigger.getId|build_url|Command working directory|Copy host mic|Start mic in bootstrap|mic 2\.1\.')
    selected=[f'{i}: {s}' for i,s in enumerate(lines,1) if len(s)<4000 and (i<=18 or i>len(lines)-35 or rx.search(s))]
    (ROOT/'evidence'/f'qb-{name}-selected.txt').write_text('\n'.join(selected)+'\n')
    packs=[]
    for j,start in enumerate(i for i,s in enumerate(lines,1) if 'Pack all loop images together' in s):
        # All four image logs have no subsequent Running step; retain every line through EOF.
        end=next((i for i in range(start+1,len(lines)+1) if 'Running step...' in lines[i-1]),len(lines)+1)-1
        raw='\n'.join(f'{i}: {lines[i-1]}' for i in range(start,end+1))+'\n'
        (ROOT/'evidence'/f'qb-{name}-packing-{j+1}.txt').write_text(raw)
        packs.append({'start_line':start,'end_line':end,'lines_to_eof':len(lines)-start+1})
    META[name]={'path':str(p.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
        'lines':len(lines),'ends_with_newline':data.endswith(b'\n'),'last_line':lines[-1], 'keyword_matches':matches,'packing':packs}
(ROOT/'evidence/qb_console_metadata.json').write_text(json.dumps(META,ensure_ascii=False,indent=2)+'\n')
report=['# QB 控制台日志取证（stage2a，2026-10-06）','',
'五份材料是用户新增的 QB 完整控制台输出，包含 mic stdout/stderr、外层脚本与 QB 状态，区别于之前发布的三份 mic `.log`。原文件不改写；行号按换行计数（长 `ks_data` 仍为一行），sha256、尾部换行与逐关键词索引见 [元数据](../evidence/qb_console_metadata.json)。控制台只有时分秒，不自行补日期/时区；与公开 mic.log 重叠段一致，下面只计算同份日志的时间差。', '',
'**当前判定：两次均在预期 `.tar.gz` 缺失后由 mic 抛出 `shutil.move` 的 FileNotFoundError、返回 1，再被 QB 标记失败；mic 被直接杀死/步骤超时的解释不符合控制台收尾。压缩器的原始 rc 和输出被丢弃，ENOSPC 是优先验证的资源假设（低至中置信），压缩器自身受 OOM/SIGKILL 或其他失败尚不能定性。** 证据：`1187398full-log.txt` L8878–8926、8936、8951–8955；`1189686full-log.txt` L8878–8926、8936、8951–8955；[archive.py](../evidence/src_snapshot/mic/mic/archive.py) L66–110、327–348。', '',
'## 一、逐日志命令、环境、worker、步骤边界和状态','',
'`starting mic to create image` 的打印在执行及 rsync 之后，是外层输出顺序/缓冲现象，不能把那一行的时间当成 mic 的真实启动时刻；首个 mic 版本行只能作为已经启动的最早可见证据。例：`1189686full-log.txt` L130、8878、8927–8936。', '']
configs={
'1178308full-log':dict(host='.202',env=48,tmp=73,step=43,execute=46,cmd=8968,mic=132,copy=147,boot=148,inside=157,finish=8949,result=8974,post=8976,ks=24),
'1182527full-log':dict(host='.118',env=57,tmp=82,step=52,execute=55,cmd=8938,mic=148,copy=163,boot=164,inside=173,finish=8919,result=8944,post=8946,ks=29),
'1187398full-log':dict(host='.91',env=48,tmp=73,step=43,execute=46,cmd=8935,mic=130,copy=145,boot=146,inside=155,finish=8951,result=8936,post=8950,ks=24),
'1189686full-log':dict(host='.168',env=48,tmp=73,step=43,execute=46,cmd=8935,mic=130,copy=145,boot=146,inside=155,finish=8951,result=8936,post=8950,ks=24),
}
# Locate rather than assume successful GCC offsets for selected KS and bootstrap.
for name,c in configs.items():
    ls=LOGS[name]
    for key,needle in [('copy','Copy host mic to bootstrap'),('boot','Start mic in bootstrap:'),('ks','image contained ks_data is:')]:
        c[key]=next(i for i,s in enumerate(ls,1) if needle in s)
    c['inside']=next(i for i,s in enumerate(ls,1) if 'mic 2.1.3 (' in s and s.endswith(' tizen)'))
    def line(n): return f'{n}: {ls[n-1]}'
    report += [f'### {name}.txt','',
        f'- worker 为 `ip-192-168-56-{c["host"][1:]}`；工作目录/宿主版本依据 {ref(name,c["env"],c["mic"])}，宿主为 Ubuntu 24.04。image 子步骤的 `Running step` 在 {ref(name,c["step"])}，外层命令开始输出在 {ref(name,c["execute"])}；结束边界见下方状态原文（成功日志只给 post-execute，没有显式数字退出码）。',
        '- 完整 mic 命令（原文）：','', '```text',line(c['cmd']),'```','',
        f'- 命令显式含 `cr auto <ks> --release <RID> -o <outdir> -k <cachedir> --logfile=...`；没有显式 `--runtime`、`--pack-to`、`--tmpdir`、`-c`、`--non-interactive`，不补造这些选项（{ref(name,c["cmd"])}）。选中 KS 头部提供 `-A aarch64 -f loop --pack-to=@NAME@.tar.gz --record-pkgs=name,content,license`（{ref(name,c["ks"])}，该行是长字典，以下只引用头部，不替代原件）。',
        f'- 全文没有 `mic.conf` 字符串，无法据此还原配置文件内容；明确的环境及 bootstrap 行如下（{ref(name,c["env"],c["tmp"],c["copy"],c["boot"],c["inside"])}）。`TMPDIR=/home/tizenbuild/tmp` 是外层环境；实际打包仍在 `/var/tmp/mic/build`（下方 tar 原文），二者不可混同。runtime bootstrap 由执行行为确认。', '', '```text',
        *([line(i) for i in range(c['env']-1,c['tmp']+1)]),line(c['copy']),line(c['boot']),line(c['inside']),'```','',
        '- 步骤开始和结束/最终状态：','', '```text',line(1),line(c['step']),line(c['execute']),line(c['finish']),line(c['result']),line(c['post']),line(len(ls)),'```','']
name='1189639full-log'; ls=LOGS[name]
report += ['### 1189639full-log.txt（父构建）','',
'- 父任务工作主机标识是 `qbsource26`，工作目录 `qbsource26_8914`（`1189639full-log.txt` L26–29、44）；子任务在 `ip-192-168-56-168_8812`。子日志明确记录从父工作目录复制变量到子目录（`1189686full-log.txt` L44–45），不是同一 worker。父日志没有 mic 的版本 hostname，因此不把工作目录标识说成 `hostname` 命令的实测结果。',
'- 没有实际 `starting mic to create image`、`Running command: gzip/pigz`、`Pack all loop images together`、`mic.conf` 或 mic traceback（全文 L1–22544；扫描结果见元数据）；存在生成 KS 与触发 image 子构建。父 `master>IMAGE` 最后被跳过，不包含子日志中实际执行的同一 `master>IMAGE>Image_Create`（L22503–22529、22541–22542）。',
'- 父构建开始 L1 / master Running L10，Trigger_Image_Create 开始 L22503；六个重复触发子步骤在 L22519–22529，未分别标注对应 KS，不能指定其中一行就是 headed-aarch64 的精确开始。结束传播及 master 最终 failure 如下：','', '```text']
for i in [1,10,29,22503,22536,22538,22540,22542,22544]: report.append(f'{i}: {ls[i-1]}')
report += ['```','',
'## 二、关键判定和时间差','',
'### 1187398：clang / gzip','',
'- 存在 shutil.move 的双层 FileNotFoundError traceback（`1187398full-log.txt` L8879–8926），落点 `archive.py:346` 的 `shutil.move(tarball_name, archive_name)`（L8914–8915）。gzip 16:54:24,928 → 首个 traceback 16:55:07,361 = **42.433 秒**；到最终缺文件异常 L8926 是 **42.442 秒**（L8878、8879、8926）。',
'- 压缩启动前后直到 EOF 没有 gzip 自己的 stderr（包括 No space / Killed / ENOSPC），也没有压缩器 rc（L8876–8955；全文关键词检索见第四节）。这不是 gzip 没报错的证明，源码把 stdout/stderr 合并捕获，调用者未处理返回 tuple（archive.py L66–110）。mic 返回 **1**，外层仍完成 mic.log 同步，再抛 LocalError，QB 将 Image_Create、IMAGE、master 正常标为 failed（L8927–8955）。', '',
'### 1189686：clang / pigz','',
'- 同样有 traceback，位置和 gzip 相同（`1189686full-log.txt` L8879–8926、8914–8915）。pigz 16:22:01,450 → 首个 traceback 16:22:31,278 = **29.828 秒**；到最终异常是 **29.836 秒**，到 `mic returned 1` 是 **30.893 秒**（L8878、8879、8926、8936）。',
'- 最后一行为 **L8955 / 16:22:32,955**，距离 pigz 启动 **31.505 秒**；原文见第五节。后面确有 QB 自己的正常 failed 状态链 L8951、8953、8955，没有 step killed、worker lost、timeout/aborted 的实际事件、没有压缩器数字 exit code（L8876–8955，第四节扫描）。',
'- **“pigz 几秒就被杀、mic 死了”被控制台否定**：mic 在约30秒后仍执行 Python 异常路径、向外层返回 1，外层继续 rsync 和 LocalError。这里排除的是 mic 自己被杀/步骤突然终止；不能排除 pigz 子进程先被 SIGKILL，因为没有保留其 rc 或输出（L8879–8955；archive.py L66–110）。', '',
'### 成功对照：1178308 clang gzip / 1182527 gcc gzip','',
'|日志及引用|tar启动→gzip启动|gzip启动→manifest|Pack→manifest|Pack→mic Finished|Pack→QB日志末行|',
'|---|---:|---:|---:|---:|---:|']
for name in ['1178308full-log','1182527full-log']:
    ls=LOGS[name]; start=META[name]['packing'][0]['start_line']; manifest=start+3; finish=configs[name]['finish']
    report += [f'|{ref(name,start,start+1,start+2,manifest,finish,len(ls))}|{elapsed(ls,start+1,start+2)} s|{elapsed(ls,start+2,manifest)} s|{elapsed(ls,start,manifest)} s|{elapsed(ls,start,finish)} s|{elapsed(ls,start,len(ls))} s|']
report += ['',
'“gzip→manifest”含压缩完成、返回和 move 等开销，不是纯压缩 CPU 时间；打包主体以 manifest 为边界，Finished/EOF 还包含校验清单/复制/同步/外层收尾。两份成功打包尾段 **没有 WARNING/WARN/SyntaxWarning，也没有 traceback**（`1178308full-log.txt` L8933–8978；`1182527full-log.txt` L8903–8948）。全文之前有 WARN/安装脚本警告，例如 KS 字典 WARN L21、脚本警告；不能把“打包段无警告”扩展为全文无警告。两份最终成功由 `The build was successful.` 确认（分别 L8974、8944）；没有显式 `mic returned 0`，不伪造 numeric rc。', '',
'### 父构建与 pigz 子构建关系','',
'关系是日志直接证据：`1189686full-log.txt` L36 `trigger.getId(): 1189639`、L37 `build_url: .../1189686`、L44–45 父子变量目录。父只知道触发子任务失败并向上传播，未重复 mic 的缺文件 traceback，错误文本不相同但因果链一致。父 L22536 的 16:22:33,105 紧随子 Image_Create failed（16:22:32,532）及子 master failed（16:22:32,955）；时差分别 **0.573 s / 0.150 s**（`1189686full-log.txt` L8951、8955；`1189639full-log.txt` L22536）。', '',
'```text']
for i in [36,37,44,45]: report.append(f'{i}: {LOGS["1189686full-log"][i-1]}')
report += ['```','',
'父消息 `failed, cancelled, or timed out` 是通用三选一模板，结合子日志明确的异常+返回1+failed链，应解读为子失败传播，不能据模板声称 timeout 或 cancel（父 L22536；子 L8936、8951–8955）。父 build URL、用户给定的 clang/gcc 标签不用于推断编译器因果；worker 不同、发行包不同，成功对照不是控制了所有变量的实验。','',
'## 三、资源原因的区分与置信度','',
'|问题|stage1 只有发布 mic.log|stage2a 控制台后的结论与依据|',
'|---|---|---|',
'|mic 自己被杀 / QB 突然终止？|不可区分|已否定作为此次终止方式；两份均 traceback、mic返回1、QB普通失败链（1187398/1189686 L8879–8955）|',
'|gzip vs pigz 是否只有一个有 traceback？|两份 mic.log 都没有|两个控制台都有，调用栈相同（两份 L8879–8926）|',
'|压缩器 exit1 / SIGKILL？|不可区分|仍不可区分；mic rc1不是压缩器rc（两份 L8936；archive.py L66–110）|',
'|工作盘 ENOSPC？|优先假设|没有df/空闲块/ENOSPC直接证据；机制上仍优先，低至中置信（第四节；两份L8877中间tar）|',
'|pigz OOM / cgroup OOM？|可能|仍无内核/cgroup证据；不能证明或排除子进程OOM，低置信（第四节）|',
'|缺文件触发点及诊断丢失？|源码/探针支持|QB真实 traceback与源码move行一致，置信度高（两份 L8914–8926；archive.py L66–110、327–348）|', '',
'同时 tar 的 rc 也未检查（archive.py 的 `_do_tar` / `_make_tarball`），所以不能仅从后续 gzip/pigz 启动就认定 tar 成功生成完整输入。缺失输出最可能来自被掩盖的外部打包/压缩失败；目前无法把触发原因唯一收敛到 ENOSPC。后续应测打包工作盘分配块/空闲块、压缩器 rc/stderr、cgroup memory.events 和内核记录；本阶段不运行复现。','',
'## 四、全文关键词命中（逐行，可复核）','',
'大小写不敏感 **literal substring** 搜索，列出全部命中行号；“无”表示0命中，不代表系统未发生该事件。原文不截断，保存在各 `evidence/qb-*-keyword_hits.txt`（行首为原日志行号）；机器可读索引在 metadata。`df/free/oom` 特意保留包名、路径、hash 等误命中，避免把搜不到独立命令和搜不到字符串混为一谈。','']
for name,meta in META.items():
    report += [f'### {name}.txt','',f'[全部命中行原文](../evidence/qb-{name}-keyword_hits.txt)','', '|词|命中行数|原文件行号（连续范围包含其间每一行）|','|---|---:|---|']
    for k in KEYS: report += [f'|`{k}`|{len(meta["keyword_matches"][k])}|{ranges(meta["keyword_matches"][k])}|']
    report += ['']
report += ['### 命中语义复核','',
'- 四份 image 日志 `oom` 各1命中，实际上是 `screen_zoom`：1178308 L5021、1182527 L4979、1187398 L4997、1189686 L4997；不是 OOM。`signal` 是 system-signal-sender 包/路径，父是 rust-signal-hook-registry 项目（逐行原文见上方链接）。',
'- `df` 为 dfs-adaptation/dfs-opencv/libsndfile、hash/path 等；`free` 为 libfreebl/libfreetype/freedesktop 等，未见独立 df/free 命令及其磁盘/内存统计输出（五份全文索引及命中原文）。因此不能据这些 substring 命中认定 worker 有资源采样。',
'- image 的 `timeout` 命中来自 KS `bootloader --timeout=3`、`syspopup timeout[-1]` 等，例如1178308 L21、L5697；`cancel` 是 libaction-cancel-alarm.so（1178308 L5337、1182527 L5353、1187398 L5329、1189686 L5329）。父 `timeout` 有 `timeout 9h/6h gbs build` 的命令配置（L1193、3724）及KS内容，**不是 image 超时事件**；父 `cancel` 的唯一命中是上述通用传播模板（L22536）。',
'- 五份均无 `No space`、`ENOSPC`、`Killed`、`abort`、`returned exit code`、`rc=` 字符串。实际 mic 数字返回记录采用 `Error: mic returned 1`（两个失败子日志 L8936），必须额外检索，不能因 requested phrase 无命中就漏掉它。', '',
'## 五、从 Pack all loop images together 到 EOF 的每一行原文','',
'四份 image 日志的打包之后没有下一条 `Running step...`，因此每段保留到 EOF；行首数字只是取证索引，冒号后逐字保留时间戳和原文。空输出的 QB 行也保留。父日志没有这条打包起点，故没有可摘录的打包段（`1189639full-log.txt` L1–22544；metadata packing=[]）。','']
for name,meta in META.items():
    for j,pack in enumerate(meta['packing'],1):
        raw=(ROOT/'evidence'/f'qb-{name}-packing-{j}.txt').read_text().rstrip('\n')
        report += [f'### {name}.txt L{pack["start_line"]}–L{pack["end_line"]}','', '```text',raw,'```','']
# Obtain exact OOM false-positive line numbers dynamically.
for name,meta in META.items():
    if name.startswith('1182527'):
        report=[s.replace('1182527 L4979',f'1182527 L{meta["keyword_matches"]["oom"][0]}') for s in report]
(ROOT/'docs/qb_console_forensics.md').write_text('\n'.join(report)+'\n')
print('Wrote QB report, metadata, and exact line extracts for',len(META),'logs')
