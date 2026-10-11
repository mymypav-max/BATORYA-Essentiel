<!doctype html>
<html lang="fr" data-theme="light">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>BATORYA Essentiel V6 — Prototype B</title>
<style>
/* ============ TOKENS ============ */
:root{
  --bg:#EDF0F6; --tint:radial-gradient(1100px 480px at 85% -12%, #E0E8FF 0%, rgba(224,232,255,0) 62%);
  --surface:#FFFFFF; --surface2:#F4F6FB; --surface3:#EBEFF7;
  --line:#DFE4EF; --line2:#C9D2E3;
  --ink:#0B1220; --muted:#5A6478; --faint:#96A0B3;
  --accent:#2B4BFF; --accent-hi:#1B36D6; --accent-soft:#E9EEFF; --accent-2:#08A8C6; --accent2-soft:#DFF5FA;
  --ok:#0C9257; --ok-soft:#E1F5EB; --warn:#B57508; --warn-soft:#FBF1DC; --bad:#CE3226; --bad-soft:#FBE6E3;
  --shadow:0 1px 2px rgba(11,18,32,.05),0 8px 24px rgba(11,18,32,.07);
  --glow:0 0 0 3px rgba(43,75,255,.15);
}
html[data-theme="dark"]{
  --bg:#0A0E17; --tint:radial-gradient(1100px 480px at 85% -12%, #14204A 0%, rgba(20,32,74,0) 62%);
  --surface:#121A2E; --surface2:#0E1526; --surface3:#1B2540;
  --line:#222D47; --line2:#30405F;
  --ink:#E9EDF7; --muted:#94A0BA; --faint:#5F6B85;
  --accent:#5D7CFF; --accent-hi:#7B93FF; --accent-soft:#1B2547; --accent-2:#2CCBE8; --accent2-soft:#0F2C38;
  --ok:#3BC585; --ok-soft:#12291F; --warn:#E5A83E; --warn-soft:#2B2110; --bad:#F0685C; --bad-soft:#2F1714;
  --shadow:0 1px 2px rgba(0,0,0,.45),0 12px 32px rgba(0,0,0,.5);
  --glow:0 0 0 3px rgba(93,124,255,.22);
}
/* ============ BASE ============ */
*{box-sizing:border-box;margin:0}
html,body{height:100%}
body{
  font-family:'Inter','SF Pro Text','Segoe UI Variable','Segoe UI',system-ui,sans-serif;
  background:var(--bg);color:var(--ink);font-size:14px;-webkit-font-smoothing:antialiased;overflow:hidden;
}
body::before{content:'';position:fixed;inset:0;background:var(--tint);pointer-events:none;z-index:0}
#app{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column}
.mono{font-family:'JetBrains Mono','SF Mono','Cascadia Code',ui-monospace,monospace;font-variant-numeric:tabular-nums}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:var(--line2);border-radius:99px;border:2px solid var(--bg)}
:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
/* ============ TOP DECK ============ */
.topline{height:3px;flex-shrink:0;background:linear-gradient(90deg,var(--accent),var(--accent-2))}
.top{height:54px;flex-shrink:0;display:flex;align-items:center;gap:8px;padding:0 14px;
  background:color-mix(in srgb,var(--surface) 86%,transparent);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:9px;border:none;background:none;cursor:pointer;padding:4px 8px 4px 2px;border-radius:9px}
.brand:hover{background:var(--surface2)}
.mark{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;font-weight:800;font-size:14px;letter-spacing:-.5px}
html[data-theme="dark"] .mark{color:#0A0E17}
.brandtxt{display:flex;flex-direction:column;align-items:flex-start;line-height:1.15}
.brandtxt b{font-size:14.5px;letter-spacing:-.2px}
.brandtxt i{font-style:normal;font-size:9.5px;color:var(--muted);letter-spacing:.06em}
.chaps{display:flex;align-items:center;gap:2px;flex:1;overflow-x:auto;scrollbar-width:none;padding:0 6px}
.chaps::-webkit-scrollbar{display:none}
.chap{border:none;background:none;cursor:pointer;padding:7px 12px;border-radius:8px;
  font:inherit;font-size:13px;font-weight:500;color:var(--muted);white-space:nowrap;transition:background .12s,color .12s}
.chap:hover{background:var(--surface2);color:var(--ink)}
.chap.on{background:var(--accent-soft);color:var(--accent);font-weight:600}
.tools{display:flex;align-items:center;gap:6px;flex-shrink:0}
.searchbox{display:flex;align-items:center;gap:8px;border:1px solid var(--line2);background:var(--surface);
  border-radius:9px;padding:6px 10px;cursor:pointer;color:var(--faint);font-size:12.5px;min-width:170px}
.searchbox:hover{border-color:var(--accent)}
.searchbox kbd{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:10px;border:1px solid var(--line2);
  border-radius:5px;padding:1px 5px;color:var(--muted);background:var(--surface2)}
.icobtn{position:relative;border:1px solid transparent;background:none;cursor:pointer;color:var(--muted);
  border-radius:9px;padding:7px;display:flex;align-items:center}
.icobtn:hover{background:var(--surface2);color:var(--ink);border-color:var(--line)}
.icobtn .dot{position:absolute;top:6px;right:6px;width:7px;height:7px;border-radius:99px;background:var(--bad);border:1.5px solid var(--surface)}
.profilbtn{display:flex;align-items:center;gap:9px;border:1px solid transparent;background:none;cursor:pointer;
  border-radius:99px;padding:4px 8px 4px 4px}
.profilbtn:hover{background:var(--surface2);border-color:var(--line)}
.profilbtn img{width:30px;height:30px;border-radius:99px;border:1.5px solid var(--line2)}
.ptxt{display:flex;flex-direction:column;align-items:flex-start;line-height:1.15}
.ptxt b{font-size:12.5px}
.ptxt i{font-style:normal;font-size:10px;color:var(--muted)}
/* ============ MODULE BAR ============ */
.mods{flex-shrink:0;display:flex;align-items:center;gap:4px;padding:7px 20px;
  background:var(--surface);border-bottom:1px solid var(--line)}
.modlbl{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-right:10px}
.mod{border:none;background:none;cursor:pointer;font:inherit;font-size:13px;font-weight:500;color:var(--muted);
  padding:7px 12px;border-radius:8px;position:relative}
.mod:hover{background:var(--surface2);color:var(--ink)}
.mod.on{color:var(--ink);font-weight:600;background:var(--surface2)}
.mod.on::after{content:'';position:absolute;left:12px;right:12px;bottom:2px;height:2px;border-radius:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent-2))}
/* ============ CONTENT ============ */
.content{flex:1;overflow:auto;padding:22px 28px 96px}
.wrap{max-width:1240px;margin:0 auto;animation:fade .18s ease}
@keyframes fade{from{opacity:0;transform:translateY(3px)}}
.ph{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:18px;flex-wrap:wrap}
h1{font-size:21px;font-weight:750;letter-spacing:-.3px}
.sub{color:var(--muted);font-size:13px;margin-top:4px}
.crumb{display:inline-flex;align-items:center;gap:5px;border:none;background:none;cursor:pointer;color:var(--muted);font:inherit;font-size:12.5px;padding:4px 7px;border-radius:7px}
.crumb:hover{background:var(--surface2);color:var(--ink)}
.crumbs{display:flex;align-items:center;gap:6px;margin-bottom:14px;font-size:12.5px;color:var(--faint)}
.crumbs b{color:var(--ink);font-weight:600}
/* ============ SURFACES ============ */
.card{background:var(--surface);border:1px solid var(--line);border-radius:13px;box-shadow:var(--shadow)}
.card .pad{padding:16px 18px}
.k{padding:15px 17px}
.lbl{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);font-weight:600}
.big{font-size:26px;font-weight:750;letter-spacing:-.5px}
.grid{display:grid;gap:14px}
.k4{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.c2{grid-template-columns:1.5fr 1fr;align-items:start}
@media (max-width:960px){.c2{grid-template-columns:1fr}}
.tile{cursor:pointer;transition:transform .13s,border-color .13s}
.tile:hover{transform:translateY(-2px);border-color:var(--accent)}
/* ============ BUTTONS / INPUTS ============ */
.btn{display:inline-flex;align-items:center;gap:7px;padding:8px 14px;border-radius:9px;cursor:pointer;
  border:1px solid var(--line2);background:var(--surface);color:var(--ink);font:inherit;font-size:13.5px;font-weight:600;
  transition:background .12s,border-color .12s}
.btn:hover{background:var(--surface2);border-color:var(--accent)}
.btn.pri{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 1px 2px rgba(11,18,32,.2),0 4px 14px rgba(43,75,255,.3)}
html[data-theme="dark"] .btn.pri{color:#0A0E17}
.btn.pri:hover{background:var(--accent-hi);border-color:var(--accent-hi)}
.btn.sm{padding:5px 10px;font-size:12.5px;border-radius:8px}
.btn.ghost{border-color:transparent;background:none;color:var(--muted)}
.btn.ghost:hover{background:var(--surface2);color:var(--ink)}
.btn:disabled{opacity:.45;cursor:not-allowed}
.in{width:100%;background:var(--surface);border:1px solid var(--line2);border-radius:9px;padding:8px 12px;
  font:inherit;font-size:13.5px;color:var(--ink)}
.in:focus{border-color:var(--accent);box-shadow:var(--glow);outline:none}
.in:disabled{opacity:.5;background:var(--surface2)}
textarea.in{resize:vertical;min-height:70px}
label.fl{display:block;font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);margin:0 0 6px}
.field{margin-bottom:13px}
.srch{position:relative;flex:0 0 270px}
.srch svg{position:absolute;left:11px;top:9.5px;color:var(--faint)}
.srch .in{padding-left:34px}
/* ============ STATUS CHIPS ============ */
.st{display:inline-flex;align-items:center;gap:6px;padding:3px 9px 3px 7px;border-radius:99px;
  font-size:11px;font-weight:650;letter-spacing:.02em;white-space:nowrap}
.st::before{content:'';width:6px;height:6px;border-radius:99px;background:currentColor;flex-shrink:0}
.st.ok{color:var(--ok);background:var(--ok-soft)}
.st.warn{color:var(--warn);background:var(--warn-soft)}
.st.bad{color:var(--bad);background:var(--bad-soft)}
.st.acc{color:var(--accent);background:var(--accent-soft)}
.st.info{color:var(--accent-2);background:var(--accent2-soft)}
.st.gray{color:var(--muted);background:var(--surface3)}
/* filter chips */
.chip{border:1px solid var(--line2);background:var(--surface);color:var(--muted);border-radius:99px;
  padding:6px 12px;font:inherit;font-size:12.5px;cursor:pointer;white-space:nowrap}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
html[data-theme="dark"] .chip.on{color:#0A0E17}
/* ============ TABLES ============ */
.tblwrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:13.5px}
.tbl th{text-align:left;font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);
  font-weight:600;padding:10px 14px;border-bottom:1px solid var(--line)}
