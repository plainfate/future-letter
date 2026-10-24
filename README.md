# 去往未来 v0.1

写给未来自己的信（到期才可读），外加热力图、时间记录、每日摘句。
一台局域网里的小服务器就能跑，**零第三方依赖**，只用 Python 标准库。

想先了解这个项目在做什么 → 看 [INTRO.md](INTRO.md)（介绍文档）

![首页](shots/oil_home.png)

---

## 快速开始

在一台 Debian/Ubuntu/Armbian 机器上（需要 root）：

```bash
git clone <这个仓库> future-letter
cd future-letter
sudo bash install.sh
```

装完会直接打印访问地址和初始密码：

- 地址 `http://<这台机器的IP>:9000`
- 密码 `weilai2026` ← **登录后请在「设置」里改掉**

### 其他平台

| 平台 | 怎么跑 |
| --- | --- |
| **Linux（有 systemd）** | `sudo bash install.sh` —— 装服务 + 开机自启 |
| **Linux（无 systemd）**<br>容器 / WSL / OpenWrt / Alpine | `sudo bash install.sh` 会自动降级：装好文件但不注册自启，并提示手动启动命令 |
| **Docker** | `docker compose up -d`（群晖、威联通、任何有 Docker 的机器） |
| **macOS** | `./start.sh`（不需要装服务，前台跑） |
| **Windows** | 双击 `start-windows.bat`（需要先装 Python 3.9+） |

不想装任何东西，只要能跑 Python：

```bash
python3 app.py          # 前台跑，Ctrl+C 停
```

首次运行会自动建库、生成配置。数据就放在项目目录里的 `data.db`。

### 要求

- Python 3.9 以上（已在 3.9 / 3.10 / 3.11 上验证语法兼容）
- 不需要 Node、nginx、Docker、数据库服务
- 内存占用约 25 MB

---

## 装完之后

### 网页里能做的事

| 页面 | 内容 |
| --- | --- |
| **概览** | 日期/农历/下个节日、下一封待拆的信、今日摘句、已经多久、最近的日子、往年这天 |
| **信** | 写给未来的信。未解锁只显示标题和倒计时，**正文不会发送到浏览器** |
| **资讯** | RSS 聚合，默认 36氪、少数派、Solidot、IT之家、开源中国 |
| **时间** | 「已经多久」（3 年 4 个月 23 天 / 共 1241 天 / 下个里程碑）+ 倒数日 |
| **手记** | 每天一篇带心情，顶部是**热力图**，点格子跳到那天 |
| **摘句** | 1030 句中英文句子，每天换一句，「换一句」是真随机 |
| **设置** | 配色、首页模块、新闻源、自动维护、备份、导入导出、改密码、服务器状态、启动与管理 |

### 设置页里的「启动与管理」

网页能**读**状态，**清理缓存**可以直接点按钮。改开机自启和卸载要用命令行（需要 root），
设置页会给出可直接复制的命令。

### 五套配色 × 三种字体

**配色**（默认日出）：

- **日出**（默认）—— 莫奈《印象·日出》：冷灰蓝的雾港，右上角一丸橘红，水面一道倒影
- **油画 · 色块** —— 厚涂色块：墨绿、赭石、靛蓝、奶油，硬边框，位移阴影
- **印象派 · 水彩** —— 米白纸底，淡紫雾蓝的晕染
- **纸上书信** —— 暖白信纸，墨黑宋体，一点朱砂红
- **深夜台灯** —— 深蓝黑底，暖白字，不用金色

**字体**（默认像素）：

- **像素**（默认）—— 点阵屏观感，优先用系统里的 Zpix / 缝合像素 / 方舟像素，没有就退到等宽
- 宋体 —— 衬线，像纸上的活字
- 黑体 —— 无衬线，屏幕阅读最稳

> 像素字体靠字体栈，不打包字体文件（体积和授权问题）。
> 想获得最佳效果，自己装一个像素字体，比如搜「Zpix」或「缝合像素字体」，装完刷新即可。

