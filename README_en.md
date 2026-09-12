<p align="center"><a href="README.md">简体中文</a> | <b>English</b></p>

<h1 align="center">a-stock-data</h1>

<p align="center">
  <b>Full-stack data toolkit for China A-shares — 12 layers · 60 endpoints · 22 sources · zero-auth</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white" alt="Python">
  <a href="https://github.com/simonlin1212/a-stock-data/stargazers"><img src="https://img.shields.io/github/stars/simonlin1212/a-stock-data?style=social" alt="Stars"></a>
  <br>
  <img src="https://img.shields.io/badge/layers-12-2ea44f.svg" alt="Layers">
  <img src="https://img.shields.io/badge/endpoints-60-2ea44f.svg" alt="Endpoints">
  <img src="https://img.shields.io/badge/sources-22-2ea44f.svg" alt="Sources">
  <img src="https://img.shields.io/badge/auth-zero-success.svg" alt="Zero Auth">
</p>

<p align="center">
  <a href="#architecture">Architecture</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#60-endpoints">Endpoints</a> ·
  <a href="./CHANGELOG.md">Changelog</a>
</p>

Full-stack data toolkit for China A-Share market — 12-layer architecture · 60 capability endpoints (55 primary + 5 backups) · 22 data sources · TDX-first with automatic fallback

A self-contained Skill file that consolidates raw A-share data from 22 sources into a ready-to-use toolkit for AI coding assistants. Market data prefers the local `injoyai/tdx` REST service and automatically falls back to mootdx; Eastmoney PDF Referer and iwencai X-Claw details are handled as well.

