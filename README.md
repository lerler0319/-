# 🎯 DeltaGear — 三角洲行动低成本卡战备计算器

> 用最少的哈夫币，凑最高的战备值，轻松跨过地图门槛。

## ✨ 功能

- **🔧 DIY配装** — 自由搭配武器、头盔、护甲、背包、胸挂和配件，实时计算总市场价和总战备值，一眼看出能进哪些地图
- **📊 物价总览** — 按分类浏览全部装备，查看效率比（战备值 ÷ 市场价），越高的装备越划算
- **✏️ 战备录入** — 手动校准装备的战备值，覆盖自动估算的数据
- **🗺 地图门槛** — 查看各地图各难度的战备值准入要求
- **📈 价格趋势** — 查看装备价格历史折线图，把握市场波动
- **🔄 一键刷新物价** — 从社区开源数据源拉取交易行实时价格

## 🧠 核心思路

游戏里进入地图需要达到「战备值」门槛，但**战备值 ≠ 市场价**。

部分装备（如破损头盔、特定配件）战备值虚高但市场价极低——用这些装备能以远低于门槛的成本凑够战备值，省钱进图。

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
# 1. 克隆项目
git clone <repo-url>
cd delta-gear

# 2. 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库（导入装备数据）
python seed_data.py
```

### 运行

```bash
streamlit run app.py
```

浏览器打开 `http://localhost:8501` 即可使用。

Windows 用户也可以直接双击 `启动.bat`。

## 📁 项目结构

```
delta-gear/
├── app.py              # Streamlit 主应用（UI + 页面路由）
├── database.py         # SQLite 数据库层（建表、CRUD）
├── optimizer.py        # 配装优化算法（最低成本凑战备）
├── price_fetcher.py    # 价格获取（DeltaForcePrice 社区数据源）
├── seed_data.py        # 初始化种子数据（装备库 + 地图门槛）
├── requirements.txt    # Python 依赖
├── .env.example        # 环境变量模板
└── 启动.bat            # Windows 一键启动脚本
```

## 📦 数据来源

价格数据来自开源社区项目 **[DeltaForcePrice](https://github.com/orzice/DeltaForcePrice)**，每 10 分钟更新一次交易行行情，完全免费。

战备值数据来自社区贡献和游戏内实测，可在「战备录入」页面手动校准。

## 🛠 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | [Streamlit](https://streamlit.io/) |
| 数据库 | SQLite (WAL 模式) |
| 数据处理 | Pandas |
| 图表 | Plotly |
| 数据源 | DeltaForcePrice (GitHub Raw) |

## ⚙️ 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

当前版本使用免费的 GitHub 数据源，无需额外配置即可使用。`.env` 中预留了 API Key 配置项，供后续接入官方数据平台使用。

## 📝 许可

MIT License