.tbl td{padding:11px 14px;border-bottom:1px solid var(--line)}
.tbl tr:last-child td{border-bottom:none}
.tbl tbody tr{cursor:pointer;transition:background .1s}
.tbl tbody tr:hover{background:var(--accent-soft)}
.num{text-align:right}
td.num{font-family:'JetBrains Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums}
.empty{padding:34px;text-align:center;color:var(--faint)}
/* ============ MISC ============ */
.row{display:flex;align-items:center;gap:10px}
.spread{display:flex;align-items:center;justify-content:space-between;gap:12px}
.muted{color:var(--muted)}
.note{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);
  background:var(--surface3);border-radius:7px;padding:4px 9px}
.bar{height:6px;border-radius:99px;background:var(--surface3);overflow:hidden}
.bar>div{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--accent-2))}
.sparks{display:flex;align-items:flex-end;gap:3px;height:28px}
.sparks i{flex:1;border-radius:2px 2px 0 0;background:var(--accent);opacity:.25;min-width:4px}
.sparks i:last-child{opacity:1}
.divider{width:1px;background:var(--line2)}
/* ============ PROFILE MENU ============ */
.pmenu{position:fixed;top:62px;right:16px;width:236px;background:var(--surface);border:1px solid var(--line2);
  border-radius:13px;box-shadow:var(--shadow);padding:6px;z-index:80;animation:pop .14s ease}
.mi{display:flex;align-items:center;gap:10px;width:100%;padding:9px 11px;border:none;background:none;
  cursor:pointer;border-radius:8px;font:inherit;font-size:13.5px;color:var(--ink);text-align:left}
.mi:hover{background:var(--surface2)}
.mi.danger{color:var(--bad)}
.msep{height:1px;background:var(--line);margin:5px 8px}
@keyframes pop{from{opacity:0;transform:translateY(-5px)}to{opacity:1}}
/* ============ LEON ============ */
.leonfab{position:fixed;bottom:22px;right:22px;width:52px;height:52px;border-radius:99px;border:none;cursor:pointer;
  display:flex;align-items:center;justify-content:center;color:#fff;z-index:90;
  background:linear-gradient(135deg,var(--accent),var(--accent-2));box-shadow:0 6px 22px rgba(43,75,255,.45);
  transition:transform .15s}
html[data-theme="dark"] .leonfab{color:#0A0E17}
.leonfab:hover{transform:scale(1.08)}
.leonfab::after{content:'';position:absolute;inset:-4px;border-radius:99px;border:1.5px solid var(--accent);
  animation:ring 2.6s ease-out infinite;opacity:0}
@keyframes ring{0%{transform:scale(.85);opacity:.55}70%{transform:scale(1.18);opacity:0}100%{opacity:0}}
.leonp{position:fixed;bottom:86px;right:22px;width:370px;height:470px;background:var(--surface);border:1px solid var(--line2);
  border-radius:16px;box-shadow:0 20px 55px rgba(0,0,0,.3);display:flex;flex-direction:column;z-index:90;
  animation:pop .16s ease;overflow:hidden}
.leonh{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--line)}
.leonh .orb{width:30px;height:30px;border-radius:99px;display:flex;align-items:center;justify-content:center;color:#fff;
  background:linear-gradient(135deg,var(--accent),var(--accent-2))}