---

## 命令行

所有事情都有命令行版本，`sudo` 只在需要动 systemd 时用：

```bash
cd /opt/future-letter

python3 app.py --help                      # 看全部命令
python3 app.py --status                    # 服务/缓存/数据状态
python3 app.py --set-password 新密码        # 改密码
python3 app.py --backup /tmp/bk.db         # 备份（会先合并 WAL）
python3 app.py --clear-cache               # 清缓存
python3 app.py --clear-cache --keep 5      # 只留 5 份备份
python3 app.py --clear-cache --news 100    # 只留 100 条资讯
python3 app.py --refresh-news              # 立刻抓一次资讯
```

### 开机自启

```bash
sudo systemctl enable future-letter      # 开启
sudo systemctl disable future-letter     # 关闭
systemctl is-enabled future-letter        # 看状态（不需要 sudo）
```

### 启停与日志

```bash
sudo systemctl restart future-letter
sudo systemctl status future-letter
sudo journalctl -u future-letter -f
sudo journalctl -u future-letter | grep 维护   # 只看后台维护
```

### 卸载

```bash
sudo bash /opt/future-letter/install.sh --uninstall           # 保留数据
sudo bash /opt/future-letter/install.sh --uninstall --purge   # 连数据一起删
```

`--uninstall` 会停服务、删 unit、但**保留** `/opt/future-letter/data.db` 和备份。
`--purge` 删之前会先把最后一份数据库存到 `/root/future-letter-final-*.db`，再删目录。

### 升级

```bash
cd future-letter && git pull
sudo bash install.sh --upgrade     # 保留数据与设置
```

---

## 备份（重要）

**每天自动备份已经开着**，在 `/opt/future-letter/backups/`，保留最近几份。

手动来一份：

```bash
plink -ssh ... "cd /opt/future-letter && setpriv --reuid=future --regid=future \
  --clear-groups python3 app.py --backup /tmp/bk.db"
scp .../tmp/bk.db ./backup.db
```

> **不要直接 `cp data.db`。** 开了 WAL 模式，最近的写入可能还在 `data.db-wal` 里，
> 单拷主库会丢数据。用 `--backup`，它会先 checkpoint 再拷。

想换机器或留个副本：设置页有**「导出全部数据（JSON）」**，信的正文也在里面，
导入只追加、不重复、不删现有内容。

---

## 项目结构

```
future-letter/
├── app.py            网站本体：路由、页面、HTTP、导入导出、CLI
├── store.py          数据层，连接按线程复用
├── feeds.py          RSS 抓取与解析
├── lunar.py          农历 / 干支 / 节日
├── quotes.py         1030 句摘句（含 quotes_more / quotes_en_more）
├── heatmap.py        热力图计算与渲染
├── elapsed.py        「已经多久」的日历计算
├── sysinfo.py        读 /proc 拿 CPU/内存/温度
├── maintenance.py    后台线程：自动抓取、自动备份、合并 WAL
├── themes.py         五套配色 + 三种字体 + 全部 CSS
├── install.sh        安装 / 升级 / 卸载（自动适配有无 systemd）
├── start.sh          macOS / Linux 前台启动
├── start-windows.bat Windows 双击启动
├── docker-compose.yml 容器部署
├── selfcheck.py      静态自检（函数名、模块属性、主题完整性、提示码）
├── test_full.py      107 项自动测试
├── verify_prod.py    线上验收
├── measure.py        测体积和耗时
└── render_preview.py 渲染页面截图
```

运行时（安装后）：

```
/opt/future-letter/
├── app.py 等 .py
├── config.json        端口、会话密钥（权限 600）
├── data.db            ★ 你的信、手记、日子、设置全在这
├── data.db-wal        SQLite 日志，别单独删
└── backups/           自动备份
```

---

## 开发