> Compatible with [Claude Code](https://github.com/anthropics/claude-code) · [Codex](https://github.com/openai/codex) · [OpenClaw](https://github.com/anthropics/openclaw)
>
> The Skill file is structured Markdown + embedded Python. Any AI coding assistant with context injection can use it.

---

## Open to AI Roles in Shenzhen

The author is open to AI roles in Shenzhen, particularly in **AI-powered investment research products, Forward Deployed Engineering (FDE), and AI consulting or solutions** at Tencent, other leading technology companies, and financial institutions.

He combines experience in financial institutions with hands-on AI product development, building open-source market data tools and multi-agent systems with **17K+ GitHub stars**.

Contact: [simonlin0423@gmail.com](mailto:simonlin0423@gmail.com)

---

## Architecture

```
China A-Share Full-Stack Data · 12-Layer Architecture · V3.8.1
│  (Priority: injoyai/tdx REST → mootdx fallback; Tencent supplements valuation fields)
├── Market Data    injoyai/tdx + mootdx + Tencent + Baidu + Sina    Candlesticks + Order Book + PE/PB + Index/ETF
│                                                     + adjust factors qfq/hfq  ★V3.7
├── Research       Eastmoney + THS + iwencai          Stock reports / Industry reports / PDF / Consensus EPS / NL search
├── Signals        THS + Eastmoney                    Hot stocks + Sector attribution + Northbound flow
│                                                     + Sector membership + Fund flow(push2) + Dragon Tiger + Lockup + Industry + Board fund flow
├── Capital Flow   Eastmoney datacenter + push2       Margin trading + Block trades + Holder count + Dividends + Fund flow(min+120d)
│   / Chips     computed locally                  Chip distribution (CYQ): profit ratio / avg cost / cost range / peak  ★V3.7
├── News           Eastmoney + Cailianpress           Stock news / CLS flash (✅revived in V3.4) / Global finance (mutual backup)
├── Fundamentals   injoyai/tdx + mootdx + Eastmoney + Sina  37-field quarterly + F10 + Financial statements
│               + baostock + SW                  Valuation history (PE/PB/PS + turnover + ST) / listing & delisting / SW industry history  ★V3.7
├── Filings        cninfo + injoyai/tdx/mootdx        Full filings across SSE / SZSE / BSE
├── Limit-Up       Eastmoney push2ex + THS            ZT/ZB/DT/prev-ZT pools / limit reasons / consecutive-board ladder
│                                                     + Watch list pool + Intraday price-anomaly pool  ★V3.6
├── Options        Sina hq.sinajs                     ETF option T-quotes / Greeks / implied volatility  ★V3.3
├── Sentiment      cninfo IRM + THS + Eastmoney       Investor Q&A / hot lists / popularity rank / concept hits  ★V3.3
├── Macro          PBoC + NBS                     Social financing (monthly, 12 cols) / PMI (mfg · non-mfg · composite · by size)
└── Index/Calendar CSI + CNI + SZSE               Constituents / weights / PE & dividend yields / official trading calendar
```

> The 12 layers include a **Backup Sources & Fallback Strategy** appendix: dragon-tiger, fund flow and filings, plus official SSE/SZSE margin data and BSE current quotes with five-level books. See SKILL.md for coverage and source dates.

---

## Quick Start

**3 steps, 2 minutes.**

```bash
# 1. Create skill directory
mkdir -p ~/.claude/skills/a-stock-data

# 2. Download SKILL.md
curl -o ~/.claude/skills/a-stock-data/SKILL.md \
  https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md

# 3. Install Python dependencies
pip install requests pandas stockstats numpy baostock xlrd openpyxl
# Optional fallback client: pip install mootdx
```

Recommended: start the preferred TDX service as well:

```bash
git clone https://github.com/injoyai/tdx.git
cd tdx && go run ./example/HTTPServer
# Set ASTOCK_TDX_URL if it is not at http://127.0.0.1:8080
```

> The example TDX service has no authentication. Keep it on the local machine or a controlled private network; do not expose it directly to the public internet.

Launch Claude Code and say "Check the valuation of 688017" — the skill activates automatically.

> **Codex / OpenClaw users:** Paste the contents of SKILL.md into your system prompt or project context file. The embedded Python code is ready to execute.

---

## 60 Endpoints

There are 55 primary entries and 5 backups. Counts refer to capability entries: CSI/CNI or SSE/SZSE routes within one function count once; helpers and research candidates are excluded.

> **Counting convention:** the tables below have 61 rows but count as 60 capability endpoints — "Eastmoney Industry Reports" shares **the same endpoint** as "Eastmoney reportapi" (only the `qType` parameter differs) and "THS Northbound (historical)" is a local self-built cache (not a separate endpoint), so neither is counted; the single "EM Intraday Anomaly Pool" row covers **two** endpoints (`list` / `count`), adding one back. 61 − 1 − 1 + 1 = 60.

### Market Data (real-time, no IP ban)

| Endpoint | Data |
|----------|------|
| TDX Market Data (injoyai/tdx preferred, mootdx fallback) | Multi-period candlesticks + five-level book + tick-by-tick + real-time quote |
| Tencent Finance | PE(TTM) / PB / Market Cap / Float Cap / Turnover / Price Limits / Index / ETF |
| **Baidu K-line** | Daily K-line + MA5/MA10/MA20 moving averages included (V3.0 new) |
| **Sina Adjust Factors** | qfq / hfq factor series + applying them to unadjusted candles (V3.7 new) |

### Research Reports

| Endpoint | Data |
|----------|------|
| Eastmoney reportapi | Single-stock report list + ratings + 3-year EPS forecasts |
| Eastmoney Industry Reports | Industry report list (qType=1, same endpoint) + industry name/code + rating (V3.2.3) |
| Eastmoney PDF | Full research report PDF, stock & industry (Referer auth handled) |
| THS Consensus EPS | Institutional consensus EPS (direct basic.10jqka.com.cn) |
| iwencai NL Search | Natural language cross-topic report search |

### Signals

| Endpoint | Data |
|----------|------|
| THS Hot Stocks | Today's strong stocks + sector attribution tags (editorial annotations) |
| THS Northbound (real-time) | Shanghai Connect minute-level flow (Shenzhen Connect unreliable since upstream disclosure tightening — see HKEX backup for authoritative data) |
| THS Northbound (historical) | Local self-cached daily history |
| Eastmoney Sector Membership | All sectors a stock belongs to (industry/concept/region mixed) + BK code + daily change + leading stock (V3.2.2, replaced Baidu PAE, one request) |
| **Eastmoney Fund Flow** | Main / Large / Medium / Small / Super-large order minute-level net inflow (V3.1, replaced Baidu PAE) |
| Dragon Tiger Board | Appearance records + Top 5 buy/sell brokerages + institutional activity |
| Daily Dragon Tiger (Full Market) | All stocks on daily board + net buy ranking + appearance reasons |
| Lockup Expiry Calendar | Historical releases + 90-day upcoming expiry alerts |
| **Industry Ranking** | Eastmoney industry change/up/down counts (V3.0, replaced THS 401) |
| **Board Fund Flow** | Industry/concept/region × today/5d/10d main net inflow & ratio + super-large/large/medium/small tiers + leading stock (V3.5, same endpoint as Industry Ranking) |

### Capital Flow / Ownership (V3.0 New)

| Endpoint | Data |
|----------|------|
| **Margin Trading** | Daily margin balance / buy / repay + short selling balance |
| **Block Trades** | Deal price/volume + buyer/seller brokerages + premium rate |
| **Shareholder Count** | Quarterly holder count + QoQ change + avg shares per holder |
| **Dividend History** | Per-share cash dividend / bonus shares / transfer shares |
| **120-Day Fund Flow** | Main / large / medium / small order daily net inflow |
| **Chip Distribution (CYQ)** | Profit ratio / average cost / 90-70 cost range & concentration / chip peak (computed locally, V3.7 new) |

### News

| Endpoint | Data |
|----------|------|
| Stock News | Eastmoney per-stock news (direct search-api-web) |
| CLS Flash | Market-wide real-time flash (v1 API + local signature, zero key, ✅revived in V3.4.0, mutual backup with Global News) |
| Global News | Eastmoney global finance news (direct np-weblist, 7×24) |

### Fundamentals + Filings

| Endpoint | Data |
|----------|------|
| Quarterly Snapshot | 37 fields (EPS / ROE / Net Profit / Revenue...) |
| F10 Company Data | 9 categories (truncation optimization, -70% tokens) |
| Eastmoney Stock Info | Industry / total shares / float / market cap / listing date (direct push2) |
| Sina Financial Statements | Balance sheet / Income statement / Cash flow (direct quotes.sina.cn) |
| cninfo Filings | Full filings across all exchanges |
| **Valuation History** | Daily PE/PB/PS/PCF + turnover + suspension + ST flag (back to 2016; **Beijing Exchange not supported**, V3.7 new) |
| **Listing / Delisting Date** | ipoDate / outDate / status (only zero-auth source for delisting dates, V3.7 new) |
| **SW Industry History** | Every industry reclassification per stock (removes look-ahead bias; codes only, no Chinese names, V3.7 new) |

### Limit-Up / Limit-Down (V3.3 new)

| Endpoint | Data |
|----------|------|
| EM Limit-Up Pool | Consecutive boards / N-day-M-board / seal fund / break count / seal time / industry |
| EM Break-Board Pool | Opened after limit-up + amplitude / speed |
| EM Limit-Down Pool | Seal fund / consecutive limit-down / open count / board turnover |
| EM Prev-Day Limit-Up Pool | Yesterday's limit-up performance today (promotion rate / profit effect) |
| THS Limit-Up Insight | Limit reason themes / seal success rate / board type / seal amount |
| EM Watch List Pool | Exchange risk-warning / watch list + validity window (new in V3.6) |
| EM Intraday Anomaly Pool | Severe price-anomaly detail + per-stock aggregated counts + all 12 anomaly rules decoded (new in V3.6) |

### ETF Options (V3.3 new)

| Endpoint | Data |
|----------|------|
| Option Contract List | 50ETF / 300ETF / STAR50 ETF / 500ETF call & put contracts by month |
| T-Quote | Bid/ask 5 levels / open interest / strike / last / volume |
| Greeks + IV | Delta / Gamma / Theta / Vega / implied vol / theoretical value (exchange-computed, no local BSM) |

### Sentiment & Interaction (V3.3 new)

| Endpoint | Data |
|----------|------|
| Investor Q&A (IRM) | Investor questions + official company replies (unique source: how a company responds to rumors/news) |
| THS Hot List | Popularity / concept tags / rank change |
| EM Popularity Rank | Rank + rank change + name/price |
| EM Stock Concept Hits | Which concepts the market is grouping this stock under + heat |

### Macro (V3.7 new)

| Endpoint | Data |
|----------|------|
| **PBoC Social Financing** | Aggregate Financing to the Real Economy, monthly, 12 columns (RMB/entrusted/trust loans, undiscounted acceptances, corporate & government bonds, equity financing, ABS, write-offs) |
| **NBS PMI** | Manufacturing / non-manufacturing / composite PMI + large / medium / small enterprise breakdown |

### Index Data and Trading Calendar

| Endpoint | Data |
|----------|------|
| Index Constituents | Latest CSI constituents and latest published CNI month-end constituents; actual source dates, no historical membership backfill |
| Index Weights | Latest published CSI/CNI weights in percentage points; dates may differ from constituents |
| Index Valuation | CSI PE and dividend yields under two share-capital conventions; recent file, no PB or full-history guarantee |
| Official Trading Calendar | Complete SZSE calendar month; missing days, unpublished months and unknown flags raise errors |

### Backup Sources (fallback when a primary source fails)

| Endpoint | Data |
|----------|------|
| Official Dragon-Tiger Backup | SSE + SZSE official APIs, zero-auth, authoritative first-party, incl. brokerage seats (when Eastmoney is banned) |
| Fund Flow Backup | Sina daily 4-tier order net flow (super-large / large / medium / small + net inflow) |
| Filings Backup | SZSE official for Shenzhen tickers, Eastmoney for Shanghai, both with direct PDF links (when cninfo is banned) |
| Official Margin Backup | Query SSE/SZSE separately; CNY amounts and share/unit quantities; missing SSE short balance remains null |
| BSE Quote Backup | Board-wide or single-symbol OHLC, volume, amount and five-level snapshot; validates session date; no historical backfill or verified intraday latency |

> Plus a **per-layer primary → independent-backup table** (exchange official / THS F10 / HKEX / cninfo webapi / Jin10 — all on different rate-limit planes) and a "confirmed dead" list — see the "Backup Sources & Fallback Strategy" section in SKILL.md.

### Authentication

All integrated sources except iwencai require no user registration or API key. CSI, CNI and BSE need no user credentials; BSE establishes an anonymous site cookie. Only iwencai semantic search requires an API key ([apply here](https://www.iwencai.com/skillhub)). Optional research candidates are excluded from these capabilities.

---

## Usage Examples

Just tell your AI assistant:

| Scenario | Prompt |
|----------|--------|
| Valuation | "Estimate 688017 — give me PE / PEG / payback period" |
| Sector Attribution | "Which stocks are strong today and what sectors are driving them" |
| Research Reports | "Latest reports on humanoid robot supply chain, especially ball screws and reducers" |
| Northbound Flow | "How's northbound capital flow looking today" |
| Concept Blocks | "What concept sectors does 688017 belong to" |
| Fund Flow | "Is institutional money flowing into or out of 000858 today" |
| Dragon Tiger Board | "Has 002475 appeared on the dragon tiger board recently, which brokerages are buying" |
| Daily Dragon Tiger | "Which stocks had the highest net buy on today's dragon tiger board" |
| Lockup Expiry | "Any lockup expiries coming up in the next 3 months for this stock" |
| Industry Rotation | "Which industries are up the most today, where is money flowing" |
| Margin Trading | "What's the recent trend in margin balance for 600519" |
| Block Trades | "Any recent block trades for this stock, premium or discount" |
| Shareholder Count | "Is 000858 shareholder count increasing or decreasing" |
| Dividends | "How much has Moutai paid in dividends over the years" |
| ETF Quote | "What's the price of 510050 (SSE 50 ETF) and today's change" |
| Limit-Up Sentiment | "How many stocks hit limit-up today, highest consecutive boards, break rate" |
| Limit-Up Themes | "What themes drove today's limit-ups, which are multi-day boards" |
| Watch List Pool | "Which stocks are on the exchange watch list right now, and until when" |
| Intraday Anomalies | "Which stocks had severe price anomalies today, and which rule did they trigger" |
| Anomaly × Watch List | "Of today's anomaly stocks, which are already on the watch list" |
| ETF Options | "What's the implied vol and Delta of the at-the-money 50ETF option" |
| Investor Q&A | "What are investors asking BYD recently and how did the company respond" |
| Market Heat | "Which stocks are hottest today and what concepts are they grouped under" |
| News & Filings | "Pull recent news and filings for 300476" |
| Market Flash | "Any big market news right now on the CLS flash feed" |
| Batch Compare | "Compare valuations of these 5 semiconductor stocks" |
| **Chip Distribution** | "How much of 600519 is in profit, where's the average cost and the chip peak" |
| **Valuation History** | "What percentile is Moutai's PE over the past decade, and show turnover too" |
| **ST / Suspension** | "When was 000004 flagged ST, and has it ever been suspended" |
| **Industry Drift** | "Which SW industry was 000001 in back in 2016 — same as today?" |
| **Macro Backdrop** | "What's the latest social financing and PMI — is liquidity loose or tight" |
| Index Constituents | "List the latest CSI 300 constituents and their source date" |
| Index Weights | "Show the latest published ChiNext weights, preserving their actual date" |
| Index Valuation | "Show recent CSI 300 PE and dividend yields, with both conventions separately" |
| Trading Calendar | "Which days in September 2026 are open, according to SZSE?" |
| Margin Backup | "Eastmoney is unavailable; fetch SSE and SZSE margin data separately for 2026-09-03" |
| BSE Backup | "Fetch the current official BSE snapshot for 920021 and verify its session date" |

### 4 Built-in Research Workflows

| Workflow | What it does | Time |
|----------|-------------|------|
| Single Stock Valuation | Live price → Consensus EPS → Forward PE / PEG / PE payback years | 30 sec |
| Batch Comparison | Side-by-side valuation ranking | 1 min |
| Thematic Research | iwencai multi-keyword NL search + Eastmoney PDF cross-reference | 2 min |
| New Target Research | Coverage → Valuation → Concepts → Fund flow → Dragon tiger → Lockup → Margin | 1 min |

---


## Data Source Priority (V3.8.1)

> **Principle: quotes, K-lines, ticks, financial snapshots and F10 prefer injoyai/tdx REST, with automatic mootdx fallback. Tencent supplements PB, market cap, turnover and price limits. Eastmoney is reserved for exclusive data and routed through `em_get()`.**

| Priority | Source | Protocol | IP Ban Risk | Use |
|----------|--------|----------|-------------|-----|
| **1 (top)** | injoyai/tdx REST (TDX) | Local HTTP → TCP 7709 | **Never banned** | K-line / order book / ticks / financials / F10 |
| **automatic fallback** | mootdx (TDX) | Python → TCP 7709 | **Never banned** | Compatible fallback when the primary service is unavailable |
| **2** | Tencent Finance | HTTP | **Never banned** | Live price / PE / PB / market cap / turnover / index / ETF |
| 3 | THS Hot Stocks / Northbound | HTTP | Very low (zero auth) | Hot stocks / themes / northbound flow |
| 4 | Baidu Finance | HTTP | Very low | K-line (w/ MA5/10/20) |
| 5 | Sina Finance | HTTP | Low | Financial statements |
| 6 | cninfo | HTTP | Low | Filings |
| 7 | THS Consensus EPS | HTTP | Low (UA required) | Consensus EPS |
| 8 | iwencai | OpenAPI | Low (key required) | NL semantic search |
| 9 | **baostock** | TCP | Low (no registration) | Valuation history PE/PB/PS/PCF + turnover + suspension + ST + listing/delisting dates (**no Beijing Exchange**) |
| 10 | **SW Research** | HTTP | Low (public XLS) | Industry classification history |
| 11 | **PBoC** | HTTP | Low (official site) | Aggregate social financing |
| 12 | **NBS** | HTTP | Low (official site) | PMI |
| By data type | **CSI / CNI** | HTTP | Public files; avoid frequent downloads | Constituents/weights and CSI PE/dividend yields |
| Official backups | **SSE / SZSE / BSE** | HTTP | Anonymous access; throttle batch requests | SSE/SZSE margin and BSE current quotes/books, alongside existing exchange backups |
| **last (exclusive only)** | **Eastmoney** datacenter/push2/reportapi/search/np-weblist | HTTP | **Medium — has rate-limit risk** | Dragon-tiger / lockup / margin / block trade / shareholders / dividends / fund flow / reports / news (all via `em_get()`) |

> **Architecture:** injoyai/tdx REST is a local Go protocol service, mootdx is its same-source Python fallback, and baostock is another TCP client. Other sources use direct HTTP APIs. **Eastmoney calls all go through `em_get()` for serial throttling.**
>
> **Fallback:** When a primary source fails, check the "Backup Sources & Fallback Strategy" section in SKILL.md. Some core data types have independent backups on **different domains with separate rate limits**. Not every capability has a backup; always verify dates and completeness after fetching.

---

## FAQ

**Why are index weights not dated today? Can they be used for historical backtests?**
Constituents and weights may be published on different dates. The CNI endpoint returns a month-end snapshot; `date` is the source date. Current membership is not historical membership. This release does not integrate adjustment history or substitute zero for missing index PB.

**How do I run the two new backups?**
Execute the full Layer 12 code block in SKILL.md, then the official margin/BSE backup block. Query margin data separately for `SH` and `SZ`; BSE requires the expected session date. Date mismatches, incomplete pagination and unpublished data raise errors.

**Are easy_tdx and the new official THS API included?**
They are research candidates, not runtime dependencies. Auction integration needs Python 3.10+ compatibility work; the THS service requires a user key. See the [source integration record](docs/source-integration-v3.8.0.md) (Chinese). No installation dependencies were added.

## Verification

`python3 -m unittest discover -s tests -v` extracts the shipped code directly from SKILL.md and checks dates, fields, symbol routing, units, pagination and error propagation. Live tests require explicit `ASTOCK_LIVE_TRADE_DATE` and `ASTOCK_LIVE_MARGIN_DATE` values matching current official data. See the [verification record](docs/source-integration-v3.8.0.md) (Chinese).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).

---

## Disclaimer

This project provides data access tools only and does not constitute investment advice. Investing involves risk.

---

## Support

If this tool saved you time, a coffee is appreciated ☕

<p align="center">
  <a href="https://buymeacoffee.com/simonlin1212"><img src="./assets/bmc-qr.png" width="180" alt="Buy Me a Coffee"></a>
</p>

> Need a data endpoint that isn't here? Open an [Issue](https://github.com/simonlin1212/a-stock-data/issues); sponsors' issues go first.

---

## License

[Apache License 2.0](./LICENSE)

**Author:** Simon Lin · X [@linsizhen](https://x.com/linsizhen) · Email: [simonlin0423@gmail.com](mailto:simonlin0423@gmail.com)