html[data-theme="dark"] .leonh .orb{color:#0A0E17}
.lmsg{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:9px}
.lm{max-width:84%;padding:10px 13px;border-radius:13px;font-size:13.5px;line-height:1.5}
.lm.bot{background:var(--surface2);border:1px solid var(--line);border-bottom-left-radius:5px}
.lm.me{align-self:flex-end;background:var(--accent);color:#fff;border-bottom-right-radius:5px}
html[data-theme="dark"] .lm.me{color:#0A0E17}
.leonc{padding:10px 12px;border-top:1px solid var(--line)}
.leonc .qs{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;margin-bottom:9px}
/* ============ CALENDAR ============ */
.calhead{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}
.calhead span{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);font-weight:600;text-align:center}
.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
.day{min-height:92px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:7px;font-size:12px}
.day.off{opacity:.35}
.day.today{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.day b{font-size:11.5px;color:var(--muted);font-weight:600}
.day.today b{color:var(--accent)}
.ev{border-radius:6px;padding:3px 6px;font-size:10.5px;font-weight:600;margin-top:4px;cursor:pointer;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ev-a{background:var(--accent-soft);color:var(--accent)}
.ev-b{background:var(--accent2-soft);color:var(--accent-2)}
.ev-w{background:var(--warn-soft);color:var(--warn)}
.ev-g{background:var(--ok-soft);color:var(--ok)}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px}
.legend span{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--muted)}
.legend i{width:10px;height:10px;border-radius:3px}
/* theme cards */
.tc{flex:1;border:1px solid var(--line2);border-radius:12px;cursor:pointer;padding:12px;text-align:left;background:var(--surface);position:relative}
.tc.on{border-color:var(--accent);box-shadow:var(--glow)}
.tc .prev{height:64px;border-radius:8px;padding:8px;display:flex;flex-direction:column;gap:5px;margin-bottom:9px;border:1px solid var(--line)}
.tc .prev i{display:block;height:6px;border-radius:3px}
.tc.on .tick{position:absolute;top:10px;right:10px;color:var(--accent)}
/* toast */
.toast{position:fixed;bottom:22px;left:22px;background:var(--ink);color:var(--bg);padding:12px 17px;
  border-radius:11px;font-size:13.5px;max-width:430px;z-index:100;box-shadow:0 10px 30px rgba(0,0,0,.35);animation:pop .15s ease}
@media (max-width:1080px){.searchbox{display:none}.brandtxt i{display:none}}
@media (max-width:760px){.ptxt{display:none}.content{padding:16px 14px 90px}}
</style>
</head>
<body>
<div id="app"></div>
<script>
'use strict';
/* ================================================================
   BATORYA Essentiel V6 — Prototype B « Cobalt Graphite »
   Fichier autonome : HTML + CSS + JS, données 100 % fictives,
   aucune connexion réseau, aucune donnée réelle enregistrée.
   ================================================================ */

/* ---------- Icônes SVG (trait) ---------- */
const P = {
  home:'M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5',
  users:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 .01M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  doc:'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h5',
  hard:'M2 20h20M4 20V10l8-6 8 6v10M9 20v-5h6v5',
  invoice:'M6 2h12v20l-3-2-3 2-3-2-3 2zM9 7h6M9 11h6M9 15h3',
  wallet:'M20 12V8H6a2 2 0 0 1 0-4h12v4M4 6v12a2 2 0 0 0 2 2h14v-4M18 12a2 2 0 0 0 0 4h4v-4z',
  book:'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5z',
  folder:'M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z',
  calendar:'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z',
  gear:'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 3 15a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.4-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 10 4.6a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 21 11a2 2 0 1 1 0 4z',
  search:'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3',
  plus:'M12 5v14M5 12h14', chevL:'M15 18l-6-6 6-6', chevR:'M9 18l6-6-6-6', chevD:'M6 9l6 6 6-6',
  x:'M18 6 6 18M6 6l12 12', bell:'M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0',
  sun:'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4',
  moon:'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z',
  phone:'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z',
  mail:'M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM22 6l-10 7L2 6',
  pin:'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0zM12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  check:'M20 6 9 17l-5-5', clock:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2',
  download:'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  spark:'M12 2l1.9 5.8L20 9.7l-5.8 1.9L12 18l-1.9-6.4L4 9.7l6.1-1.9z',
  send:'M22 2 11 13M22 2l-7 20-4-9-9-4z', lock:'M5 11h14v11H5zM8 11V7a4 4 0 0 1 8 0v4',
  info:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 16v-4M12 8h.01',
  edit:'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4z',
  euro:'M18 7a7 7 0 1 0 0 10M3 10h11M3 14h11',
  trash:'M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6'
};
function ic(n,s){s=s||16;return '<svg width="'+s+'" height="'+s+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="'+P[n]+'"/></svg>';}
const eur = n => n.toLocaleString('fr-FR') + ' \u20AC';

/* ---------- Avatar fictif (SVG embarqué, aucune connexion) ---------- */
const AVATAR = 'data:image/svg+xml,' + encodeURIComponent(
'<svg xmlns="http://www.w3.org/2000/svg" width="168" height="168"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2B4BFF"/><stop offset="1" stop-color="#08A8C6"/></linearGradient></defs><rect width="168" height="168" fill="url(#g)"/><circle cx="84" cy="64" r="30" fill="#EAF0FF"/><path d="M28 168c6-38 28-56 56-56s50 18 56 56z" fill="#EAF0FF"/></svg>');

/* ---------- Données fictives cohérentes ---------- */
const USER = { name:'Rémy Pavy', company:'Pavy Plomberie', role:'Plombier-chauffagiste — EI',
  email:'contact@pavy-plomberie.fr', phone:'06 12 34 56 78', siret:'912 345 678 00019' };

const CLIENTS = [
 {id:'C-001',name:'Marie Bertrand',type:'Particulier',city:'Nantes',addr:'12 rue des Lilas, 44000 Nantes',phone:'06 11 22 33 44',email:'marie.bertrand@email.fr',since:'Mars 2024',docs:6,status:'client',notes:'Chaudière gaz entretenue chaque année. Préfère être jointe le matin.'},
 {id:'C-002',name:'Gérard Dupont',type:'Particulier',city:'Rezé',addr:'8 allée des Chênes, 44400 Rezé',phone:'06 55 44 33 22',email:'g.dupont@email.fr',since:'Janv. 2025',docs:3,status:'client'},
 {id:'C-003',name:'SCI Bellevue',type:'Professionnel',city:'Saint-Herblain',addr:'45 rue de la Loire, 44800 St-Herblain',phone:'02 40 55 12 12',email:'gestion@sci-bellevue.fr',since:'Sept. 2023',docs:11,status:'client'},
 {id:'C-004',name:'Sophie Lambert',type:'Particulier',city:'Orvault',addr:'3 impasse du Bocage, 44700 Orvault',phone:'07 88 99 00 11',email:'sophie.l@email.fr',since:'Juin 2025',docs:2,status:'client'},
 {id:'C-005',name:'Boulangerie Maison Léon',type:'Professionnel',city:'Nantes',addr:'27 pl. du Commerce, 44000 Nantes',phone:'02 40 12 34 56',email:'contact@maison-leon.fr',since:'—',docs:1,status:'prospect',notes:'Prospect rencontré au salon. Demande de devis robinetterie + lave-vaisselle.'},
 {id:'C-006',name:'Karim Haddad',type:'Particulier',city:'Vertou',addr:'15 rue de la Garenne, 44120 Vertou',phone:'06 77 88 99 10',email:'k.haddad@email.fr',since:'Févr. 2026',docs:2,status:'prospect'}
];

const DEVIS = [
 {id:'DEV-2026-021',client:'SCI Bellevue',date:'02/10/2026',amount:4820,status:'sent',chantier:null},
 {id:'DEV-2026-020',client:'Boulangerie Maison Léon',date:'01/10/2026',amount:2350,status:'draft',chantier:null},
 {id:'DEV-2026-018',client:'Karim Haddad',date:'26/09/2026',amount:1890,status:'accepted',chantier:'CH-2026-008'},
 {id:'DEV-2026-017',client:'Marie Bertrand',date:'22/09/2026',amount:760,status:'accepted',chantier:'CH-2026-007'},
 {id:'DEV-2026-015',client:'Sophie Lambert',date:'15/09/2026',amount:1240,status:'expired',chantier:null},
 {id:'DEV-2026-012',client:'Gérard Dupont',date:'05/09/2026',amount:940,status:'accepted',chantier:'CH-2026-006'}
];
const devisSt = {sent:['Envoyé','info'],draft:['Brouillon','gray'],accepted:['Accepté','ok'],expired:['Expiré','warn'],refused:['Refusé','bad']};

const CHANTIERS = [
 {id:'CH-2026-008',client:'Karim Haddad',title:'Remplacement chaudière + mise aux normes',start:'05/10/2026',end:'09/10/2026',progress:70,status:'active',devis:'DEV-2026-018',amount:1890},
 {id:'CH-2026-007',client:'Marie Bertrand',title:'Réparation fuite + robinetterie SdB',start:'03/10/2026',end:'04/10/2026',progress:100,status:'done',devis:'DEV-2026-017',amount:760},
 {id:'CH-2026-006',client:'Gérard Dupont',title:'Installation radiateurs (4 pièces)',start:'12/10/2026',end:'16/10/2026',progress:0,status:'planned',devis:'DEV-2026-012',amount:940},
 {id:'CH-2026-005',client:'SCI Bellevue',title:'Entretien annuel immeuble (12 logts)',start:'20/09/2026',end:'21/09/2026',progress:100,status:'done',devis:'DEV-2026-009',amount:2160}
];
const chantSt = {active:['En cours','acc'],planned:['Planifié','info'],done:['Terminé','ok']};

const FACTURES = [
 {id:'F-2026-034',client:'SCI Bellevue',date:'22/09/2026',due:'22/10/2026',amount:2160,paid:2160,status:'paid',chantier:'CH-2026-005'},
 {id:'F-2026-032',client:'Marie Bertrand',date:'04/10/2026',due:'03/11/2026',amount:760,paid:380,status:'partial',chantier:'CH-2026-007'},
 {id:'F-2026-029',client:'Boulangerie Maison Léon',date:'18/08/2026',due:'17/09/2026',amount:1450,paid:0,status:'late',chantier:null},
 {id:'F-2026-025',client:'SCI Bellevue',date:'05/06/2026',due:'05/07/2026',amount:320,paid:320,status:'paid',chantier:null}
];
const factSt = {paid:['Réglée','ok'],partial:['Partielle','warn'],late:['Impayée','bad'],sent:['Émise','info']};

const PRESTATIONS = [
 {ref:'P-001',name:'Remplacement chaudière gaz condensation',unit:'forfait',price:2450,cat:'Chauffage'},
 {ref:'P-002',name:'Dépose ancienne chaudière + évacuation',unit:'forfait',price:280,cat:'Chauffage'},
 {ref:'P-003',name:'Pose radiateur acier 1500W',unit:'u',price:210,cat:'Chauffage'},
 {ref:'P-004',name:'Entretien annuel chaudière',unit:'u',price:130,cat:'Maintenance'},
 {ref:'P-005',name:'Recherche de fuite',unit:'h',price:65,cat:'Plomberie'},
 {ref:'P-006',name:'Remplacement robinet mélangeur',unit:'u',price:95,cat:'Plomberie'},
 {ref:'P-007',name:'Main d\u2019œuvre (taux horaire)',unit:'h',price:55,cat:'Main d\u2019œuvre'},
 {ref:'P-008',name:'Déplacement zone 1 (Nantes agglo)',unit:'forfait',price:25,cat:'Main d\u2019œuvre'},
 {ref:'P-009',name:'Installation lave-vaisselle',unit:'forfait',price:150,cat:'Plomberie'},
 {ref:'P-010',name:'Purge circuit chauffage',unit:'h',price:60,cat:'Chauffage'}
];

const EVENTS = [
 {date:'2026-10-05',label:'Chaudière Haddad — début',type:'ev-a'},
 {date:'2026-10-06',label:'Chantier chaudière Haddad',type:'ev-a'},
 {date:'2026-10-07',label:'Chantier chaudière Haddad',type:'ev-a'},
 {date:'2026-10-08',label:'Point client Haddad',type:'ev-b'},
 {date:'2026-10-09',label:'Chaudière Haddad — fin',type:'ev-a'},
 {date:'2026-10-10',label:'Relance devis Maison Léon',type:'ev-w'},
 {date:'2026-10-12',label:'Radiateurs Dupont — début',type:'ev-a'},
 {date:'2026-10-14',label:'Relance facture F-2026-029',type:'ev-w'},
 {date:'2026-10-16',label:'Radiateurs Dupont — fin',type:'ev-a'},
 {date:'2026-10-20',label:'Entretien annuel Bertrand',type:'ev-g'},
 {date:'2026-10-24',label:'Rappel encaissements',type:'ev-w'}
];
const MOVES = [
 {l:'Acompte Bertrand',v:'+380',s:'ok',d:'05/10/2026 · Virement'},
 {l:'HeatingPro — chaudière Haddad',v:'-780',s:'bad',d:'04/10/2026 · CB pro'},
 {l:'SCI Bellevue — solde entretien',v:'+2160',s:'ok',d:'22/09/2026 · Virement'},
 {l:'Frise Matériaux — radiateurs',v:'-460',s:'bad',d:'20/09/2026 · Virement'}
];

/* ---------- Architecture : les 9 chapitres officiels ---------- */
const CHAPTERS = [
 {id:'crm',label:'CRM',modules:[['clients','Clients & prospects'],['prospects','Prospects']]},
 {id:'commerce',label:'Commerce',modules:[['devis','Devis'],['bons','Bons de commande']]},
 {id:'travaux',label:'Travaux',modules:[['chantiers','Chantiers']]},
 {id:'facturation',label:'Facturation',modules:[['factures','Factures'],['avoirs','Avoirs & acomptes']]},
 {id:'tresorerie',label:'Trésorerie',modules:[['flux','Flux & dépenses'],['echeances','Échéances']]},
 {id:'catalogue',label:'Catalogue',modules:[['prestations','Prestations']]},
 {id:'documents',label:'Documents',modules:[['docs','Tous les documents']]},
 {id:'planification',label:'Planification',modules:[['calendrier','Calendrier'],['chrono','Chronologie']]},
 {id:'parametres',label:'Paramètres',modules:[['prefs','Préférences'],['entreprise','Entreprise'],['donnees','Données & licence']]}
];

/* ---------- État global ---------- */
const state = {
  chapter:null, module:null, page:null, pageId:null,
  theme:'light', profile:false, leon:false, leonMsgs:[
    {w:'bot',t:'Bonjour Rémy ! Je suis Léon, votre assistant intégré. Je fonctionne entièrement sur cet ordinateur : vos données ne quittent jamais BATORYA.'}
  ],
  search:'', filter:'all', cat:'Tout', ffilter:'all',
  picker:false, edit:false, cal:0, refocus:null, toast:null
};
let devisLines = [
  {ref:'P-001',name:'Remplacement chaudière gaz condensation',qty:1,unit:'forfait',price:2450},
  {ref:'P-002',name:'Dépose ancienne chaudière + évacuation',qty:1,unit:'forfait',price:280}
];
let toastTimer = null;

/* ---------- Utilitaires ---------- */
function toast(msg){ state.toast = msg; clearTimeout(toastTimer); render();
  toastTimer = setTimeout(()=>{ state.toast = null; render(); }, 3400); }
function go(chapter, module){
  state.chapter = chapter; state.module = module; state.page = null; state.pageId = null;
  state.search = ''; state.filter = 'all'; state.cat = 'Tout'; state.ffilter = 'all';
  state.picker = false; state.profile = false; state.refocus = null; render();
}
function applyTheme(){ document.documentElement.dataset.theme = state.theme; render(); }

/* ---------- Léon ---------- */
function leonReply(q){
  if (/devis/i.test(q)) return {t:'Vous avez 3 devis en attente. Le devis DEV-2026-021 (SCI Bellevue, 4 820 €) mérite une relance. J\u2019ouvre le module Devis.',go:['commerce','devis']};
  if (/fact|pay|encaiss|d[oû]/i.test(q)) return {t:'Restant dû : 1 830 €. La facture F-2026-029 (1 450 €) est en retard depuis le 17/09. J\u2019ouvre la facturation.',go:['facturation','factures']};
  if (/chantier|travaux/i.test(q)) return {t:'1 chantier en cours : chaudière Haddad (70 %). 1 chantier planifié la semaine prochaine. J\u2019ouvre le suivi.',go:['travaux','chantiers']};
  if (/client/i.test(q)) return {t:'6 fiches : 4 clients et 2 prospects. Marie Bertrand attend un solde de 380 €.'};
  return {t:'Je peux vous aider à retrouver un document, préparer un devis ou suivre vos encaissements. Que souhaitez-vous faire ?'};
}
function askLeon(q){
  if(!q || !q.trim()) return;
  state.leonMsgs.push({w:'me',t:q.trim()});
  const r = leonReply(q.trim());
  state.leonMsgs.push({w:'bot',t:r.t});
  if(r.go) setTimeout(()=>go(r.go[0], r.go[1]), 800);
  render();
}

/* ---------- Fragments réutilisables ---------- */
const stChip = (txt, tone) => '<span class="st '+tone+'">'+txt+'</span>';
const crumbs = (chLabel, modId, pageLabel) =>
  '<div class="crumbs"><button class="crumb" data-act="module" data-ch="'+state.chapter+'" data-mod="'+modId+'">'+ic('chevL',12)+chLabel+'</button><span>/</span><b>'+pageLabel+'</b></div>';
const todoItem = (icon, tone, title, desc, actLabel, act) =>
  '<div class="row" style="align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--line)">'+
  '<span class="st '+tone+'" style="padding:6px">'+ic(icon,12)+'</span>'+
  '<div style="flex:1"><div style="font-weight:600;font-size:13.5px">'+title+'</div><div class="muted" style="font-size:12.5px">'+desc+'</div></div>'+
  '<button class="btn sm" data-act="'+act.a+'" '+(act.p||'')+'>'+actLabel+'</button></div>';

/* ================================================================
   VUES
   ================================================================ */
function vHome(){
  return `
  <div class="card pad" style="margin-bottom:16px">
    <div class="spread" style="flex-wrap:wrap;gap:16px">
      <div>
        <h1>Bonjour Rémy</h1>
        <p class="sub">Dimanche 11 octobre 2026 — vue d'ensemble de votre activité.</p>
        <div class="row" style="margin-top:13px">
          <button class="btn pri" data-act="page" data-page="devis-edit">${ic('plus',14)}Créer un devis</button>
          <button class="btn" data-act="toast" data-msg="Formulaire « Nouveau client » — démonstration, aucune donnée enregistrée.">${ic('users',14)}Nouveau client</button>
          <button class="btn" data-act="toast" data-msg="Facture vierge prête (simulation) — sélectionnez d'abord un chantier ou un client.">${ic('invoice',14)}Facturer un chantier</button>
        </div>
      </div>
      <div class="row" style="gap:22px">
        <div><span class="lbl">À encaisser</span><div class="big mono">1 830 €</div><span class="st warn">3 factures ouvertes</span></div>
        <div class="divider" style="align-self:stretch"></div>
        <div><span class="lbl">En retard</span><div class="big mono" style="color:var(--bad)">1 450 €</div><span class="st bad">F-2026-029</span></div>
      </div>
    </div>
  </div>

  <div class="grid k4" style="margin-bottom:16px">
    <div class="card k tile" data-act="module" data-ch="commerce" data-mod="devis">
      <div class="spread"><span class="lbl">Devis en attente</span>${ic('doc',14)}</div>
      <div class="big mono">3</div>
      <div class="sparks"><i style="height:30%"></i><i style="height:55%"></i><i style="height:45%"></i><i style="height:70%"></i><i style="height:100%"></i></div>
    </div>
    <div class="card k tile" data-act="module" data-ch="travaux" data-mod="chantiers">
      <div class="spread"><span class="lbl">Chantier en cours</span>${ic('hard',14)}</div>
      <div class="big mono">1</div>
      <div class="muted" style="font-size:12px">Chaudière Haddad · 70 %</div>
    </div>
    <div class="card k tile" data-act="module" data-ch="tresorerie" data-mod="flux">
      <div class="spread"><span class="lbl">Encaissé en octobre</span>${ic('wallet',14)}</div>
      <div class="big mono">2 860 €</div>
      <div class="muted" style="font-size:12px">+ 18 % vs septembre</div>
    </div>
    <div class="card k tile" data-act="module" data-ch="planification" data-mod="calendrier">
      <div class="spread"><span class="lbl">Semaine du 12</span>${ic('calendar',14)}</div>
      <div class="big mono">2</div>
      <div class="muted" style="font-size:12px">interventions planifiées</div>
    </div>
  </div>

  <div class="grid c2">
    <div class="card pad">
      <div class="spread" style="margin-bottom:8px"><h2 style="font-size:15px">À traiter</h2>
        <button class="btn ghost sm" data-act="module" data-ch="tresorerie" data-mod="echeances">Tout voir</button></div>
      ${todoItem('clock','warn','Relancer la facture F-2026-029','Boulangerie Maison Léon — 1 450 € en retard depuis le 17/09','Ouvrir',{a:'page',p:'data-page="facture" data-id="F-2026-029"'})}
      ${todoItem('doc','info','Devis DEV-2026-020 à finaliser','Boulangerie Maison Léon — brouillon depuis le 01/10','Modifier',{a:'page',p:'data-page="devis-edit"'})}
      ${todoItem('phone','acc','Appeler Sophie Lambert','Devis robinetterie expiré le 15/09 — relance courtoise conseillée','Simuler',{a:'toast',p:'data-msg="Appel simulé — le logiciel compose le numéro en local, sans service distant."'})}
      ${todoItem('check','ok','Solder la facture F-2026-032','Marie Bertrand — acompte de 380 € reçu, reste 380 €','Ouvrir',{a:'page',p:'data-page="facture" data-id="F-2026-032"'})}
    </div>
    <div class="grid" style="align-items:start">
      <div class="card pad">
        <h2 style="font-size:15px;margin-bottom:10px">Semaine prochaine</h2>
        <div class="row" style="gap:10px;padding:7px 0"><span class="ev ev-a mono" style="margin:0">12</span><span style="font-size:13px">Radiateurs Dupont — démarrage</span></div>
        <div class="row" style="gap:10px;padding:7px 0;border-top:1px solid var(--line)"><span class="ev ev-w mono" style="margin:0">14</span><span style="font-size:13px">Relance F-2026-029</span></div>
        <div class="row" style="gap:10px;padding:7px 0;border-top:1px solid var(--line)"><span class="ev ev-a mono" style="margin:0">16</span><span style="font-size:13px">Radiateurs Dupont — fin</span></div>
        <button class="btn sm" style="width:100%;justify-content:center;margin-top:11px" data-act="module" data-ch="planification" data-mod="calendrier">Ouvrir la planification</button>
      </div>
      <div class="card pad">
        <h2 style="font-size:15px;margin-bottom:6px">Derniers documents</h2>
        ${[['F-2026-032','Facture — M. Bertrand','Partielle','warn'],['DEV-2026-021','Devis — SCI Bellevue','Envoyé','info'],['DEV-2026-020','Devis — Maison Léon','Brouillon','gray']].map(d=>`
          <div class="row" style="padding:9px 0;border-bottom:1px solid var(--line);cursor:pointer" data-act="toast" data-msg="Ouverture du PDF « ${d[0]} » simulée — fichier local fictif.">
            <span class="muted">${ic('doc',15)}</span>
            <div style="flex:1;font-size:13px">${d[1]}<div class="muted mono" style="font-size:10.5px">${d[0]}</div></div>
            ${stChip(d[2],d[3])}
          </div>`).join('')}
      </div>
    </div>
  </div>`;
}

/* ---------- CRM ---------- */
function vClients(){
  const list = CLIENTS.filter(c => (state.filter==='all'||c.status===state.filter) &&
    (c.name+' '+c.city).toLowerCase().includes(state.search.toLowerCase()));
  return `
  <div class="ph"><div><h1>Clients & prospects</h1><p class="sub">6 fiches enregistrées sur cet ordinateur — aucune synchronisation distante.</p></div>
    <button class="btn pri" data-act="toast" data-msg="Fiche « Nouveau client » (démonstration) — rien n'est enregistré.">${ic('plus',14)}Nouveau client</button></div>
  <div class="row" style="margin-bottom:14px;flex-wrap:wrap">
    <div class="srch">${ic('search',15)}<input class="in" placeholder="Rechercher un nom, une ville…" data-search="clients" value="${state.search}"/></div>
    ${[['all','Tous'],['client','Clients'],['prospect','Prospects']].map(f=>'<button class="chip '+(state.filter===f[0]?'on':'')+'" data-act="filter" data-f="'+f[0]+'">'+f[1]+'</button>').join('')}
  </div>
  <div class="card tblwrap">
    <table class="tbl"><thead><tr><th>Nom</th><th>Type</th><th>Ville</th><th>Téléphone</th><th>Depuis</th><th>Statut</th></tr></thead>
    <tbody>${list.map(c=>`
      <tr data-act="${c.id==='C-001'?'page':'toast'}" ${c.id==='C-001'?'data-page="client"':'data-msg="Démonstration : seule la fiche de Marie Bertrand est détaillée."'}>
        <td><b>${c.name}</b><div class="muted mono" style="font-size:10.5px">${c.id}</div></td>
        <td class="muted">${c.type}</td><td>${c.city}</td><td class="muted">${c.phone}</td><td class="muted">${c.since}</td>
        <td>${stChip(c.status==='client'?'Client':'Prospect',c.status==='client'?'ok':'warn')}</td>
      </tr>`).join('')}
      ${list.length===0?'<tr><td colspan="6" class="empty">Aucun résultat. Essayez un autre nom ou filtre.</td></tr>':''}
    </tbody></table>
  </div>`;
}

function vProspects(){
  const ps = CLIENTS.filter(c=>c.status==='prospect');
  return `
  <div class="ph"><h1>Prospects</h1><p class="sub">Contacts en phase de devis, sans engagement en cours.</p></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">
    ${ps.map(p=>`
    <div class="card pad">
      <div class="spread"><div><b style="font-size:15px">${p.name}</b><div class="muted" style="font-size:12.5px">${p.type} · ${p.city}</div></div>
      ${stChip('Prospect','warn')}</div>
      <div class="row" style="gap:14px;margin:11px 0 7px;font-size:12.5px;color:var(--muted)">
        <span class="row" style="gap:5px">${ic('phone',13)}${p.phone}</span><span class="row" style="gap:5px">${ic('mail',13)}${p.email}</span></div>
      ${p.notes?'<p class="muted" style="font-size:12.5px;margin:4px 0 12px">'+p.notes+'</p>':''}
      <div class="row"><button class="btn sm pri" data-act="page" data-page="devis-edit">${ic('plus',13)}Devis</button>
        <button class="btn ghost sm" data-act="toast" data-msg="Fiche prospect ${p.id} — édition simulée.">${ic('edit',13)}Fiche</button></div>
    </div>`).join('')}
  </div>`;
}

function vClient(){
  const c = CLIENTS[0];
  return `
  ${crumbs('CRM','clients',c.name)}
  <div class="card pad" style="margin-bottom:16px">
    <div class="spread" style="flex-wrap:wrap;gap:14px">
      <div class="row" style="gap:15px">
        <img src="${AVATAR}" alt="Avatar fictif" style="width:76px;height:76px;border-radius:18px;border:1px solid var(--line2)"/>
        <div>
          <h1 style="margin:0 0 3px">${c.name}</h1>
          <div class="muted" style="font-size:13px">${c.id} · Client depuis ${c.since}</div>
          <div class="row" style="margin-top:9px">${stChip('Client actif','ok')}${stChip(c.docs+' documents','gray')}</div>
        </div>
      </div>
      <div class="row">
        <button class="btn" data-act="toast" data-msg="Appel simulé — composition du numéro en local.">${ic('phone',14)}Appeler</button>
        <button class="btn pri" data-act="page" data-page="devis-edit">${ic('plus',14)}Nouveau devis</button>
      </div>
    </div>
  </div>
  <div class="grid c2">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:12px">Coordonnées</h2>
      ${[['pin','Adresse',c.addr],['phone','Téléphone',c.phone],['mail','E-mail',c.email],['doc','Type',c.type]].map(i=>`
        <div class="row" style="gap:11px;margin-bottom:11px;align-items:flex-start"><span class="muted" style="margin-top:2px">${ic(i[0],15)}</span>
        <div><span class="lbl">${i[1]}</span><div style="font-size:13.5px">${i[2]}</div></div></div>`).join('')}
      <span class="lbl">Note interne</span>
      <div class="note" style="display:block;line-height:1.5;margin-top:5px">${c.notes}</div>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:6px">Historique</h2>
      <table class="tbl"><thead><tr><th>Document</th><th>Date</th><th class="num">Montant</th><th>Statut</th></tr></thead>
      <tbody>
        <tr data-act="page" data-page="facture" data-id="F-2026-032"><td><b>Facture</b> F-2026-032</td><td class="muted">04/10/2026</td><td class="num">${eur(760)}</td>${stChip('Partielle — 380 € reçus','warn')}</tr>
        <tr data-act="toast" data-msg="Chantier CH-2026-007 — détail simulé (démonstration)."><td><b>Chantier</b> CH-2026-007 — Fuite + robinetterie</td><td class="muted">03/10/2026</td><td class="num">${eur(760)}</td>${stChip('Terminé','ok')}</tr>
        <tr data-act="toast" data-msg="Devis DEV-2026-017 — PDF local fictif."><td><b>Devis</b> DEV-2026-017</td><td class="muted">22/09/2026</td><td class="num">${eur(760)}</td>${stChip('Accepté','ok')}</tr>
      </tbody></table>
    </div>
  </div>`;
}

/* ---------- COMMERCE ---------- */
function vDevis(){
  const list = DEVIS.filter(d => (d.client+' '+d.id).toLowerCase().includes(state.search.toLowerCase()));
  return `
  <div class="ph"><div><h1>Devis</h1><p class="sub">Suivez l'état de vos propositions commerciales.</p></div>
    <button class="btn pri" data-act="page" data-page="devis-edit">${ic('plus',14)}Nouveau devis</button></div>
  <div class="srch" style="margin-bottom:14px">${ic('search',15)}<input class="in" placeholder="Rechercher un devis ou un client…" data-search="devis" value="${state.search}"/></div>
  <div class="card tblwrap">
    <table class="tbl"><thead><tr><th>Numéro</th><th>Client</th><th>Date</th><th class="num">Montant</th><th>Statut</th><th>Chantier</th></tr></thead>
    <tbody>${list.map(d=>{ const s=devisSt[d.status]; return `
      <tr data-act="${d.id==='DEV-2026-020'?'page':'toast'}" ${d.id==='DEV-2026-020'?'data-page="devis-edit"':'data-msg="Consultation du devis '+d.id+' simulée (PDF local fictif)."'}">
        <td><b>${d.id}</b></td><td>${d.client}</td><td class="muted">${d.date}</td><td class="num"><b>${eur(d.amount)}</b></td>
        <td>${stChip(s[0],s[1])}</td><td class="muted">${d.chantier||'—'}</td></tr>`;}).join('')}
    </tbody></table>
  </div>`;
}

function vDevisEdit(){
  const total = devisLines.reduce((s,l)=>s+l.qty*l.price,0);
  return `
  ${crumbs('Commerce','devis','Nouveau devis')}
  <div class="spread" style="margin-bottom:16px">
    <h1>Nouveau devis</h1>
    <div class="row">
      <button class="btn" data-act="module" data-ch="commerce" data-mod="devis">Annuler</button>
      <button class="btn" data-act="toast" data-msg="Devis enregistré comme brouillon — simulation.">${ic('doc',14)}Brouillon</button>
      <button class="btn pri" data-act="toast" data-msg="Aperçu PDF généré localement (simulation) — aucun envoi réel.">${ic('check',14)}Finaliser le devis</button>
    </div>
  </div>
  <div class="grid" style="grid-template-columns:1fr 1.9fr;align-items:start" id="devisgrid">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:12px">Client</h2>
      <div class="field"><span class="lbl">Client concerné</span>
        <select class="in"><option>Boulangerie Maison Léon</option><option>Marie Bertrand</option><option>SCI Bellevue</option><option>— Nouveau client —</option></select></div>
      <div class="field"><span class="lbl">Adresse d'intervention</span><input class="in" value="27 pl. du Commerce, 44000 Nantes"/></div>
      <div class="row" style="gap:10px">
        <div class="field" style="flex:1"><span class="lbl">Date</span><input class="in" value="11/10/2026"/></div>
        <div class="field" style="flex:1"><span class="lbl">Validité</span><input class="in" value="30 jours"/></div>
      </div>
      <span class="note">${ic('info',12)} TVA non applicable, art. 293 B du CGI</span>
    </div>
    <div>
      <div class="card pad" style="margin-bottom:14px">
        <div class="spread" style="margin-bottom:8px"><h2 style="font-size:15px">Prestations</h2>
          <button class="btn sm" data-act="picker">${ic('plus',13)}Ajouter depuis le catalogue</button></div>
        ${state.picker?`
        <div style="border:1px solid var(--accent);border-radius:11px;padding:10px;margin-bottom:12px;background:var(--accent-soft)">
          <div class="srch" style="margin-bottom:8px">${ic('search',14)}<input class="in" style="padding-left:32px;font-size:12.5px" placeholder="Rechercher une prestation…"/></div>
          ${PRESTATIONS.slice(0,5).map(p=>`
            <button class="mi" style="font-size:13px" data-act="addline" data-ref="${p.ref}">${ic('plus',13)}${p.name}
            <span class="muted mono" style="margin-left:auto;font-size:11px">${eur(p.price)} / ${p.unit}</span></button>`).join('')}
        </div>`:''}
        <div class="tblwrap"><table class="tbl">
          <thead><tr><th>Prestation</th><th>Qté</th><th>Unité</th><th class="num">PU</th><th class="num">Total</th><th></th></tr></thead>
          <tbody>${devisLines.map((l,i)=>`
            <tr style="cursor:default"><td><b>${l.name}</b><div class="muted mono" style="font-size:10.5px">${l.ref}</div></td>
            <td><input class="in mono" style="padding:5px 8px;width:64px" type="number" min="0" step="0.5" value="${l.qty}" data-qty="${i}"/></td>
            <td class="muted">${l.unit}</td><td class="num">${eur(l.price)}</td><td class="num"><b>${eur(l.qty*l.price)}</b></td>
            <td><button class="btn ghost sm" style="color:var(--bad)" data-act="rmline" data-i="${i}">${ic('trash',14)}</button></td></tr>`).join('')}
          </tbody></table></div>
      </div>
      <div class="card pad" style="display:flex;justify-content:flex-end">
        <div style="min-width:250px">
          <div class="spread" style="margin-bottom:5px"><span class="muted">Sous-total</span><b class="mono">${eur(total)}</b></div>
          <div class="spread" style="margin-bottom:5px"><span class="muted">TVA</span><span class="muted">Non applicable</span></div>
          <div class="spread" style="border-top:1px solid var(--line);padding-top:9px"><b>Total HT</b><span class="big mono" style="font-size:19px">${eur(total)}</span></div>
        </div>
      </div>
    </div>
  </div>`;
}

function vBons(){
  const rows = [['BC-2026-011','Frise Matériaux','CH-2026-008',1240,'received'],['BC-2026-010','HeatingPro','CH-2026-008',780,'sent'],['BC-2026-008','Frise Matériaux','CH-2026-006',520,'sent']];
  return `
  <div class="ph"><h1>Bons de commande</h1><p class="sub">Commandes fournisseurs liées à vos chantiers.</p></div>
  <div class="card tblwrap"><table class="tbl">
    <thead><tr><th>Numéro</th><th>Fournisseur</th><th>Chantier</th><th class="num">Montant</th><th>Statut</th></tr></thead>
    <tbody>${rows.map(r=>`<tr data-act="toast" data-msg="Bon de commande ${r[0]} — PDF local fictif.">
      <td><b>${r[0]}</b></td><td>${r[1]}</td><td class="muted">${r[2]}</td><td class="num">${eur(r[3])}</td>
      <td>${stChip(r[4]==='received'?'Réceptionné':'Envoyé',r[4]==='received'?'ok':'info')}</td></tr>`).join('')}
    </tbody></table></div>`;
}

/* ---------- TRAVAUX ---------- */
function vChantiers(){
  return `
  <div class="ph"><div><h1>Chantiers</h1><p class="sub">Suivi opérationnel de vos travaux en cours et planifiés.</p></div>
    <div class="row"><button class="btn" data-act="module" data-ch="planification" data-mod="calendrier">${ic('calendar',14)}Planification</button>
    <button class="btn pri" data-act="toast" data-msg="Nouveau chantier — démonstration, aucune donnée enregistrée.">${ic('plus',14)}Nouveau chantier</button></div></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(320px,1fr))">
    ${CHANTIERS.map(ch=>{ const s=chantSt[ch.status]; return `
    <div class="card pad tile" data-act="toast" data-msg="Fiche chantier ${ch.id} — vue détaillée simulée (démonstration).">
      <div class="spread" style="margin-bottom:8px"><span class="muted mono" style="font-size:11px;font-weight:600">${ch.id}</span>${stChip(s[0],s[1])}</div>
      <b style="font-size:15px;line-height:1.35;display:block">${ch.title}</b>
      <div class="muted" style="font-size:12.5px;margin:4px 0 12px">${ch.client}</div>
      <div class="row" style="gap:14px;font-size:12.5px;color:var(--muted);margin-bottom:12px">
        <span class="row" style="gap:5px">${ic('calendar',13)}${ch.start} → ${ch.end}</span>
        <span class="row" style="gap:5px">${ic('euro',13)}${eur(ch.amount)}</span></div>
      <div class="bar" style="margin-bottom:6px"><div style="width:${ch.progress}%;${ch.progress===100?'background:var(--ok)':''}"></div></div>
      <div class="spread"><span class="muted mono" style="font-size:11px">${ch.progress}% · Devis ${ch.devis}</span><span class="lbl">ouvrir</span></div>
    </div>`;}).join('')}
  </div>`;
}

/* ---------- FACTURATION ---------- */
function vFactures(){
  const list = FACTURES.filter(f => state.ffilter==='all' || f.status===state.ffilter);
  return `
  <div class="ph"><div><h1>Factures</h1><p class="sub">Encaissé en octobre : 2 860 € · Restant dû : 1 830 €.</p></div>
    <button class="btn pri" data-act="toast" data-msg="Facture vierge prête (simulation) — sélectionnez un chantier ou un client.">${ic('plus',14)}Créer une facture</button></div>
  <div class="row" style="gap:7px;margin-bottom:14px;flex-wrap:wrap">
    ${[['all','Toutes'],['partial','Partielles'],['late','Impayées'],['paid','Réglées']].map(f=>'<button class="chip '+(state.ffilter===f[0]?'on':'')+'" data-act="ffilter" data-f="'+f[0]+'">'+f[1]+'</button>').join('')}
  </div>
  <div class="card tblwrap"><table class="tbl">
    <thead><tr><th>Facture</th><th>Client</th><th>Date</th><th>Échéance</th><th class="num">Montant</th><th class="num">Reste dû</th><th>Statut</th></tr></thead>
    <tbody>${list.map(f=>{ const s=factSt[f.status]; const detail=['F-2026-032','F-2026-029'].includes(f.id); return `
      <tr ${detail?'data-act="page" data-page="facture" data-id="'+f.id+'"':'data-act="toast" data-msg="Consultation de '+f.id+' simulée (PDF local fictif)." style="cursor:pointer"'}>
        <td><b>${f.id}</b></td><td>${f.client}</td><td class="muted">${f.date}</td>
        <td class="muted"${f.status==='late'?' style="color:var(--bad)"':''}>${f.due}</td>
        <td class="num">${eur(f.amount)}</td><td class="num"><b>${eur(f.amount-f.paid)}</b></td>
        <td>${stChip(s[0],s[1])}</td></tr>`;}).join('')}
    </tbody></table></div>`;
}

function vFacture(){
  const f = FACTURES.find(x=>x.id===state.pageId) || FACTURES[1];
  const late = f.status==='late';
  return `
  ${crumbs('Facturation','factures',f.id)}
  <div class="spread" style="margin-bottom:16px;flex-wrap:wrap;gap:12px">
    <div class="row" style="gap:12px"><h1 style="margin:0">${f.id}</h1>
      ${stChip(late?'Impayée — relance nécessaire':factSt[f.status][0], late?'bad':factSt[f.status][1])}</div>
    <div class="row">
      <button class="btn" data-act="toast" data-msg="PDF « ${f.id} » ouvert localement — fichier fictif.">${ic('download',14)}PDF</button>
      <button class="btn" ${late?'':'disabled'} data-act="toast" data-msg="Rappel de paiement généré en local (simulation) — aucun envoi réel.">${ic('mail',14)}Rappel</button>
      <button class="btn pri" data-act="toast" data-msg="Encaissement de ${eur(f.amount-f.paid)} enregistré (simulation — aucune donnée réelle).">${ic('check',14)}Encaisser le solde</button>
    </div>
  </div>
  <div class="grid c2">
    <div class="card pad" style="margin-bottom:14px">
      <div class="spread" style="margin-bottom:10px">
        <div><b style="font-size:15px">${f.client}</b><div class="muted" style="font-size:12.5px">Chantier ${f.chantier||'—'}</div></div>
        <div class="muted" style="font-size:12.5px;text-align:right">Émise le ${f.date}<br/>Échéance ${f.due}</div>
      </div>
      <div class="tblwrap"><table class="tbl">
        <thead><tr><th>Prestation</th><th class="num">Qté</th><th class="num">PU</th><th class="num">Total</th></tr></thead>
        <tbody>
          <tr style="cursor:default"><td>Recherche de fuite + réparation</td><td class="num">3 h</td><td class="num">${eur(65)}</td><td class="num">${eur(195)}</td></tr>
          <tr style="cursor:default"><td>Remplacement robinet mélangeur</td><td class="num">2 u</td><td class="num">${eur(95)}</td><td class="num">${eur(190)}</td></tr>
          <tr style="cursor:default"><td>Main d'œuvre complémentaire</td><td class="num">6,5 h</td><td class="num">${eur(55)}</td><td class="num">${eur(357.5)}</td></tr>
          <tr style="cursor:default"><td>Déplacement zone 1</td><td class="num">1</td><td class="num">${eur(25)}</td><td class="num">${eur(25)}</td></tr>
        </tbody></table></div>
      <div style="display:flex;justify-content:flex-end;margin-top:12px"><div style="min-width:220px">
        <div class="spread" style="margin-bottom:4px"><span class="muted">Total HT</span><b class="mono">${eur(f.amount)}</b></div>
        <div class="spread"><span class="muted">TVA</span><span class="muted">Non applicable</span></div>
      </div></div>
    </div>
    <div class="grid" style="align-items:start">
      <div class="card pad">
        <h2 style="font-size:15px;margin-bottom:10px">Règlements</h2>
        ${f.paid>0?`
        <div class="spread" style="padding-bottom:10px;border-bottom:1px solid var(--line)">
          <div><b style="font-size:13.5px">Acompte reçu</b><div class="muted" style="font-size:12px">05/10/2026 · Virement</div></div>
          <b class="mono">${eur(f.paid)}</b></div>`:'<div class="muted" style="font-size:13px;margin-bottom:10px">Aucun règlement enregistré.</div>'}
        <div class="spread" style="padding-top:10px">
          <b style="font-size:13.5px;color:${late?'var(--bad)':'var(--accent)'}">Reste dû</b>
          <b class="mono" style="font-size:17px;color:${late?'var(--bad)':'var(--accent)'}">${eur(f.amount-f.paid)}</b></div>
      </div>
      <div class="card pad">
        <h2 style="font-size:15px;margin-bottom:8px">Documents associés</h2>
        <button class="mi" data-act="toast" data-msg="Ouverture locale simulée : devis DEV-2026-017.">${ic('doc',15)}Devis DEV-2026-017 (PDF)</button>
        <button class="mi" data-act="toast" data-msg="Ouverture locale simulée : dossier du chantier CH-2026-007.">${ic('folder',15)}Chantier CH-2026-007</button>
      </div>
    </div>
  </div>`;
}

function vAvoirs(){
  const rows = [['AV-2026-003','Avoir','Marie Bertrand',120,'applied'],['AV-2026-002','Avoir','SCI Bellevue',80,'applied'],['AC-2026-011','Acompte','Marie Bertrand',380,'received'],['AC-2026-010','Acompte','SCI Bellevue',500,'received']];
  return `
  <div class="ph"><h1>Avoirs & acomptes</h1><p class="sub">Documents d'ajustement et règlements partiels.</p></div>
  <div class="card tblwrap"><table class="tbl">
    <thead><tr><th>Numéro</th><th>Type</th><th>Client</th><th class="num">Montant</th><th>Statut</th></tr></thead>
    <tbody>${rows.map(r=>`<tr data-act="toast" data-msg="Document ${r[0]} — fichier fictif.">
      <td><b>${r[0]}</b></td><td class="muted">${r[1]}</td><td>${r[2]}</td><td class="num">${eur(r[3])}</td>
      <td>${stChip(r[4]==='applied'?'Imputé':'Reçu',r[4]==='applied'?'ok':'info')}</td></tr>`).join('')}
    </tbody></table></div>`;
}

/* ---------- TRÉSORERIE ---------- */
function vFlux(){
  const bars = [['Juin',2600],['Juil',3100],['Août',2950],['Sept',3480],['Oct*',2860]];
  const max = Math.max(...bars.map(b=>b[1]));
  return `
  <div class="ph"><h1>Flux & dépenses</h1><p class="sub">Lecture simple de vos entrées et sorties d'argent.
    <span class="note">${ic('info',12)} Données fictives — * mois en cours</span></p></div>
  <div class="grid k4" style="margin-bottom:16px">
    <div class="card k"><span class="lbl">Encaissé (oct.)</span><div class="big mono" style="color:var(--ok)">2 860 €</div></div>
    <div class="card k"><span class="lbl">Dépenses (oct.)</span><div class="big mono" style="color:var(--bad)">1 240 €</div></div>
    <div class="card k tile" data-act="module" data-ch="facturation" data-mod="factures"><span class="lbl">Restant à recevoir</span><div class="big mono">1 830 €</div></div>
    <div class="card k"><span class="lbl">Disponible (est.)</span><div class="big mono">4 450 €</div></div>
  </div>
  <div class="grid c2">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:16px">Encaissements mensuels</h2>
      <div class="row" style="align-items:flex-end;gap:16px;height:160px">
        ${bars.map(b=>`<div style="flex:1;text-align:center">
          <div style="background:var(--accent-soft);border-radius:8px 8px 3px 3px;height:128px;display:flex;align-items:flex-end">
            <div style="width:${b[0]==='Oct*'?'55%':'100%'};margin:0 auto;height:${Math.round(b[1]/max*100)}%;background:linear-gradient(180deg,var(--accent),var(--accent-hi));border-radius:8px 8px 3px 3px"></div>
          </div>
          <div class="muted mono" style="font-size:11px;margin-top:8px">${b[0]}</div>
        </div>`).join('')}
      </div>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:8px">Derniers mouvements</h2>
      ${MOVES.map(m=>`
        <div class="spread" style="padding:10px 0;border-bottom:1px solid var(--line)">
          <div><span style="font-size:13.5px">${m.l}</span><div class="muted mono" style="font-size:11px">${m.d}</div></div>
          <b class="mono" style="color:var(--${m.s})">${m.v} €</b></div>`).join('')}
    </div>
  </div>`;
}

function vEcheances(){
  const rows = [
    ['F-2026-029','Relance impayée — Boulangerie Maison Léon','17/09/2026','bad','Retard','1 450 €','page','facture','F-2026-029'],
    ['DEV-2026-021','Relance devis — SCI Bellevue','12/10/2026','info','À traiter','4 820 €','toast','Consultation du devis DEV-2026-021 simulée.',''],
    ['F-2026-032','Solde attendu — Marie Bertrand','03/11/2026','warn','À venir','380 €','page','facture','F-2026-032'],
    ['CH-2026-006','Démarrage chantier — Gérard Dupont','12/10/2026','acc','À traiter','','toast','Fiche chantier CH-2026-006 — vue détaillée simulée.','']
  ];
  return `
  <div class="ph"><h1>Échéances</h1><p class="sub">Ce qui attend une action de votre part.</p></div>
  <div class="card pad">
    ${rows.map(r=>`
    <div class="spread" style="padding:13px 0;border-bottom:1px solid var(--line)">
      <div><b style="font-size:13.5px">${r[1]}</b><div class="muted mono" style="font-size:12px">${r[0]} · échéance ${r[2]}</div></div>
      <div class="row">${r[5]?'<b class="mono" style="min-width:72px;text-align:right">'+r[5]+'</b>':''}${stChip(r[4],r[3])}
        <button class="btn sm" data-act="${r[6]}" ${r[6]==='page'?'data-page="'+r[7]+'" data-id="'+r[8]+'"':'data-msg="'+r[7]+'"'}>Ouvrir</button></div>
    </div>`).join('')}
  </div>`;
}

/* ---------- CATALOGUE ---------- */
function vCatalogue(){
  const cats = ['Tout','Chauffage','Plomberie','Maintenance','Main d\u2019œuvre'];
  const list = PRESTATIONS.filter(p => (state.cat==='Tout'||p.cat===state.cat) && p.name.toLowerCase().includes(state.search.toLowerCase()));
  return `
  <div class="ph"><div><h1>Catalogue de prestations</h1><p class="sub">Vos prestations réutilisables pour devis et factures.</p></div>
    <button class="btn pri" data-act="toast" data-msg="Nouvelle prestation (démonstration).">${ic('plus',14)}Nouvelle prestation</button></div>
  <div class="spread" style="margin-bottom:14px;flex-wrap:wrap;gap:10px">
    <div class="srch">${ic('search',15)}<input class="in" placeholder="Rechercher une prestation…" data-search="cat" value="${state.search}"/></div>
    <div class="row" style="flex-wrap:wrap">${cats.map(c=>'<button class="chip '+(state.cat===c?'on':'')+'" data-act="cat" data-c="'+c+'">'+c+'</button>').join('')}</div>
  </div>
  <div class="card tblwrap"><table class="tbl">
    <thead><tr><th>Réf.</th><th>Libellé</th><th>Catégorie</th><th>Unité</th><th class="num">Prix</th><th></th></tr></thead>
    <tbody>${list.map(p=>`
      <tr style="cursor:default"><td class="muted mono" style="font-size:12px">${p.ref}</td><td><b>${p.name}</b></td>
      <td>${stChip(p.cat,'gray')}</td><td class="muted">${p.unit}</td><td class="num"><b>${eur(p.price)}</b></td>
      <td><button class="btn sm" data-act="toast" data-msg="« ${p.name} » prêt à être inséré dans un document (simulation).">${ic('plus',13)}Utiliser</button></td></tr>`).join('')}
    </tbody></table></div>`;
}

/* ---------- DOCUMENTS ---------- */
function vDocs(){
  const groups = [['Factures',4,'invoice'],['Devis',6,'doc'],['Bons de commande',3,'folder'],['Avoirs & acomptes',4,'wallet']];
  const files = [['F-2026-034.pdf','Facture','SCI Bellevue','22/09/2026','48 Ko'],['DEV-2026-021.pdf','Devis','SCI Bellevue','02/10/2026','52 Ko'],['CH-2026-008 — photos.zip','Chantier','Karim Haddad','08/10/2026','3,2 Mo'],['BC-2026-011.pdf','Bon de commande','Frise Matériaux','04/10/2026','39 Ko']];
  return `
  <div class="ph"><h1>Documents</h1><p class="sub">Tous les fichiers générés, stockés localement sur cet ordinateur.</p></div>
  <div class="grid k4" style="margin-bottom:16px">
    ${groups.map(g=>`<div class="card k tile" data-act="toast" data-msg="Dossier « ${g[0]} » — ${g[1]} fichiers fictifs.">
      <div class="spread"><span class="lbl">${g[0]}</span><span class="muted">${ic(g[2],15)}</span></div>
      <div class="big mono">${g[1]}</div><div class="muted" style="font-size:12px">documents PDF</div></div>`).join('')}
  </div>
  <div class="card tblwrap"><table class="tbl">
    <thead><tr><th>Fichier</th><th>Type</th><th>Client</th><th>Date</th><th>Taille</th></tr></thead>
    <tbody>${files.map(f=>`<tr data-act="toast" data-msg="Ouverture locale simulée : ${f[0]}.">
      <td><b>${f[0]}</b></td><td class="muted">${f[1]}</td><td>${f[2]}</td><td class="muted">${f[3]}</td><td class="muted mono" style="font-size:12px">${f[4]}</td></tr>`).join('')}
    </tbody></table></div>`;
}

/* ---------- PLANIFICATION ---------- */
const MOIS = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'];
function vCalendrier(){
  const d = new Date(2026, 9 + state.cal, 1);
  const y = d.getFullYear(), m = d.getMonth();
  const first = (d.getDay()+6)%7, nd = new Date(y, m+1, 0).getDate();
  const cells = []; for(let i=0;i<first;i++) cells.push(null); for(let i=1;i<=nd;i++) cells.push(i);
  const key = y+'-'+String(m+1).padStart(2,'0');
  return `
  <div class="ph"><div><h1>Planification</h1><p class="sub">${MOIS[m]} ${y} — planning local, sans synchronisation externe.</p></div>
    <div class="row">
      <button class="btn sm icobtn" data-act="cal" data-d="-1">${ic('chevL',14)}</button>
      <button class="btn sm" data-act="cal" data-d="0">Octobre 2026</button>
      <button class="btn sm icobtn" data-act="cal" data-d="1">${ic('chevR',14)}</button>
    </div></div>
  <div class="card pad">
    <div class="calhead">${['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'].map(j=>'<span>'+j+'</span>').join('')}</div>
    <div class="cal">
      ${cells.map(c => c===null ? '<div class="day off"></div>' : `
        <div class="day ${y===2026&&m===9&&c===11?'today':''}">
          <b class="mono">${c}</b>
          ${EVENTS.filter(e=>e.date===key+'-'+String(c).padStart(2,'0')).map(e=>'<div class="ev '+e.type+'" title="'+e.label+'">'+e.label+'</div>').join('')}
        </div>`).join('')}
    </div>
    <div class="legend">
      <span><i class="ev-a" style="width:10px;height:10px;border-radius:3px;display:inline-block"></i>Chantiers</span>
      <span><i style="width:10px;height:10px;border-radius:3px;display:inline-block;background:var(--accent2-soft);border:1px solid var(--accent-2)"></i>Rendez-vous</span>
      <span><i class="ev-w" style="width:10px;height:10px;border-radius:3px;display:inline-block"></i>Relances</span>
      <span><i class="ev-g" style="width:10px;height:10px;border-radius:3px;display:inline-block"></i>Maintenance</span>
    </div>
    ${y===2026&&m===9?'':'<p class="note" style="margin-top:12px">'+ic('info',12)+' Aucun événement fictif pour ce mois — la démonstration couvre octobre 2026.</p>'}
  </div>`;
}
function vChrono(){
  const weeks = [['Semaine du 5 octobre',[['Lun 5','Chaudière Haddad — début','ev-a'],['Jeu 8','Point client Haddad','ev-b'],['Ven 9','Chaudière Haddad — fin','ev-a'],['Sam 10','Relance devis Maison Léon','ev-w']]],
    ['Semaine du 12 octobre',[['Lun 12','Radiateurs Dupont — début','ev-a'],['Mer 14','Relance facture F-2026-029','ev-w'],['Ven 16','Radiateurs Dupont — fin','ev-a']]],
    ['Semaine du 19 octobre',[['Mar 20','Entretien annuel Bertrand','ev-g'],['Sam 24','Rappel encaissements','ev-w']]]];
  return `
  <div class="ph"><h1>Chronologie</h1><p class="sub">Vos interventions et rappels dans l'ordre du temps.</p></div>
  ${weeks.map(w=>`
  <div class="card pad" style="margin-bottom:14px">
    <h2 style="font-size:14px;margin-bottom:6px">${w[0]}</h2>
    ${w[1].map(e=>`<div class="row" style="padding:10px 0;border-bottom:1px solid var(--line)">
      <span class="ev ${e[2]} mono" style="min-width:58px;text-align:center;margin:0">${e[0]}</span>
      <span style="font-size:13.5px">${e[1]}</span></div>`).join('')}
  </div>`).join('')}`;
}

/* ---------- PARAMÈTRES ---------- */
function vPrefs(){
  return `
  <div class="ph"><h1>Préférences</h1><p class="sub">Réglages locaux — rien n'est synchronisé avec un service distant.</p></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:14px">Apparence</h2>
      <span class="lbl" style="display:block;margin-bottom:8px">Thème de l'interface</span>
      <div class="row" style="align-items:stretch;margin-bottom:16px">
        <button class="tc ${state.theme==='light'?'on':''}" data-act="settheme" data-t="light">
          ${state.theme==='light'?'<span class="tick">'+ic('check',15)+'</span>':''}
          <span class="prev" style="background:#F3F5FA">
            <i style="width:60%;background:#0B1220"></i><i style="width:85%;background:#DFE4EF"></i><i style="width:38%;background:#2B4BFF"></i>
          </span><b style="font-size:13px">Clair — Cobalt</b></button>
        <button class="tc ${state.theme==='dark'?'on':''}" data-act="settheme" data-t="dark">
          ${state.theme==='dark'?'<span class="tick">'+ic('check',15)+'</span>':''}
          <span class="prev" style="background:#0E1526">
            <i style="width:60%;background:#E9EDF7"></i><i style="width:85%;background:#222D47"></i><i style="width:38%;background:#5D7CFF"></i>
          </span><b style="font-size:13px">Sombre — Graphite</b></button>
      </div>
      <div class="field"><span class="lbl">Taille du texte</span><select class="in"><option>Normal (recommandé)</option><option>Grand</option><option>Petit</option></select></div>
      <div class="field"><span class="lbl">Densité des listes</span><select class="in"><option>Confortable</option><option>Compacte</option></select></div>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:14px">Assistant Léon</h2>
      <div class="spread" style="padding:10px 0;border-bottom:1px solid var(--line)">
        <div><b style="font-size:13.5px">Bulle d'appel</b><div class="muted" style="font-size:12.5px">Afficher l'icône de Léon en permanence</div></div>
        <button class="btn sm" data-act="leon">${ic('spark',13)}Tester</button></div>
      <div class="spread" style="padding:10px 0;border-bottom:1px solid var(--line)">
        <div><b style="font-size:13.5px">Suggestions proactives</b><div class="muted" style="font-size:12.5px">Léon signale les relances à effectuer</div></div>
        <span class="st ok">Activées</span></div>
      <p class="note" style="margin-top:12px">${ic('lock',12)} Léon fonctionne en local : aucune requête réseau.</p>
    </div>
  </div>`;
}
function vEntreprise(){
  return `
  <div class="ph"><h1>Entreprise</h1><p class="sub">Informations reprises sur vos devis et factures.</p></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:14px">Identification</h2>
      <div class="field"><span class="lbl">Entreprise</span><input class="in" value="${USER.company}"/></div>
      <div class="field"><span class="lbl">SIRET</span><input class="in" value="${USER.siret}"/></div>
      <div class="field"><span class="lbl">Téléphone</span><input class="in" value="${USER.phone}"/></div>
      <div class="field"><span class="lbl">E-mail</span><input class="in" value="${USER.email}"/></div>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:14px">Règles de facturation</h2>
      <div class="field"><span class="lbl">Régime de TVA</span><select class="in"><option>Franchise — TVA non applicable</option><option>Assujetti (20 %)</option></select></div>
      <div class="field"><span class="lbl">Validité par défaut des devis</span><input class="in" value="30 jours"/></div>
      <div class="field"><span class="lbl">Mentions légales</span><textarea class="in">TVA non applicable, art. 293 B du CGI</textarea></div>
    </div>
  </div>`;
}
function vDonnees(){
  return `
  <div class="ph"><h1>Données & licence</h1><p class="sub">Stockage, sauvegarde et informations sur le logiciel.</p></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:12px">Stockage local</h2>
      <div class="row" style="gap:11px;margin-bottom:11px"><span class="muted" style="margin-top:2px">${ic('lock',15)}</span>
        <div><span class="lbl">Emplacement</span><div style="font-size:13.5px">Dossier BATORYA — cet ordinateur uniquement</div></div></div>
      <div class="row" style="gap:11px;margin-bottom:14px"><span class="muted" style="margin-top:2px">${ic('folder',15)}</span>
        <div><span class="lbl">Sauvegarde</span><div style="font-size:13.5px">Manuelle, conseillée chaque semaine</div></div></div>
      <button class="btn" data-act="toast" data-msg="Sauvegarde simulée : aucun fichier réel n'a été créé.">${ic('download',14)}Créer une sauvegarde</button>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:12px">À propos</h2>
      <div class="row" style="gap:11px;margin-bottom:11px"><span class="muted" style="margin-top:2px">${ic('info',15)}</span>
        <div><span class="lbl">Version</span><div style="font-size:13.5px">BATORYA Essentiel V6 — prototype B de conception</div></div></div>
      <div class="row" style="gap:11px;margin-bottom:11px"><span class="muted" style="margin-top:2px">${ic('lock',15)}</span>
        <div><span class="lbl">Licence</span><div style="font-size:13.5px">Démonstration locale</div></div></div>
      <div class="row" style="gap:11px"><span class="muted" style="margin-top:2px">${ic('spark',15)}</span>
        <div><span class="lbl">Assistant</span><div style="font-size:13.5px">Léon — intégré, fonctionne en local</div></div></div>
    </div>
  </div>`;
}

/* ---------- PROFIL ---------- */
function vProfil(){
  return `
  <div class="crumbs"><button class="crumb" data-act="home">${ic('chevL',12)}Accueil</button><span>/</span><b>Mon profil</b></div>
  <div class="spread" style="margin-bottom:16px"><h1>Mon profil</h1>
    <button class="btn" data-act="editp">${ic('edit',14)}${state.edit?'Terminer':'Modifier'}</button></div>
  <div class="grid" style="grid-template-columns:300px 1fr;align-items:start" id="profilgrid">
    <div class="card pad" style="text-align:center">
      <img src="${AVATAR}" alt="Photo de profil fictive" style="width:84px;height:84px;border-radius:99px;border:3px solid var(--surface);box-shadow:var(--shadow);margin:6px auto 12px;display:block"/>
      <b style="font-size:17px">${USER.name}</b>
      <div class="muted" style="font-size:13px;margin-bottom:6px">${USER.role}</div>
      ${stChip('Compte local','acc')}
      <p class="note" style="margin-top:14px">${ic('info',12)} Photo fictive — stockée localement</p>
    </div>
    <div class="card pad">
      <h2 style="font-size:15px;margin-bottom:14px">Informations professionnelles</h2>
      <div class="grid" style="grid-template-columns:1fr 1fr">
        <div class="field"><span class="lbl">Nom complet</span><input class="in" value="${USER.name}" ${state.edit?'':'disabled'}/></div>
        <div class="field"><span class="lbl">Entreprise</span><input class="in" value="${USER.company}" ${state.edit?'':'disabled'}/></div>
        <div class="field"><span class="lbl">E-mail</span><input class="in" value="${USER.email}" ${state.edit?'':'disabled'}/></div>
        <div class="field"><span class="lbl">Téléphone</span><input class="in" value="${USER.phone}" ${state.edit?'':'disabled'}/></div>
        <div class="field"><span class="lbl">SIRET</span><input class="in" value="${USER.siret}" ${state.edit?'':'disabled'}/></div>
        <div class="field"><span class="lbl">Mentions TVA</span><input class="in" value="TVA non applicable, art. 293 B du CGI" ${state.edit?'':'disabled'}/></div>
      </div>
      ${state.edit?'<button class="btn pri" data-act="toast" data-msg="Modifications enregistrées (simulation) — aucune donnée réelle.">'+ic('check',14)+'Enregistrer</button>':''}
    </div>
  </div>`;
}

/* ================================================================
   RENDU PRINCIPAL
   ================================================================ */
function view(){
  if(state.page==='profil') return vProfil();
  if(state.page==='client') return vClient();
  if(state.page==='devis-edit') return vDevisEdit();
  if(state.page==='facture') return vFacture();
  switch(state.module){
    case 'clients': return vClients();
    case 'prospects': return vProspects();
    case 'devis': return vDevis();
    case 'bons': return vBons();
    case 'chantiers': return vChantiers();
    case 'factures': return vFactures();
    case 'avoirs': return vAvoirs();
    case 'flux': return vFlux();
    case 'echeances': return vEcheances();
    case 'prestations': return vCatalogue();
    case 'docs': return vDocs();
    case 'calendrier': return vCalendrier();
    case 'chrono': return vChrono();
    case 'prefs': return vPrefs();
    case 'entreprise': return vEntreprise();
    case 'donnees': return vDonnees();
    default: return vHome();
  }
}

function render(){
  const ch = CHAPTERS.find(c=>c.id===state.chapter) || null;
  document.getElementById('app').innerHTML = `
  <div class="topline"></div>
  <header class="top">
    <button class="brand" data-act="home" title="Retour à l'accueil">
      <span class="mark">B</span>
      <span class="brandtxt"><b>BATORYA</b><i>Essentiel V6 · local</i></span>
    </button>
    <nav class="chaps">
      <button class="chap ${!state.chapter?'on':''}" data-act="home">Accueil</button>
      ${CHAPTERS.map(c=>'<button class="chap '+(state.chapter===c.id?'on':'')+'" data-act="chapter" data-ch="'+c.id+'">'+c.label+'</button>').join('')}
    </nav>
    <div class="tools">
      <button class="searchbox" data-act="toast" data-msg="Recherche globale — fonction simulée dans ce prototype.">${ic('search',14)}<span>Rechercher…</span><kbd>Ctrl K</kbd></button>
      <button class="icobtn" data-act="theme" title="${state.theme==='dark'?'Thème clair':'Thème sombre'}">${ic(state.theme==='dark'?'sun':'moon',16)}</button>
      <button class="icobtn" data-act="toast" data-msg="3 rappels en attente : relance F-2026-029, devis Maison Léon, chaudière Haddad." title="Notifications">${ic('bell',16)}<span class="dot"></span></button>
      <button class="profilbtn" data-act="profile" title="Mon profil">
        <img src="${AVATAR}" alt=""/><span class="ptxt"><b>${USER.name}</b><i>${USER.company}</i></span>${ic('chevD',13)}
      </button>
    </div>
  </header>
  ${ch?'<div class="mods"><span class="modlbl">'+ch.label+'</span>'+
    ch.modules.map(m=>'<button class="mod '+(state.module===m[0]?'on':'')+'" data-act="module" data-ch="'+ch.id+'" data-mod="'+m[0]+'">'+m[1]+'</button>').join('')+'</div>':''}
  <main class="content"><div class="wrap">${view()}</div></main>

  ${state.profile?`
  <div class="pmenu">
    <div class="row" style="padding:10px 12px"><img src="${AVATAR}" alt="" style="width:36px;height:36px;border-radius:99px"/>
      <div><b style="font-size:13.5px">${USER.name}</b><div class="muted" style="font-size:11.5px">${USER.email}</div></div></div>
    <div class="msep"></div>
    <button class="mi" data-act="page" data-page="profil">${ic('users',15)}Mon profil</button>
    <button class="mi" data-act="chapter" data-ch="parametres">${ic('gear',15)}Paramètres</button>
    <button class="mi" data-act="theme">${ic(state.theme==='dark'?'sun':'moon',15)}${state.theme==='dark'?'Thème clair':'Thème sombre'}</button>
    <div class="msep"></div>
    <button class="mi" data-act="toast" data-msg="BATORYA Essentiel V6 — prototype B de conception. Licence : démonstration locale.">${ic('info',15)}À propos de BATORYA</button>
    <button class="mi danger" data-act="toast" data-msg="Session verrouillée (simulation). Les données restent sur cet ordinateur.">${ic('lock',15)}Verrouiller</button>
  </div>`:''}

  <button class="leonfab" data-act="leon" title="Léon — assistant intégré">${ic(state.leon?'x':'spark',20)}</button>

  ${state.leon?`
  <div class="leonp">
    <div class="leonh"><span class="orb">${ic('spark',15)}</span>
      <div style="flex:1"><b style="font-size:13.5px">Léon</b><div class="muted" style="font-size:11px">Assistant intégré · local</div></div>
      <button class="icobtn" data-act="leon">${ic('x',15)}</button></div>
    <div class="lmsg">${state.leonMsgs.map(m=>'<div class="lm '+m.w+'">'+m.t+'</div>').join('')}</div>
    <div class="leonc">
      <div class="qs">${['Où en sont mes devis ?','Qui me doit de l\u2019argent ?','Mes chantiers en cours'].map(q=>'<button class="chip" data-act="leonq" data-q="'+q+'">'+q+'</button>').join('')}</div>
      <div class="row" style="gap:8px"><input class="in" style="font-size:13px" placeholder="Posez une question à Léon…" data-leon-input/>
        <button class="btn pri sm" style="padding:8px 11px" data-act="sendleon">${ic('send',14)}</button></div>
    </div>
  </div>`:''}

  ${state.toast?'<div class="toast">'+state.toast+'</div>':''}`;

  /* Rétablir le focus après un re-render (saisie de recherche) */
  if(state.refocus){
    const el = document.querySelector('[data-search="'+state.refocus+'"]');
    if(el){ el.focus(); try{ el.setSelectionRange(el.value.length, el.value.length); }catch(e){} }
    state.refocus = null;
  }
}

/* ================================================================
   INTERACTIONS
   ================================================================ */
document.addEventListener('click', e=>{
  /* fermer le menu profil si l'on clique ailleurs */
  if(state.profile && !e.target.closest('.profilbtn') && !e.target.closest('.pmenu')){
    state.profile = false; render();
  }
  const t = e.target.closest('[data-act]');
  if(!t) return;
  const a = t.dataset.act;
  switch(a){
    case 'home': go(null,null); break;
    case 'chapter': { const c = CHAPTERS.find(x=>x.id===t.dataset.ch); go(c.id, c.modules[0][0]); break; }
    case 'module': go(t.dataset.ch, t.dataset.mod); break;
    case 'page': state.page = t.dataset.page; state.pageId = t.dataset.id||null; state.profile=false; state.edit=false; render(); break;
    case 'theme': state.theme = state.theme==='dark'?'light':'dark'; applyTheme(); break;
    case 'settheme': state.theme = t.dataset.t; applyTheme(); break;
    case 'profile': state.profile = !state.profile; render(); break;
    case 'leon': state.leon = !state.leon; render(); break;
    case 'toast': toast(t.dataset.msg); break;
    case 'filter': state.filter = t.dataset.f; render(); break;
    case 'ffilter': state.ffilter = t.dataset.f; render(); break;
    case 'cat': state.cat = t.dataset.c; render(); break;
    case 'picker': state.picker = !state.picker; render(); break;
    case 'editp': state.edit = !state.edit; render(); break;
    case 'cal': { const d = +t.dataset.d; state.cal = d===0 ? 0 : Math.max(-2, Math.min(2, state.cal+d)); render(); break; }
    case 'addline': { const p = PRESTATIONS.find(x=>x.ref===t.dataset.ref);
      devisLines.push({ref:p.ref,name:p.name,qty:1,unit:p.unit,price:p.price});
      state.picker = false; toast('« '+p.name+' » ajouté au devis (simulation).'); render(); break; }
    case 'rmline': devisLines.splice(+t.dataset.i,1); render(); break;
    case 'sendleon': { const el = document.querySelector('[data-leon-input]'); askLeon(el?el.value:''); break; }
    case 'leonq': askLeon(t.dataset.q); break;
  }
});

/* Saisie : met à jour l'état puis restitue le focus dans l'input */
document.addEventListener('input', e=>{
  if(e.target.matches('[data-search]')){
    state.search = e.target.value;
    state.refocus = e.target.dataset.search;
    render();
  }
});

/* Quantités du devis : recalcul sur validation (change) pour garder le focus pendant la saisie */
document.addEventListener('change', e=>{
  const el = e.target;
  if(el.matches('[data-qty]')){
    const i = +el.dataset.qty, q = Math.max(0, parseFloat(el.value)||0);
    devisLines[i].qty = q; render();
  }
});

document.addEventListener('keydown', e=>{
  if(e.key==='Enter' && e.target.matches('[data-leon-input]')){
    askLeon(e.target.value);
  }
  if(e.key==='Escape'){
    if(state.leon){ state.leon=false; render(); }
    else if(state.profile){ state.profile=false; render(); }
  }
});

render();
</script>
</body>
</html>