```bash
python3 selfcheck.py     # 静态自检：函数名、模块属性、主题完整性、提示码
python3 test_full.py     # 107 项：功能、安全、移动端、性能机制
python3 lunar.py         # 农历自检
python3 elapsed.py       # 日期拆分自检
python3 heatmap.py       # 热力图自检
python3 quotes.py        # 摘句去重自检
python3 measure.py http://127.0.0.1:9000 你的密码
```

改完先 `test_full.py` 全绿，再 `sudo bash install.sh --upgrade`。

---

## 性能

| | 数值 |
| --- | --- |
| 首页传输 | 约 1.1 KB（gzip 后） |
| 服务端单页 | 8~9 ms |
| 二次访问 | 304，0 字节 |
| CSS | 约 4 KB，缓存一年 |
| 进程内存 | 约 25 MB |

做法：CSS 独立文件走长缓存、HTML/CSS 都 gzip、页面带 ETag、数据库连接按线程复用、
日期栏与当日摘句按天缓存、农历查询预计算 + 二分。

---

## 踩过的坑（都修了）

1. **iOS 主屏 / 安卓 WebView 上按钮报「拒绝跨站提交」** —— 它们发 `Origin: null`，被基于 Origin 的判断误杀。改成表单带会话令牌。
2. **手机上配色错乱 / 背景变纯色** —— `background-attachment: fixed` 是 iOS Safari 的已知渲染问题，改成固定定位伪元素。
3. **手机上输入框一点就整页放大** —— 字号 15px 触发 iOS 自动缩放且不还原，全部提到 16px。
4. **提交后刷新重复提交** —— 改成提交后 303 重定向。
5. **主题选中框不跟手** —— 改成纯 CSS `:has(input:checked)`。
6. **备份丢数据** —— WAL 模式下单拷主库会丢最近写入，改成先 checkpoint。
7. **后台在干什么看不见** —— 维护线程原来不打日志，现在每件事都写 journal。
8. **导入让信翻倍** —— `letters` 没有唯一约束，改成按「标题+正文+解锁日」判重。
9. **摘句不够随机** —— 原来「换一句」是顺序 +1，改成 `secrets.randbelow` 真随机；每日那句换成 blake2b 并掺入月份和星期，避免相邻日期落在相邻句子。
10. **清缓存把连接关了** —— 线程复用的连接被误关，导致后面 checkpoint 报错。
11. **开机自启开关点了没反应** —— NoNewPrivileges=yes（我加的安全加固）会直接禁止 sudo 提权，
   报错是 "The no new privileges flag is set, which prevents sudo from running as root"。
   服务里调 sudo 就必然失败。改成保留其它加固、去掉这一条，并用极窄的 sudoers 规则约束。
12. **字体切换不生效** —— CSS 的缓存键里只有主题没有字体，切了字体浏览器还用旧 CSS。改成 `?t=主题&f=字体&v=指纹`。

---

## 技术要点

**未解锁的信**：判断在服务端做。未到日期时数据库里的 `body` 字段根本不读出来 ——
不是 CSS 隐藏，看源码、抓请求、猜 URL 都拿不到正文。

**零依赖**：只用 Python 3.11 标准库。

**安全边界**：以低权限用户运行，systemd 开了 `ProtectSystem=strict`、`NoNewPrivileges`、
`PrivateTmp`；除登录页外全部要求登录；表单带会话令牌；跨站提交会被拒。

⚠️ **没有 HTTPS**，只适合局域网。要暴露到公网，必须先套一层带证书的反向代理，
否则密码在网络上是明文。

## 许可

**Apache License 2.0** —— 保留版权，允许商用；比 MIT 多一层明确的专利授权。

见 [LICENSE](LICENSE)。简单说：

- 可以商用、可以改了卖、可以私有部署
- 改完不必开源，但改动过的文件要注明你改过
- 保留版权声明、许可证原文和 NOTICE
- 贡献者授予你专利许可（MIT 没有这条）
- 作者不承担任何责任

本项目 © 2026 去往未来 / Future Letter
