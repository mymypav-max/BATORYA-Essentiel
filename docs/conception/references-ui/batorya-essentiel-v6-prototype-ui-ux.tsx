import React, { useState, useMemo, useEffect } from "react";

/* ============================================================
   BATORYA Essentiel V6 — Prototype interactif
   Données 100% fictives, locales, offline-first (démonstration)
   ============================================================ */

/* ---------- Palette & design tokens ---------- */
const DESIGN = `
:root{
  --bg:#F6F3EE; --surface:#FFFFFF; --surface2:#F1EDE6; --line:#E3DCD0;
  --text:#2A2621; --muted:#7A7367; --accent:#C05F2C; --accent-soft:#F7E4D8;
  --green:#3E7C4F; --green-soft:#E3EFE6; --amber:#A8741B; --amber-soft:#F6EBD2;
  --red:#B03A2E; --red-soft:#F7E1DD; --blue:#3D6B8F; --blue-soft:#E1EAF1;
  --shadow:0 1px 2px rgba(42,38,33,.06),0 4px 14px rgba(42,38,33,.05);
}
.dark{
  --bg:#191613; --surface:#211D19; --surface2:#2A2520; --line:#38312A;
  --text:#ECE6DC; --muted:#9C9285; --accent:#E08B57; --accent-soft:#3A2A20;
  --green:#7CB98B; --green-soft:#22301F; --amber:#D9AC5C; --amber-soft:#332916;
  --red:#E08077; --red-soft:#3A211E; --blue:#82ACCB; --blue-soft:#1F2A33;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.28);
}
html,body,#root{height:100%}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI Variable','Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);font-size:14.5px;-webkit-font-smoothing:antialiased}
.app{display:flex;flex-direction:column;height:100vh;overflow:hidden}
.app-scroll{flex:1;overflow:auto}
/* Surfaces */
.surface{background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.surface-flat{background:var(--surface);border:1px solid var(--line);border-radius:12px}
.pad{padding:16px}
/* Top bar */
.topbar{background:var(--surface);border-bottom:1px solid var(--line);display:flex;align-items:stretch;height:56px;flex-shrink:0;position:relative;z-index:40}
.topbar-in{display:flex;align-items:center;gap:6px;padding:0 14px;width:100%}
.brand{display:flex;align-items:center;gap:9px;padding:6px 10px 6px 2px;border-radius:10px;cursor:pointer;flex-shrink:0}
.brand-mark{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--accent),#8F3F1B);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:14px;letter-spacing:-.5px}
.dark .brand-mark{color:#241A12}
.brand-name{font-weight:700;font-size:15px;letter-spacing:-.2px}
.brand-sub{font-size:10px;color:var(--muted);margin-top:-2px}
/* Chapitres */
.chap{padding:8px 13px;border-radius:9px;font-size:13.5px;font-weight:500;color:var(--muted);cursor:pointer;border:none;background:none;white-space:nowrap;display:flex;align-items:center;gap:7px;transition:background .12s,color .12s}
.chap:hover{background:var(--surface2);color:var(--text)}
.chap.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
/* Module bar */
.modbar{background:var(--surface);border-bottom:1px solid var(--line);padding:8px 20px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;flex-shrink:0}
.mod{padding:7px 13px;border-radius:8px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;border:none;background:none}
.mod:hover{background:var(--surface2);color:var(--text)}
.mod.active{background:var(--surface2);color:var(--text);font-weight:600;box-shadow:inset 0 -2px 0 var(--accent)}
/* Content */
.content{padding:22px 26px 90px;max-width:1240px;margin:0 auto;width:100%}
.page-title{font-size:21px;font-weight:700;letter-spacing:-.3px;margin:0 0 4px}
.page-sub{color:var(--muted);font-size:13px;margin:0 0 18px}
/* Buttons */
.btn{display:inline-flex;align-items:center;gap:7px;padding:8px 14px;border-radius:9px;font-size:13.5px;font-weight:600;cursor:pointer;border:1px solid var(--line);background:var(--surface);color:var(--text);transition:filter .12s, background .12s}
.btn:hover{background:var(--surface2)}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff}
.dark .btn-primary{color:#241A12}
.btn-primary:hover{filter:brightness(1.07);background:var(--accent)}
.btn-ghost{border:none;background:none;color:var(--muted)}
.btn-ghost:hover{background:var(--surface2);color:var(--text)}
.btn-sm{padding:5px 10px;font-size:12.5px;border-radius:8px}
.btn:disabled{opacity:.45;cursor:not-allowed}
/* Inputs */
.input{padding:8px 12px;border-radius:9px;border:1px solid var(--line);background:var(--surface);color:var(--text);font-size:13.5px;outline:none;width:100%}
.input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.input::placeholder{color:var(--muted)}
label.f{display:block;font-size:12px;font-weight:600;color:var(--muted);margin:0 0 5px}
.field{margin-bottom:14px}
/* Badges */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:99px;font-size:11.5px;font-weight:600;white-space:nowrap}
.b-green{background:var(--green-soft);color:var(--green)} .b-amber{background:var(--amber-soft);color:var(--amber)}
.b-red{background:var(--red-soft);color:var(--red)} .b-blue{background:var(--blue-soft);color:var(--blue)}
.b-gray{background:var(--surface2);color:var(--muted)} .b-accent{background:var(--accent-soft);color:var(--accent)}
/* Tables */
.tbl{width:100%;border-collapse:collapse;font-size:13.5px}
.tbl th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);font-weight:600;padding:9px 12px;border-bottom:1px solid var(--line)}
.tbl td{padding:11px 12px;border-bottom:1px solid var(--line)}
.tbl tr:last-child td{border-bottom:none}
.tbl tbody tr{cursor:pointer;transition:background .1s}
.tbl tbody tr:hover{background:var(--surface2)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:var(--muted)}
/* Cards grid */
.grid{display:grid;gap:14px}
.kpi{padding:16px 18px}
.kpi .v{font-size:24px;font-weight:750;letter-spacing:-.5px;margin:6px 0 2px;font-variant-numeric:tabular-nums}
.kpi .l{font-size:12.5px;color:var(--muted);font-weight:500}
/* Profile */
.avatar{width:30px;height:30px;border-radius:99px;object-fit:cover;border:1.5px solid var(--line)}
.avatar-lg{width:84px;height:84px;border-radius:99px;object-fit:cover;border:3px solid var(--surface);box-shadow:var(--shadow)}
.profile-btn{display:flex;align-items:center;gap:9px;padding:5px 10px 5px 5px;border-radius:99px;border:1px solid transparent;background:none;cursor:pointer}
.profile-btn:hover{background:var(--surface2);border-color:var(--line)}
.menu{position:absolute;top:52px;right:14px;width:230px;background:var(--surface);border:1px solid var(--line);border-radius:13px;box-shadow:var(--shadow);padding:6px;z-index:60;animation:pop .13s ease}
@keyframes pop{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.menu-item{display:flex;align-items:center;gap:10px;width:100%;padding:9px 11px;border-radius:8px;font-size:13.5px;cursor:pointer;border:none;background:none;color:var(--text);text-align:left}
.menu-item:hover{background:var(--surface2)}
.menu-item.danger{color:var(--red)}
.menu-sep{height:1px;background:var(--line);margin:5px 8px}
/* Léon */
.leon-fab{position:fixed;bottom:22px;right:22px;width:52px;height:52px;border-radius:99px;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--accent),#8F3F1B);color:#fff;box-shadow:0 6px 20px rgba(192,95,44,.4);transition:transform .15s;z-index:70}
.dark .leon-fab{color:#241A12}
.leon-fab:hover{transform:scale(1.07)}
.leon-panel{position:fixed;bottom:86px;right:22px;width:360px;height:460px;background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:0 18px 50px rgba(0,0,0,.25);display:flex;flex-direction:column;z-index:70;animation:pop .15s ease}
.leon-msg{padding:10px 13px;border-radius:12px;font-size:13.5px;max-width:82%;line-height:1.45}
.leon-msg.bot{background:var(--surface2);border:1px solid var(--line)}
.leon-msg.me{background:var(--accent);color:#fff;align-self:flex-end}
.dark .leon-msg.me{color:#241A12}
.chip{padding:6px 11px;border-radius:99px;border:1px solid var(--line);background:var(--surface);font-size:12px;color:var(--muted);cursor:pointer;white-space:nowrap}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:600}
/* Misc */
.row{display:flex;align-items:center;gap:10px}
.spread{display:flex;align-items:center;justify-content:space-between;gap:12px}
.progress{height:6px;border-radius:99px;background:var(--surface2);overflow:hidden}
.progress>div{height:100%;background:var(--accent);border-radius:99px}
.back{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--muted);cursor:pointer;border:none;background:none;padding:4px 6px;border-radius:7px}
.back:hover{background:var(--surface2);color:var(--text)}
.breadcrumb{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--muted);margin-bottom:14px}
.breadcrumb b{color:var(--text);font-weight:600}
.note{font-size:11.5px;color:var(--muted);background:var(--surface2);border-radius:8px;padding:6px 10px;display:inline-flex;align-items:center;gap:6px}
/* Calendar */
.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
.cal-day{min-height:88px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:7px;font-size:12px}
.cal-day.other{opacity:.4}
.cal-day.today{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.cal-ev{border-radius:6px;padding:3px 6px;font-size:11px;font-weight:600;margin-top:4px;cursor:pointer;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ev-accent{background:var(--accent-soft);color:var(--accent)} .ev-blue{background:var(--blue-soft);color:var(--blue)}
.ev-green{background:var(--green-soft);color:var(--green)} .ev-amber{background:var(--amber-soft);color:var(--amber)}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--line);border-radius:99px;border:2px solid var(--bg)}
`;

/* ---------- Icônes (SVG inline, trait 1.8) ---------- */
const I = {
  home: <path d="M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5"/>,
  users: <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 .01M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>,
  doc: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h5"/>,
  hard: <path d="M2 20h20M4 20V10l8-6 8 6v10M9 20v-5h6v5"/>,
  invoice: <path d="M6 2h12v20l-3-2-3 2-3-2-3 2zM9 7h6M9 11h6M9 15h3"/>,
  wallet: <path d="M20 12V8H6a2 2 0 0 1 0-4h12v4M4 6v12a2 2 0 0 0 2 2h14v-4M18 12a2 2 0 0 0 0 4h4v-4z"/>,
  book: <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5z"/>,
  folder: <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>,
  calendar: <path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>,
  gear: <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 3 15a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.4-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 10 4.6a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 21 11a2 2 0 1 1 0 4z"/>,
  search: <path d="M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3"/>,
  plus: <path d="M12 5v14M5 12h14"/>,
  chevL: <path d="M15 18l-6-6 6-6"/>,
  chevR: <path d="M9 18l6-6-6-6"/>,
  chevD: <path d="M6 9l6 6 6-6"/>,
  x: <path d="M18 6 6 18M6 6l12 12"/>,
  bell: <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0"/>,
  sun: <path d="M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>,
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>,
  phone: <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z"/>,
  mail: <path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM22 6l-10 7L2 6"/>,
  pin: <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0zM12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>,
  check: <path d="M20 6 9 17l-5-5"/>,
  clock: <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2"/>,
  download: <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>,
  spark: <path d="M12 2l1.9 5.8L20 9.7l-5.8 1.9L12 18l-1.9-6.4L4 9.7l6.1-1.9z"/>,
  send: <path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/>,
  lock: <path d="M5 11h14v11H5zM8 11V7a4 4 0 0 1 8 0v4"/>,
  info: <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 16v-4M12 8h.01"/>,
  edit: <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4z"/>,
  euro: <path d="M18 7a7 7 0 1 0 0 10M3 10h11M3 14h11"/>,
  trash: <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>,
};
const Icon = ({ d, size = 17, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={style}>{I[d]}</svg>
);

/* ---------- Données fictives (cohérentes entre écrans) ---------- */
const USER = { name: "Rémy Pavy", role: "Plombier-chauffagiste — EI", company: "Pavy Plomberie", email: "contact@pavy-plomberie.fr", phone: "06 12 34 56 78", siret: "912 345 678 00019" };

const CLIENTS = [
  { id: "C-001", name: "Marie Bertrand", type: "Particulier", city: "Nantes", addr: "12 rue des Lilas, 44000 Nantes", phone: "06 11 22 33 44", email: "marie.bertrand@email.fr", since: "Mars 2024", docs: 6, status: "client", notes: "Chaudière gaz entretenue chaque année. Préfère être jointe le matin." },
  { id: "C-002", name: "Gérard Dupont", type: "Particulier", city: "Rezé", addr: "8 allée des Chênes, 44400 Rezé", phone: "06 55 44 33 22", email: "g.dupont@email.fr", since: "Janv. 2025", docs: 3, status: "client" },
  { id: "C-003", name: "SCI Bellevue", type: "Professionnel", city: "Saint-Herblain", addr: "45 rue de la Loire, 44800 St-Herblain", phone: "02 40 55 12 12", email: "gestion@sci-bellevue.fr", since: "Sept. 2023", docs: 11, status: "client" },
  { id: "C-004", name: "Sophie Lambert", type: "Particulier", city: "Orvault", addr: "3 impasse du Bocage, 44700 Orvault", phone: "07 88 99 00 11", email: "sophie.l@email.fr", since: "Juin 2025", docs: 2, status: "client" },
  { id: "C-005", name: "Boulangerie Maison Léon", type: "Professionnel", city: "Nantes", addr: "27 pl. du Commerce, 44000 Nantes", phone: "02 40 12 34 56", email: "contact@maison-leon.fr", since: "—", docs: 1, status: "prospect", notes: "Prospect rencontré au salon. Demande de devis robinetterie + lave-vaisselle." },
  { id: "C-006", name: "Karim Haddad", type: "Particulier", city: "Vertou", addr: "15 rue de la Garenne, 44120 Vertou", phone: "06 77 88 99 10", email: "k.haddad@email.fr", since: "Fév. 2026", docs: 2, status: "prospect" },
];

const DEVIS = [
  { id: "DEV-2026-021", client: "SCI Bellevue", date: "02/10/2026", amount: 4820, status: "sent", chantier: null },
  { id: "DEV-2026-020", client: "Boulangerie Maison Léon", date: "01/10/2026", amount: 2350, status: "draft", chantier: null },
  { id: "DEV-2026-018", client: "Karim Haddad", date: "26/09/2026", amount: 1890, status: "accepted", chantier: "CH-2026-008" },
  { id: "DEV-2026-017", client: "Marie Bertrand", date: "22/09/2026", amount: 760, status: "accepted", chantier: "CH-2026-007" },
  { id: "DEV-2026-015", client: "Sophie Lambert", date: "15/09/2026", amount: 1240, status: "expired", chantier: null },
  { id: "DEV-2026-012", client: "Gérard Dupont", date: "05/09/2026", amount: 940, status: "accepted", chantier: "CH-2026-006" },
];
const devisStatus = { sent: ["Envoyé", "b-blue"], draft: ["Brouillon", "b-gray"], accepted: ["Accepté", "b-green"], expired: ["Expiré", "b-amber"], refused: ["Refusé", "b-red"] };

const CHANTIERS = [
  { id: "CH-2026-008", client: "Karim Haddad", title: "Remplacement chaudière + mise aux normes", start: "05/10/2026", end: "09/10/2026", progress: 70, status: "active", devis: "DEV-2026-018", amount: 1890 },
  { id: "CH-2026-007", client: "Marie Bertrand", title: "Réparation fuite + robinetterie SdB", start: "03/10/2026", end: "04/10/2026", progress: 100, status: "done", devis: "DEV-2026-017", amount: 760 },
  { id: "CH-2026-006", client: "Gérard Dupont", title: "Installation radiateurs (4 pièces)", start: "12/10/2026", end: "16/10/2026", progress: 0, status: "planned", devis: "DEV-2026-012", amount: 940 },
  { id: "CH-2026-005", client: "SCI Bellevue", title: "Entretien annuel immeuble (12 logts)", start: "20/09/2026", end: "21/09/2026", progress: 100, status: "done", devis: "DEV-2026-009", amount: 2160 },
];
const chantierStatus = { active: ["En cours", "b-accent"], planned: ["Planifié", "b-blue"], done: ["Terminé", "b-green"] };

const FACTURES = [
  { id: "F-2026-034", client: "SCI Bellevue", date: "22/09/2026", due: "22/10/2026", amount: 2160, paid: 2160, status: "paid", chantier: "CH-2026-005" },
  { id: "F-2026-032", client: "Marie Bertrand", date: "04/10/2026", due: "03/11/2026", amount: 760, paid: 380, status: "partial", chantier: "CH-2026-007" },
  { id: "F-2026-029", client: "Boulangerie Maison Léon", date: "18/08/2026", due: "17/09/2026", amount: 1450, paid: 0, status: "late", chantier: null },
  { id: "F-2026-025", client: "SCI Bellevue", date: "05/06/2026", due: "05/07/2026", amount: 320, paid: 320, status: "paid", chantier: null },
];
const factureStatus = { paid: ["Réglée", "b-green"], partial: ["Partiel", "b-amber"], late: ["Impayée", "b-red"], sent: ["Émise", "b-blue"] };

const PRESTATIONS = [
  { ref: "P-001", name: "Remplacement chaudière gaz condensation", unit: "forfait", price: 2450, cat: "Chauffage" },
  { ref: "P-002", name: "Dépose ancienne chaudière + évacuation", unit: "forfait", price: 280, cat: "Chauffage" },
  { ref: "P-003", name: "Pose radiateur acier 1500W", unit: "u", price: 210, cat: "Chauffage" },
  { ref: "P-004", name: "Entretien annuel chaudière", unit: "u", price: 130, cat: "Maintenance" },
  { ref: "P-005", name: "Recherche de fuite", unit: "h", price: 65, cat: "Plomberie" },
  { ref: "P-006", name: "Remplacement robinet mélangeur", unit: "u", price: 95, cat: "Plomberie" },
  { ref: "P-007", name: "Main d'œuvre (taux horaire)", unit: "h", price: 55, cat: "Main d'œuvre" },
  { ref: "P-008", name: "Déplacement zone 1 (Nantes agglo)", unit: "forfait", price: 25, cat: "Main d'œuvre" },
  { ref: "P-009", name: "Installation lave-vaisselle", unit: "forfait", price: 150, cat: "Plomberie" },
  { ref: "P-010", name: "Purge circuit chauffage", unit: "h", price: 60, cat: "Chauffage" },
];

const EVENTS = [
  { d: 5, label: "Chaudière Haddad — début", type: "ev-accent" },
  { d: 6, label: "Chaudière Haddad", type: "ev-accent" },
  { d: 8, label: "Chaudière Haddad", type: "ev-accent" },
  { d: 9, label: "Chaudière Haddad — fin", type: "ev-accent" },
  { d: 10, label: "Rappel devis Maison Léon", type: "ev-amber" },
  { d: 12, label: "Radiateurs Dupont — début", type: "ev-blue" },
  { d: 14, label: "Relance F-2026-029", type: "ev-amber" },
  { d: 16, label: "Radiateurs Dupont — fin", type: "ev-blue" },
  { d: 20, label: "Entretien Bertrand", type: "ev-green" },
  { d: 24, label: "Relance encaissements", type: "ev-amber" },
];

const EUR = (n) => n.toLocaleString("fr-FR") + " €";

/* ---------- Avatar fictif (SVG data-URI, aucune connexion requise) ---------- */
const AVATAR = "data:image/svg+xml," + encodeURIComponent(
`<svg xmlns="http://www.w3.org/2000/svg" width="168" height="168"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C05F2C"/><stop offset="1" stop-color="#8F3F1B"/></linearGradient></defs><rect width="168" height="168" fill="url(#g)"/><circle cx="84" cy="66" r="30" fill="#F6E7D8"/><path d="M28 168c6-38 28-56 56-56s50 18 56 56z" fill="#F6E7D8"/></svg>`);

/* ---------- Architecture de navigation ---------- */
const CHAPTERS = {
  crm:      { label: "CRM", icon: "users", modules: [{ id: "clients", label: "Clients & prospects" }, { id: "prospects", label: "Vue prospects" }] },
  commerce: { label: "Commerce", icon: "doc", modules: [{ id: "devis", label: "Devis" }, { id: "bons", label: "Bons de commande" }] },
  travaux:  { label: "Travaux", icon: "hard", modules: [{ id: "chantiers", label: "Chantiers" }, { id: "planning", label: "Planification" }] },
  factu:    { label: "Facturation", icon: "invoice", modules: [{ id: "factures", label: "Factures" }, { id: "avoirs", label: "Avoirs & acomptes" }] },
  treso:    { label: "Trésorerie", icon: "wallet", modules: [{ id: "flux", label: "Flux & dépenses" }, { id: "echeances", label: "Échéances" }] },
  catalogue:{ label: "Catalogue", icon: "book", modules: [{ id: "catalogue", label: "Prestations" }] },
  documents:{ label: "Documents", icon: "folder", modules: [{ id: "documents", label: "Tous les documents" }] },
};

/* ============================================================ APP */
export default function App() {
  const [dark, setDark] = useState(false);
  const [route, setRoute] = useState({ chapter: null, module: null, page: null }); // page = détail/vue
  const [profileMenu, setProfileMenu] = useState(false);
  const [leon, setLeon] = useState(false);
  const [toast, setToast] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2600);
    return () => clearTimeout(t);
  }, [toast]);

  const go = (chapter, module) => { setRoute({ chapter, module, page: null }); setSearch(""); setFilter("all"); };
  const home = () => setRoute({ chapter: null, module: null, page: null });
  const openPage = (page) => setRoute((r) => ({ ...r, page }));
  const notify = (msg) => setToast(msg);

  const chapter = route.chapter ? CHAPTERS[route.chapter] : null;

  return (
    <>
      <style>{DESIGN}</style>
      <div className="app">
        {/* ===== Barre supérieure ===== */}
        <header className="topbar">
          <div className="topbar-in">
            <button className="brand" onClick={home} title="Retour à l'accueil">
              <div className="brand-mark">B</div>
              <div>
                <div className="brand-name">BATORYA</div>
                <div className="brand-sub">Essentiel V6</div>
              </div>
            </button>
            <div style={{width:1,height:26,background:"var(--line)",margin:"0 6px"}} />
            <nav className="row" style={{gap:2,overflowX:"auto",flex:1}}>
              <button className={"chap" + (!route.chapter ? " active" : "")} onClick={home}>
                <Icon d="home" size={15}/> Accueil
              </button>
              {Object.entries(CHAPTERS).map(([id, c]) => (
                <button key={id} className={"chap" + (route.chapter === id ? " active" : "")}
                  onClick={() => go(id, c.modules[0].id)}>
                  <Icon d={c.icon} size={15}/> {c.label}
                </button>
              ))}
            </nav>
            <div className="row" style={{gap:4,flexShrink:0}}>
              <button className="btn-ghost btn btn-sm" title="Notifications" onClick={() => notify("3 rappels à traiter : relance facture F-2026-029, devis Maison Léon en attente, chaudière Haddad à finaliser.")} style={{padding:7}}>
                <Icon d="bell"/> {toast ? "" : <Badge n={3}/>}
              </button>
              <button className="btn-ghost btn btn-sm" title={dark ? "Thème clair" : "Thème sombre"} onClick={() => setDark(!dark)} style={{padding:7}}>
                <Icon d={dark ? "sun" : "moon"}/>
              </button>
              <div style={{width:1,height:26,background:"var(--line)",margin:"0 4px"}} />
              <button className="profile-btn" onClick={() => setProfileMenu(!profileMenu)}>
                <img className="avatar" src={AVATAR} alt="Photo de profil — fictive" />
                <div style={{textAlign:"left",lineHeight:1.2}}>
                  <div style={{fontSize:13,fontWeight:600}}>{USER.name}</div>
                  <div style={{fontSize:10.5,color:"var(--muted)"}}>{USER.company}</div>
                </div>
                <Icon d="chevD" size={13} style={{color:"var(--muted)"}}/>
              </button>
            </div>
          </div>
          {/* Menu profil */}
          {profileMenu && (
            <div className="menu">
              <div style={{padding:"10px 12px"}} className="row">
                <img className="avatar" style={{width:36,height:36}} src={AVATAR} alt=""/>
                <div>
                  <div style={{fontSize:13.5,fontWeight:600}}>{USER.name}</div>
                  <div style={{fontSize:11.5,color:"var(--muted)"}}>{USER.email}</div>
                </div>
              </div>
              <div className="menu-sep"/>
              <button className="menu-item" onClick={() => { openPage("profil"); setProfileMenu(false); }}><Icon d="users" size={15}/> Mon profil</button>
              <button className="menu-item" onClick={() => { openPage("parametres"); setProfileMenu(false); }}><Icon d="gear" size={15}/> Paramètres</button>
              <button className="menu-item" onClick={() => setDark(!dark)}><Icon d={dark ? "sun" : "moon"} size={15}/> {dark ? "Thème clair" : "Thème sombre"}</button>
              <div className="menu-sep"/>
              <button className="menu-item" onClick={() => notify("BATORYA Essentiel V6 — version prototype. Licence : démonstration locale.")}><Icon d="info" size={15}/> À propos de BATORYA</button>
              <button className="menu-item danger" onClick={() => notify("Session verrouillée (simulation). Les données restent sur cet ordinateur.")}><Icon d="lock" size={15}/> Verrouiller</button>
            </div>
          )}
        </header>

        {/* ===== Barre de modules contextuelle ===== */}
        {chapter && (
          <div className="modbar">
            <span className="muted" style={{fontSize:12,fontWeight:600,marginRight:8,display:"flex",alignItems:"center",gap:6}}>
              <Icon d={chapter.icon} size={14}/> {chapter.label}
            </span>
            {chapter.modules.map((m) => (
              <button key={m.id} className={"mod" + (route.module === m.id ? " active" : "")}
                onClick={() => go(route.chapter, m.id)}>{m.label}</button>
            ))}
          </div>
        )}

        {/* ===== Contenu ===== */}
        <div className="app-scroll" onClick={() => profileMenu && setProfileMenu(false)}>
          <div className="content">
            <Routes {...{ route, go, home, openPage, notify, dark, setDark, search, setSearch, filter, setFilter }} />
          </div>
        </div>
      </div>

      {/* ===== Léon ===== */}
      <button className="leon-fab" onClick={() => setLeon(!leon)} title="Léon — assistant intégré">
        {leon ? <Icon d="x" size={20}/> : <Icon d="spark" size={22}/>}
      </button>
      {leon && <Leon close={() => setLeon(false)} notify={notify} go={go}/>}

      {/* ===== Toast ===== */}
      {toast && (
        <div style={{position:"fixed",bottom:22,left:22,background:"var(--text)",color:"var(--bg)",padding:"11px 16px",borderRadius:11,fontSize:13.5,boxShadow:"0 8px 24px rgba(0,0,0,.3)",zIndex:80,maxWidth:420}}>
          {toast}
        </div>
      )}
    </>
  );
}

const Badge = ({n}) => <span style={{background:"var(--red)",color:"#fff",borderRadius:99,fontSize:10,padding:"1px 5px",fontWeight:700}}>{n}</span>;

/* ============================================================ ROUTER */
function Routes({ route, go, home, openPage, notify, dark, setDark, search, setSearch, filter, setFilter }) {
  if (route.page === "profil") return <Profil back={() => home()} notify={notify}/>;
  if (route.page === "parametres") return <Parametres dark={dark} setDark={setDark} notify={notify} back={() => home()}/>;
  if (route.page === "client") return <FicheClient id="C-001" back={() => go("crm","clients")} openPage={openPage} notify={notify}/>;
  if (route.page === "devis-edit") return <DevisEdit back={() => go("commerce","devis")} notify={notify}/>;
  if (route.page === "facture") return <FactureDetail id="F-2026-032" back={() => go("factu","factures")} notify={notify}/>;
  if (route.page === "facture-late") return <FactureDetail id="F-2026-029" back={() => go("factu","factures")} notify={notify}/>;

  switch (route.module) {
    case "clients": return <Clients search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} openPage={openPage} notify={notify}/>;
    case "prospects": return <Prospects openPage={openPage}/>;
    case "devis": return <DevisList search={search} setSearch={setSearch} openPage={openPage} notify={notify}/>;
    case "bons": return <BonsCmd notify={notify}/>;
    case "chantiers": return <Chantiers openPage={openPage}/>;
    case "planning": return <Planning/>;
    case "factures": return <Factures openPage={openPage}/>;
    case "avoirs": return <Avoirs notify={notify}/>;
    case "flux": return <Treso/>;
    case "echeances": return <Echeances/>;
    case "catalogue": return <Catalogue search={search} setSearch={setSearch} notify={notify}/>;
    case "documents": return <Documents notify={notify}/>;
    default: return <Dashboard go={go} openPage={openPage} notify={notify}/>;
  }
}

/* ============================================================ ACCUEIL */
function Dashboard({ go, openPage, notify }) {
  return (
    <>
      <div className="spread" style={{marginBottom:20}}>
        <div>
          <h1 className="page-title">Bonjour Rémy 👋</h1>
          <p className="page-sub">Samedi 10 octobre 2026 — voici l'état de votre activité. <span className="note"><Icon d="info" size={12}/> Données de démonstration fictives</span></p>
        </div>
        <div className="row">
          <button className="btn" onClick={() => notify("Formulaire de création client (démonstration).")}><Icon d="users" size={15}/> Nouveau client</button>
          <button className="btn btn-primary" onClick={() => openPage("devis-edit")}><Icon d="plus" size={15}/> Créer un devis</button>
        </div>
      </div>

      {/* KPI */}
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fit,minmax(190px,1fr))",marginBottom:20}}>
        <div className="surface kpi" style={{cursor:"pointer"}} onClick={() => go("commerce","devis")}>
          <div className="l row" style={{gap:6}}><Icon d="doc" size={14}/> Devis en attente</div>
          <div className="v">3</div>
          <div className="muted" style={{fontSize:12}}>dont 1 à relancer cette semaine</div>
        </div>
        <div className="surface kpi" style={{cursor:"pointer"}} onClick={() => go("travaux","chantiers")}>
          <div className="l row" style={{gap:6}}><Icon d="hard" size={14}/> Chantiers en cours</div>
          <div className="v">1</div>
          <div className="muted" style={{fontSize:12}}>Chaudière Haddad — 70 %</div>
        </div>
        <div className="surface kpi" style={{cursor:"pointer"}} onClick={() => go("factu","factures")}>
          <div className="l row" style={{gap:6}}><Icon d="invoice" size={14}/> À encaisser</div>
          <div className="v">{EUR(1830)}</div>
          <div className="muted" style={{fontSize:12}}>sur 3 factures non soldées</div>
        </div>
        <div className="surface kpi" style={{cursor:"pointer"}} onClick={() => go("factu","factures")}>
          <div className="l row" style={{gap:6}}><Icon d="clock" size={14}/> En retard</div>
          <div className="v" style={{color:"var(--red)"}}>{EUR(1450)}</div>
          <div className="muted" style={{fontSize:12}}>F-2026-029 — Maison Léon</div>
        </div>
      </div>

      <div className="grid" style={{gridTemplateColumns:"1.4fr 1fr",alignItems:"start"}}>
        {/* Actions à traiter */}
        <div className="surface pad">
          <div className="spread" style={{marginBottom:12}}>
            <h2 style={{margin:0,fontSize:15.5,fontWeight:700}}>À traiter</h2>
            <button className="btn btn-ghost btn-sm" onClick={() => go("treso","echeances")}>Tout voir</button>
          </div>
          <Todo icon="clock" tone="b-amber" title="Relancer la facture F-2026-029" desc="Boulangerie Maison Léon — 1 450 € en retard depuis le 17/09" act={() => openPage("facture-late")} action="Ouvrir"/>
          <Todo icon="doc" tone="b-blue" title="Devis DEV-2026-020 à finaliser" desc="Boulangerie Maison Léon — brouillon depuis le 01/10" act={() => openPage("devis-edit")} action="Modifier"/>
          <Todo icon="phone" tone="b-accent" title="Appeler Sophie Lambert" desc="Devis robinetterie expiré le 15/09 — relance courtoise conseillée" act={() => notify("Appel simulé — aucune donnée envoyée.")} action="Simuler"/>
          <Todo icon="check" tone="b-green" title="Solder la facture F-2026-032" desc="Marie Bertrand — acompte de 380 € reçu, reste 380 €" act={() => openPage("facture")} action="Ouvrir"/>
        </div>

        {/* Agenda + derniers documents */}
        <div style={{display:"grid",gap:14}}>
          <div className="surface pad">
            <h2 style={{margin:"0 0 10px",fontSize:15.5,fontWeight:700}}>Semaine prochaine</h2>
            <EventMini label="Lun 12 — Radiateurs Dupont (début)" tone="ev-blue"/>
            <EventMini label="Mer 14 — Relance F-2026-029" tone="ev-amber"/>
            <EventMini label="Ven 16 — Radiateurs Dupont (fin)" tone="ev-blue"/>
            <button className="btn btn-sm" style={{width:"100%",marginTop:10,justifyContent:"center"}} onClick={() => go("travaux","planning")}>Ouvrir la planification</button>
          </div>
          <div className="surface pad">
            <h2 style={{margin:"0 0 10px",fontSize:15.5,fontWeight:700}}>Derniers documents</h2>
            {[["F-2026-032","Facture — M. Bertrand","b-amber"],["DEV-2026-021","Devis — SCI Bellevue","b-blue"],["DEV-2026-020","Devis — Maison Léon","b-gray"]].map(([id,l,c])=>(
              <div key={id} className="row" style={{padding:"8px 0",borderBottom:"1px solid var(--line)",cursor:"pointer"}} onClick={() => notify("Ouverture du PDF « "+id+" » simulée (fichier local fictif).")}>
                <Icon d="doc" size={15} style={{color:"var(--muted)"}}/>
                <div style={{flex:1,fontSize:13}}>{l}<div className="muted" style={{fontSize:11}}>{id}</div></div>
                <span className={"badge "+c}>{c==="b-amber"?"Partiel":c==="b-blue"?"Envoyé":"Brouillon"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
const Todo = ({icon,tone,title,desc,act,action}) => (
  <div className="row" style={{padding:"11px 0",borderBottom:"1px solid var(--line)",alignItems:"flex-start"}}>
    <span className={"badge "+tone} style={{padding:6}}><Icon d={icon} size={13}/></span>
    <div style={{flex:1}}>
      <div style={{fontWeight:600,fontSize:13.5}}>{title}</div>
      <div className="muted" style={{fontSize:12.5}}>{desc}</div>
    </div>
    <button className="btn btn-sm" onClick={(e)=>{e.stopPropagation();act();}}>{action}</button>
  </div>
);
const EventMini = ({label,tone}) => (
  <div className="row" style={{gap:9,padding:"7px 0",fontSize:13}}>
    <span className={"cal-ev "+tone} style={{marginTop:0,flexShrink:0}}>{label.split("—")[0].trim().slice(0,3)}</span>
    <span>{label}</span>
  </div>
);

/* ============================================================ CRM */
function Clients({ search, setSearch, filter, setFilter, openPage, notify }) {
  const list = CLIENTS.filter(c =>
    (filter === "all" || c.status === filter) &&
    (c.name.toLowerCase().includes(search.toLowerCase()) || c.city.toLowerCase().includes(search.toLowerCase()))
  );
  return (
    <>
      <h1 className="page-title">Clients & prospects</h1>
      <p className="page-sub">{CLIENTS.length} fiches enregistrées localement sur cet ordinateur.</p>
      <div className="spread" style={{marginBottom:14}}>
        <div className="row">
          <div style={{position:"relative",width:260}}>
            <span style={{position:"absolute",left:11,top:9,color:"var(--muted)"}}><Icon d="search" size={15}/></span>
            <input className="input" style={{paddingLeft:34}} placeholder="Rechercher un nom, une ville…" value={search} onChange={(e)=>setSearch(e.target.value)}/>
          </div>
          {[["all","Tous"],["client","Clients"],["prospect","Prospects"]].map(([id,l])=>(
            <button key={id} className={"chip "+(filter===id?"on":"")} onClick={()=>setFilter(id)}>{l}</button>
          ))}
        </div>
        <button className="btn btn-primary" onClick={() => notify("Fiche « Nouveau client » (démonstration) — rien n'est enregistré.")}><Icon d="plus" size={15}/> Nouveau client</button>
      </div>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Nom</th><th>Type</th><th>Ville</th><th>Téléphone</th><th>Depuis</th><th>Documents</th></tr></thead>
          <tbody>
            {list.map(c => (
              <tr key={c.id} onClick={() => c.id === "C-001" ? openPage("client") : notify("Démonstration : seule la fiche de Marie Bertrand est détaillée.")}>
                <td>
                  <div style={{fontWeight:600}}>{c.name}</div>
                  <div className="muted" style={{fontSize:11.5}}>{c.id}</div>
                </td>
                <td className="muted">{c.type}</td>
                <td>{c.city}</td>
                <td className="muted">{c.phone}</td>
                <td className="muted">{c.since}</td>
                <td><span className={"badge "+(c.status==="client"?"b-green":"b-amber")}>{c.status==="client"?"Client":"Prospect"}</span></td>
              </tr>
            ))}
            {list.length===0 && <tr><td colSpan={6} style={{textAlign:"center",padding:30,color:"var(--muted)"}}>Aucun résultat. Essayez un autre nom ou filtre.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Prospects({ openPage }) {
  const ps = CLIENTS.filter(c=>c.status==="prospect");
  return (
    <>
      <h1 className="page-title">Prospects</h1>
      <p className="page-sub">Contacts en phase de devis, sans engagement en cours.</p>
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))"}}>
        {ps.map(p=>(
          <div key={p.id} className="surface pad">
            <div className="spread">
              <div>
                <div style={{fontWeight:700,fontSize:15}}>{p.name}</div>
                <div className="muted" style={{fontSize:12.5}}>{p.type} · {p.city}</div>
              </div>
              <span className="badge b-amber">Prospect</span>
            </div>
            <div className="row" style={{gap:14,margin:"12px 0 8px",fontSize:12.5,color:"var(--muted)"}}>
              <span className="row" style={{gap:5}}><Icon d="phone" size={13}/>{p.phone}</span>
              <span className="row" style={{gap:5}}><Icon d="mail" size={13}/>{p.email}</span>
            </div>
            {p.notes && <p style={{fontSize:12.5,color:"var(--muted)",margin:"6px 0 12px"}}>{p.notes}</p>}
            <div className="row">
              <button className="btn btn-sm" onClick={()=>openPage("devis-edit")}><Icon d="plus" size={13}/> Devis</button>
              <button className="btn btn-ghost btn-sm"><Icon d="edit" size={13}/> Fiche</button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function FicheClient({ back, openPage, notify }) {
  const c = CLIENTS[0];
  return (
    <>
      <div className="breadcrumb">
        <button className="back" onClick={back}><Icon d="chevL" size={13}/> CRM</button> <span>/</span> <b>{c.name}</b>
      </div>
      <div className="surface pad" style={{marginBottom:16}}>
        <div className="spread" style={{flexWrap:"wrap",gap:14}}>
          <div className="row" style={{gap:14}}>
            <img className="avatar-lg" src={AVATAR} alt="Avatar fictif" style={{borderRadius:20}}/>
            <div>
              <h1 style={{margin:"0 0 3px",fontSize:20,fontWeight:750}}>{c.name}</h1>
              <div className="muted" style={{fontSize:13}}>{c.id} · Client depuis {c.since}</div>
              <div className="row" style={{gap:8,marginTop:8}}>
                <span className="badge b-green">Client actif</span>
                <span className="badge b-gray">{c.docs} documents</span>
              </div>
            </div>
          </div>
          <div className="row">
            <button className="btn" onClick={()=>notify("Appel simulé — le logiciel compose le numéro localement.")}><Icon d="phone" size={14}/> Appeler</button>
            <button className="btn btn-primary" onClick={()=>openPage("devis-edit")}><Icon d="plus" size={14}/> Nouveau devis</button>
          </div>
        </div>
      </div>
      <div className="grid" style={{gridTemplateColumns:"1fr 1.6fr",alignItems:"start"}}>
        <div className="surface pad">
          <h2 style={{margin:"0 0 12px",fontSize:15,fontWeight:700}}>Coordonnées</h2>
          <Info icon="pin" label="Adresse" value={c.addr}/>
          <Info icon="phone" label="Téléphone" value={c.phone}/>
          <Info icon="mail" label="E-mail" value={c.email}/>
          <Info icon="doc" label="Type" value={c.type}/>
          <div style={{marginTop:14}}>
            <label className="f">Note interne</label>
            <div className="note" style={{display:"block",lineHeight:1.5}}>{c.notes}</div>
          </div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 12px",fontSize:15,fontWeight:700}}>Historique</h2>
          <table className="tbl">
            <thead><tr><th>Document</th><th>Date</th><th className="num">Montant</th><th>Statut</th></tr></thead>
            <tbody>
              <tr onClick={()=>openPage("facture")}><td><b>Facture</b> F-2026-032</td><td>04/10/2026</td><td className="num">{EUR(760)}</td><td><span className="badge b-amber">Partiel — 380 € reçus</span></td></tr>
              <tr><td><b>Chantier</b> CH-2026-007 — Fuite + robinetterie</td><td>03/10/2026</td><td className="num">{EUR(760)}</td><td><span className="badge b-green">Terminé</span></td></tr>
              <tr><td><b>Devis</b> DEV-2026-017</td><td>22/09/2026</td><td className="num">{EUR(760)}</td><td><span className="badge b-green">Accepté</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
const Info = ({icon,label,value}) => (
  <div className="row" style={{gap:11,marginBottom:11,alignItems:"flex-start"}}>
    <Icon d={icon} size={15} style={{color:"var(--muted)",marginTop:2}}/>
    <div><div className="f" style={{margin:0}}>{label}</div><div style={{fontSize:13.5}}>{value}</div></div>
  </div>
);

/* ============================================================ COMMERCE */
function DevisList({ search, setSearch, openPage, notify }) {
  const list = DEVIS.filter(d => d.client.toLowerCase().includes(search.toLowerCase()) || d.id.toLowerCase().includes(search.toLowerCase()));
  return (
    <>
      <div className="spread">
        <div>
          <h1 className="page-title">Devis</h1>
          <p className="page-sub">Suivez l'état de vos propositions commerciales.</p>
        </div>
        <button className="btn btn-primary" onClick={() => openPage("devis-edit")}><Icon d="plus" size={15}/> Nouveau devis</button>
      </div>
      <div style={{position:"relative",maxWidth:320,marginBottom:14}}>
        <span style={{position:"absolute",left:11,top:9,color:"var(--muted)"}}><Icon d="search" size={15}/></span>
        <input className="input" style={{paddingLeft:34}} placeholder="Rechercher un devis ou un client…" value={search} onChange={(e)=>setSearch(e.target.value)}/>
      </div>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Numéro</th><th>Client</th><th>Date</th><th className="num">Montant</th><th>Statut</th><th>Chantier</th></tr></thead>
          <tbody>
            {list.map(d => {
              const [l,c] = devisStatus[d.status];
              return (
                <tr key={d.id} onClick={() => d.id === "DEV-2026-020" ? openPage("devis-edit") : notify("Consultation du devis "+d.id+" simulée (PDF local fictif).")}>
                  <td><b>{d.id}</b></td><td>{d.client}</td><td className="muted">{d.date}</td>
                  <td className="num"><b>{EUR(d.amount)}</b></td>
                  <td><span className={"badge "+c}>{l}</span></td>
                  <td className="muted">{d.chantier || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

function DevisEdit({ back, notify }) {
  const [lines, setLines] = useState([
    { ref:"P-001", name:"Remplacement chaudière gaz condensation", qty:1, unit:"forfait", price:2450 },
    { ref:"P-002", name:"Dépose ancienne chaudière + évacuation", qty:1, unit:"forfait", price:280 },
  ]);
  const [picker, setPicker] = useState(false);
  const total = lines.reduce((s,l)=>s+l.qty*l.price,0);
  return (
    <>
      <div className="breadcrumb">
        <button className="back" onClick={back}><Icon d="chevL" size={13}/> Commerce</button> <span>/</span> <b>Nouveau devis</b>
      </div>
      <div className="spread" style={{marginBottom:16}}>
        <h1 className="page-title" style={{margin:0}}>Nouveau devis</h1>
        <div className="row">
          <button className="btn" onClick={back}>Annuler</button>
          <button className="btn" onClick={()=>notify("Devis enregistré comme brouillon (simulation).")}><Icon d="doc" size={14}/> Enregistrer en brouillon</button>
          <button className="btn btn-primary" onClick={()=>notify("Aperçu PDF du devis généré localement (simulation).")}><Icon d="check" size={14}/> Finaliser le devis</button>
        </div>
      </div>
      <div className="grid" style={{gridTemplateColumns:"1fr 1.8fr",alignItems:"start"}}>
        <div className="surface pad">
          <h2 style={{margin:"0 0 12px",fontSize:15,fontWeight:700}}>Client</h2>
          <div className="field">
            <label className="f">Client concerné</label>
            <select className="input"><option>Boulangerie Maison Léon</option><option>Marie Bertrand</option><option>SCI Bellevue</option><option>— Nouveau client —</option></select>
          </div>
          <div className="field">
            <label className="f">Adresse d'intervention</label>
            <input className="input" defaultValue="27 pl. du Commerce, 44000 Nantes"/>
          </div>
          <div className="row" style={{gap:10}}>
            <div className="field" style={{flex:1}}><label className="f">Date</label><input className="input" defaultValue="10/10/2026"/></div>
            <div className="field" style={{flex:1}}><label className="f">Validité</label><input className="input" defaultValue="30 jours"/></div>
          </div>
          <div className="note"><Icon d="info" size={12}/> TVA non applicable, art. 293 B du CGI — affiché sur le devis.</div>
        </div>
        <div>
          <div className="surface pad" style={{marginBottom:14}}>
            <div className="spread" style={{marginBottom:8}}>
              <h2 style={{margin:0,fontSize:15,fontWeight:700}}>Prestations</h2>
              <button className="btn btn-sm" onClick={()=>setPicker(!picker)}><Icon d="plus" size={13}/> Ajouter depuis le catalogue</button>
            </div>
            {picker && (
              <div style={{border:"1px solid var(--line)",borderRadius:11,padding:10,marginBottom:12,background:"var(--surface2)"}}>
                <div style={{position:"relative",marginBottom:8}}>
                  <span style={{position:"absolute",left:10,top:8,color:"var(--muted)"}}><Icon d="search" size={14}/></span>
                  <input className="input" style={{paddingLeft:32,fontSize:12.5}} placeholder="Rechercher une prestation…"/>
                </div>
                {PRESTATIONS.slice(0,4).map(p=>(
                  <button key={p.ref} className="menu-item" style={{fontSize:13}} onClick={()=>{setLines([...lines,{ref:p.ref,name:p.name,qty:1,unit:p.unit,price:p.price}]);setPicker(false);notify("« "+p.name+" » ajouté au devis (simulation).");}}>
                    <Icon d="plus" size={13}/> {p.name} <span className="muted" style={{marginLeft:"auto",fontSize:11.5}}>{EUR(p.price)} / {p.unit}</span>
                  </button>
                ))}
              </div>
            )}
            <table className="tbl">
              <thead><tr><th>Prestation</th><th style={{width:70}}>Qté</th><th>Unité</th><th className="num">PU</th><th className="num">Total</th><th></th></tr></thead>
              <tbody>
                {lines.map((l,i)=>(
                  <tr key={i} style={{cursor:"default"}}>
                    <td><div style={{fontWeight:600}}>{l.name}</div><div className="muted" style={{fontSize:11}}>{l.ref}</div></td>
                    <td><input className="input" style={{padding:"5px 8px"}} type="number" defaultValue={l.qty}
                      onChange={(e)=>{const q=Math.max(0,+e.target.value||0);const nl=[...lines];nl[i]={...l,qty:q};setLines(nl);}}/></td>
                    <td className="muted">{l.unit}</td>
                    <td className="num">{EUR(l.price)}</td>
                    <td className="num"><b>{EUR(l.qty*l.price)}</b></td>
                    <td><button className="btn-ghost btn btn-sm" style={{color:"var(--red)"}} onClick={()=>setLines(lines.filter((_,j)=>j!==i))}><Icon d="trash" size={14}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="surface pad" style={{display:"flex",justifyContent:"flex-end"}}>
            <div style={{minWidth:240}}>
              <div className="spread" style={{marginBottom:6}}><span className="muted">Sous-total</span><b>{EUR(total)}</b></div>
              <div className="spread" style={{marginBottom:6}}><span className="muted">TVA</span><span className="muted">Non applicable</span></div>
              <div className="spread" style={{borderTop:"1px solid var(--line)",paddingTop:8}}><span style={{fontWeight:700}}>Total HT</span><span style={{fontWeight:750,fontSize:17}}>{EUR(total)}</span></div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function BonsCmd({ notify }) {
  return (
    <>
      <h1 className="page-title">Bons de commande</h1>
      <p className="page-sub">Commandes fournisseurs liées à vos chantiers.</p>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Numéro</th><th>Fournisseur</th><th>Chantier</th><th className="num">Montant</th><th>Statut</th></tr></thead>
          <tbody>
            {[["BC-2026-011","Frise Matériaux","CH-2026-008",1240,"received"],["BC-2026-010","HeatingPro","CH-2026-008",780,"sent"],["BC-2026-008","Frise Matériaux","CH-2026-006",520,"sent"]].map(([id,f,c,m,s])=>(
              <tr key={id} onClick={()=>notify("Bon de commande "+id+" (PDF local fictif).")}>
                <td><b>{id}</b></td><td>{f}</td><td className="muted">{c}</td><td className="num">{EUR(m)}</td>
                <td><span className={"badge "+(s==="received"?"b-green":"b-blue")}>{s==="received"?"Réceptionné":"Envoyé"}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ============================================================ TRAVAUX */
function Chantiers({ openPage }) {
  return (
    <>
      <div className="spread">
        <div>
          <h1 className="page-title">Chantiers</h1>
          <p className="page-sub">Suivi opérationnel de vos travaux en cours et planifiés.</p>
        </div>
        <div className="row">
          <button className="btn"><Icon d="calendar" size={14}/> Vue planification</button>
          <button className="btn btn-primary"><Icon d="plus" size={14}/> Nouveau chantier</button>
        </div>
      </div>
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fill,minmax(320px,1fr))"}}>
        {CHANTIERS.map(ch => {
          const [l,c] = chantierStatus[ch.status];
          return (
            <div key={ch.id} className="surface pad" style={{cursor:"pointer"}} onClick={() => openPage && null}>
              <div className="spread" style={{marginBottom:8}}>
                <span className="muted" style={{fontSize:12,fontWeight:600}}>{ch.id}</span>
                <span className={"badge "+c}>{l}</span>
              </div>
              <div style={{fontWeight:700,fontSize:15,lineHeight:1.35}}>{ch.title}</div>
              <div className="muted" style={{fontSize:12.5,margin:"4px 0 10px"}}>{ch.client}</div>
              <div className="row" style={{gap:14,fontSize:12.5,color:"var(--muted)",marginBottom:12}}>
                <span className="row" style={{gap:5}}><Icon d="calendar" size={13}/>{ch.start} → {ch.end}</span>
                <span className="row" style={{gap:5}}><Icon d="euro" size={13}/>{EUR(ch.amount)}</span>
              </div>
              <div className="progress" style={{marginBottom:6}}><div style={{width:ch.progress+"%",background:ch.progress===100?"var(--green)":"var(--accent)"}}/></div>
              <div className="row" style={{justifyContent:"space-between"}}>
                <span className="muted" style={{fontSize:11.5}}>{ch.progress}% · Devis {ch.devis}</span>
                <button className="btn btn-sm" onClick={(e)=>e.stopPropagation()}>Ouvrir</button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function Planning() {
  const days = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"];
  const start = 29; // sept, mois affiché : octobre 2026 (démarre jeudi) — grille simplifiée
  const cells = [];
  const first = new Date(2026, 9, 1).getDay(); // thu=4 -> index 3 (lun-based)
  for (let i = 0; i < first - 1; i++) cells.push(null);
  for (let d = 1; d <= 31; d++) cells.push(d);
  return (
    <>
      <div className="spread">
        <div>
          <h1 className="page-title">Planification</h1>
          <p className="page-sub">Octobre 2026 — planning local, sans synchronisation externe.</p>
        </div>
        <div className="row">
          <button className="btn btn-sm"><Icon d="chevL" size={14}/></button>
          <button className="btn btn-sm">Aujourd'hui</button>
          <button className="btn btn-sm"><Icon d="chevR" size={14}/></button>
          <span style={{fontWeight:600,minWidth:110}}>Octobre 2026</span>
        </div>
      </div>
      <div className="surface pad" style={{marginTop:4}}>
        <div className="cal" style={{marginBottom:6}}>
          {days.map(d => <div key={d} style={{fontSize:11.5,fontWeight:600,color:"var(--muted)",textTransform:"uppercase",letterSpacing:.4}}>{d}</div>)}
        </div>
        <div className="cal">
          {cells.map((d,i) => d === null ? <div key={i} className="cal-day other"/> : (
            <div key={i} className={"cal-day" + (d===10 ? " today":"")}>
              <div style={{fontWeight:600,color:d===10?"var(--accent)":undefined}}>{d}</div>
              {EVENTS.filter(e=>e.d===d).map(e=>(
                <div key={e.label} className={"cal-ev "+e.type}>{e.label}</div>
              ))}
            </div>
          ))}
        </div>
        <div className="row" style={{gap:14,marginTop:12,flexWrap:"wrap"}}>
          {[["Chantiers","ev-accent"],["Facturation","ev-amber"],["Rendez-vous","ev-blue"],["Maintenance","ev-green"]].map(([l,c])=>(
            <span key={l} className="row" style={{gap:6,fontSize:12,color:"var(--muted)"}}><span className={"cal-ev "+c} style={{marginTop:0,width:12,height:12,padding:0}}/> {l}</span>
          ))}
        </div>
      </div>
    </>
  );
}

/* ============================================================ FACTURATION */
function Factures({ openPage }) {
  return (
    <>
      <div className="spread">
        <div>
          <h1 className="page-title">Factures</h1>
          <p className="page-sub">Encaissé ce mois : 2 860 € · Restant dû : 1 830 €.</p>
        </div>
        <button className="btn btn-primary"><Icon d="plus" size={14}/> Créer une facture</button>
      </div>
      <div className="row" style={{gap:8,marginBottom:14}}>
        <button className="chip on">Toutes</button><button className="chip">Émises</button><button className="chip">Partielles</button><button className="chip">Impayées</button><button className="chip">Réglées</button>
      </div>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Facture</th><th>Client</th><th>Date</th><th>Échéance</th><th className="num">Montant</th><th className="num">Reste dû</th><th>Statut</th></tr></thead>
          <tbody>
            {FACTURES.map(f => {
              const [l,c] = factureStatus[f.status];
              return (
                <tr key={f.id} onClick={() => f.id.startsWith("F-2026-03") ? openPage(f.status==="late"?"facture-late":"facture") : null}>
                  <td><b>{f.id}</b></td><td>{f.client}</td>
                  <td className="muted">{f.date}</td>
                  <td className="muted" style={{color:f.status==="late"?"var(--red)":undefined}}>{f.due}</td>
                  <td className="num">{EUR(f.amount)}</td>
                  <td className="num" style={{fontWeight:700,color:f.amount-f.paid>0?"var(--text)":undefined}}>{EUR(f.amount-f.paid)}</td>
                  <td><span className={"badge "+c}>{l}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

function FactureDetail({ id, back, notify }) {
  const f = FACTURES.find(x=>x.id===id) || FACTURES[1];
  const late = f.status === "late";
  return (
    <>
      <div className="breadcrumb">
        <button className="back" onClick={back}><Icon d="chevL" size={13}/> Facturation</button> <span>/</span> <b>{f.id}</b>
      </div>
      <div className="spread" style={{marginBottom:16,flexWrap:"wrap",gap:12}}>
        <div className="row" style={{gap:12}}>
          <h1 className="page-title" style={{margin:0}}>{f.id}</h1>
          <span className={"badge "+(late?"b-red":factureStatus[f.status][1])} style={{padding:"5px 11px"}}>{late?"Impayée — relance nécessaire":factureStatus[f.status][0]}</span>
        </div>
        <div className="row">
          <button className="btn" onClick={()=>notify("PDF « "+f.id+" » ouvert localement (fichier fictif).")}><Icon d="download" size={14}/> PDF</button>
          <button className="btn" disabled={!late}><Icon d="mail" size={14}/> Envoyer un rappel</button>
          <button className="btn btn-primary" onClick={()=>notify("Encaissement de "+EUR(f.amount-f.paid)+" enregistré (simulation — aucune donnée réelle).")}>
            <Icon d="check" size={14}/> Enregistrer un encaissement
          </button>
        </div>
      </div>
      <div className="grid" style={{gridTemplateColumns:"1.7fr 1fr",alignItems:"start"}}>
        <div className="surface pad" style={{marginBottom:14}}>
          <div className="spread" style={{marginBottom:10}}>
            <div>
              <div style={{fontWeight:700,fontSize:15}}>{f.client}</div>
              <div className="muted" style={{fontSize:12.5}}>Chantier {f.chantier || "—"}</div>
            </div>
            <div className="muted" style={{fontSize:12.5,textAlign:"right"}}>
              Émise le {f.date}<br/>Échéance {f.due}
            </div>
          </div>
          <table className="tbl">
            <thead><tr><th>Prestation</th><th className="num">Qté</th><th className="num">PU</th><th className="num">Total</th></tr></thead>
            <tbody>
              <tr style={{cursor:"default"}}><td>Recherche de fuite + réparation</td><td className="num">3 h</td><td className="num">{EUR(65)}</td><td className="num">{EUR(195)}</td></tr>
              <tr style={{cursor:"default"}}><td>Remplacement robinet mélangeur</td><td className="num">2</td><td className="num">{EUR(95)}</td><td className="num">{EUR(190)}</td></tr>
              <tr style={{cursor:"default"}}><td>Main d'œuvre complémentaire</td><td className="num">6,5 h</td><td className="num">{EUR(55)}</td><td className="num">{EUR(357.5)}</td></tr>
              <tr style={{cursor:"default"}}><td>Déplacement zone 1</td><td className="num">1</td><td className="num">{EUR(25)}</td><td className="num">{EUR(25)}</td></tr>
            </tbody>
          </table>
          <div style={{display:"flex",justifyContent:"flex-end",marginTop:10,minWidth:220}}>
            <div>
              <div className="spread" style={{marginBottom:4}}><span className="muted">Total HT</span><b>{EUR(f.amount)}</b></div>
              <div className="spread"><span className="muted">TVA</span><span className="muted">Non applicable</span></div>
            </div>
          </div>
        </div>
        <div style={{display:"grid",gap:14}}>
          <div className="surface pad">
            <h2 style={{margin:"0 0 12px",fontSize:15,fontWeight:700}}>Règlements</h2>
            {f.paid > 0 ? (
              <div className="row" style={{justifyContent:"space-between",paddingBottom:10,borderBottom:"1px solid var(--line)"}}>
                <div>
                  <div style={{fontWeight:600,fontSize:13.5}}>Acompte reçu</div>
                  <div className="muted" style={{fontSize:12}}>05/10/2026 · Virement</div>
                </div>
                <b>{EUR(f.paid)}</b>
              </div>
            ) : <div className="muted" style={{fontSize:13,marginBottom:10}}>Aucun règlement enregistré.</div>}
            <div className="spread" style={{paddingTop:10}}>
              <span style={{fontWeight:600,fontSize:13.5,color:late?"var(--red)":"var(--accent)"}}>Reste dû</span>
              <b style={{fontSize:17,color:late?"var(--red)":"var(--accent)"}}>{EUR(f.amount-f.paid)}</b>
            </div>
          </div>
          <div className="surface pad">
            <h2 style={{margin:"0 0 10px",fontSize:15,fontWeight:700}}>Documents associés</h2>
            {[["doc","Devis DEV-2026-017 (PDF)"],["folder","Chantier CH-2026-007"]].map(([i,l])=>(
              <button key={l} className="menu-item" onClick={()=>notify("Ouverture locale simulée : "+l+".")}><Icon d={i} size={15}/> {l}</button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function Avoirs({ notify }) {
  return (
    <>
      <h1 className="page-title">Avoirs & acomptes</h1>
      <p className="page-sub">Documents d'ajustement et règlements partiels.</p>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Numéro</th><th>Type</th><th>Client</th><th className="num">Montant</th><th>Statut</th></tr></thead>
          <tbody>
            {[["AV-2026-003","Avoir","Marie Bertrand",120,"applied"],["AV-2026-002","Avoir","SCI Bellevue",80,"applied"],["AC-2026-011","Acompte","Marie Bertrand",380,"received"],["AC-2026-010","Acompte","SCI Bellevue",500,"received"]].map(([id,t,c,m,s])=>(
              <tr key={id} onClick={()=>notify("Document "+id+" (fictif).")}>
                <td><b>{id}</b></td><td className="muted">{t}</td><td>{c}</td><td className="num">{EUR(m)}</td>
                <td><span className={"badge "+(s==="applied"?"b-green":"b-blue")}>{s==="applied"?"Imputé":"Reçu"}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ============================================================ TRÉSORERIE */
function Treso() {
  const bars = [["Juin",2600],["Juil",3100],["Août",2950],["Sept",3480],["Oct*",2860]];
  const max = Math.max(...bars.map(b=>b[1]));
  return (
    <>
      <h1 className="page-title">Flux & dépenses</h1>
      <p className="page-sub">Lecture simple de vos entrées et sorties d'argent. <span className="note"><Icon d="info" size={12}/> Données fictives — * mois en cours</span></p>
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",marginBottom:18}}>
        <div className="surface kpi"><div className="l">Encaissé (oct.)</div><div className="v" style={{color:"var(--green)"}}>{EUR(2860)}</div></div>
        <div className="surface kpi"><div className="l">Dépenses (oct.)</div><div className="v" style={{color:"var(--red)"}}>{EUR(1240)}</div></div>
        <div className="surface kpi"><div className="l">Restant à recevoir</div><div className="v">{EUR(1830)}</div></div>
        <div className="surface kpi"><div className="l">Disponible (est.)</div><div className="v">{EUR(4450)}</div></div>
      </div>
      <div className="grid" style={{gridTemplateColumns:"1.3fr 1fr",alignItems:"start"}}>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>Encaissements mensuels</h2>
          <div className="row" style={{alignItems:"flex-end",gap:14,height:150}}>
            {bars.map(([m,v])=>(
              <div key={m} style={{flex:1,textAlign:"center"}}>
                <div style={{background:"var(--accent-soft)",borderRadius:"8px 8px 4px 4px",height:(v/max*110)+"px",position:"relative"}}>
                  <div style={{background:"var(--accent)",borderRadius:"8px 8px 4px 4px",height:"100%",opacity:.85,width:m==="Oct*"?"55%":"100%",margin:"0 auto"}}/>
                </div>
                <div className="muted" style={{fontSize:11.5,marginTop:6}}>{m}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 12px",fontSize:15,fontWeight:700}}>Derniers mouvements</h2>
          {[["+380","Acompte Bertrand","green"],["-780","HeatingPro — chaudière","red"],["+2160","SCI Bellevue","green"],["-460","Frise Matériaux","red"]].map(([v,l,c])=>(
            <div key={l} className="row" style={{justifyContent:"space-between",padding:"9px 0",borderBottom:"1px solid var(--line)"}}>
              <span style={{fontSize:13.5}}>{l}</span>
              <b style={{color:c==="green"?"var(--green)":"var(--red)"}}>{v} €</b>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function Echeances() {
  return (
    <>
      <h1 className="page-title">Échéances</h1>
      <p className="page-sub">Ce qui attend une action de votre côté.</p>
      <div className="surface pad">
        {[["F-2026-029","Relance impayée — Boulangerie Maison Léon","17/09/2026","b-red","1 450 €"],
          ["DEV-2026-021","Relance devis — SCI Bellevue","12/10/2026","b-blue","4 820 €"],
          ["F-2026-032","Solde attendu — Marie Bertrand","03/11/2026","b-amber","380 €"],
          ["CH-2026-006","Démarrage chantier — Gérard Dupont","12/10/2026","b-accent",""]].map(([id,l,d,c,m])=>(
          <div key={id} className="row" style={{justifyContent:"space-between",padding:"12px 0",borderBottom:"1px solid var(--line)"}}>
            <div>
              <div style={{fontWeight:600,fontSize:13.5}}>{l}</div>
              <div className="muted" style={{fontSize:12}}>{id} · échéance {d}</div>
            </div>
            <div className="row">
              {m && <b style={{minWidth:70,textAlign:"right"}}>{m}</b>}
              <span className={"badge "+c}>{c==="b-red"?"Retard":c==="b-amber"?"À venir":"À traiter"}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ============================================================ CATALOGUE */
function Catalogue({ search, setSearch, notify }) {
  const cats = ["Tout","Chauffage","Plomberie","Maintenance","Main d'œuvre"];
  const [cat, setCat] = useState("Tout");
  const list = PRESTATIONS.filter(p => (cat==="Tout"||p.cat===cat) && p.name.toLowerCase().includes(search.toLowerCase()));
  return (
    <>
      <div className="spread">
        <div>
          <h1 className="page-title">Catalogue de prestations</h1>
          <p className="page-sub">Vos prestations réutilisables pour devis et factures.</p>
        </div>
        <button className="btn btn-primary" onClick={()=>notify("Nouvelle prestation (démonstration).")}><Icon d="plus" size={14}/> Nouvelle prestation</button>
      </div>
      <div className="spread" style={{marginBottom:14,flexWrap:"wrap",gap:10}}>
        <div style={{position:"relative",width:280}}>
          <span style={{position:"absolute",left:11,top:9,color:"var(--muted)"}}><Icon d="search" size={15}/></span>
          <input className="input" style={{paddingLeft:34}} placeholder="Rechercher une prestation…" value={search} onChange={(e)=>setSearch(e.target.value)}/>
        </div>
        <div className="row">{cats.map(c=>(<button key={c} className={"chip "+(cat===c?"on":"")} onClick={()=>setCat(c)}>{c}</button>))}</div>
      </div>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Réf.</th><th>Libellé</th><th>Catégorie</th><th>Unité</th><th className="num">Prix</th><th></th></tr></thead>
          <tbody>
            {list.map(p=>(
              <tr key={p.ref} style={{cursor:"default"}}>
                <td className="muted">{p.ref}</td>
                <td style={{fontWeight:600}}>{p.name}</td>
                <td><span className="badge b-gray">{p.cat}</span></td>
                <td className="muted">{p.unit}</td>
                <td className="num"><b>{EUR(p.price)}</b></td>
                <td><button className="btn btn-sm" onClick={()=>notify("« "+p.name+" » prêt à être inséré dans un document (simulation).")}><Icon d="plus" size={13}/> Utiliser</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ============================================================ DOCUMENTS */
function Documents({ notify }) {
  const groups = [
    ["Factures", 4, "invoice"], ["Devis", 6, "doc"], ["Bons de commande", 3, "folder"], ["Avoirs & acomptes", 4, "wallet"],
  ];
  return (
    <>
      <h1 className="page-title">Documents</h1>
      <p className="page-sub">Tous les fichiers générés, stockés localement sur cet ordinateur.</p>
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fill,minmax(230px,1fr))",marginBottom:18}}>
        {groups.map(([l,n,i])=>(
          <div key={l} className="surface kpi" style={{cursor:"pointer"}} onClick={()=>notify("Dossier « "+l+" » — "+n+" fichiers fictifs.")}>
            <div className="l row" style={{gap:7}}><Icon d={i} size={15}/> {l}</div>
            <div className="v">{n}</div>
            <div className="muted" style={{fontSize:12}}>documents PDF</div>
          </div>
        ))}
      </div>
      <div className="surface" style={{overflow:"hidden"}}>
        <table className="tbl">
          <thead><tr><th>Fichier</th><th>Type</th><th>Client</th><th>Date</th><th>Taille</th></tr></thead>
          <tbody>
            {[["F-2026-034.pdf","Facture","SCI Bellevue","22/09/2026","48 Ko"],["DEV-2026-021.pdf","Devis","SCI Bellevue","02/10/2026","52 Ko"],["CH-2026-008 — photos.zip","Chantier","Karim Haddad","08/10/2026","3,2 Mo"],["BC-2026-011.pdf","Bon de commande","Frise Matériaux","04/10/2026","39 Ko"]].map(([f,t,c,d,s])=>(
              <tr key={f} onClick={()=>notify("Ouverture locale simulée : "+f+".")}>
                <td><b>{f}</b></td><td className="muted">{t}</td><td>{c}</td><td className="muted">{d}</td><td className="muted">{s}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ============================================================ PROFIL & PARAMÈTRES */
function Profil({ back, notify }) {
  const [edit, setEdit] = useState(false);
  return (
    <>
      <div className="breadcrumb">
        <button className="back" onClick={back}><Icon d="chevL" size={13}/> Accueil</button> <span>/</span> <b>Mon profil</b>
      </div>
      <div className="spread" style={{marginBottom:16}}>
        <h1 className="page-title" style={{margin:0}}>Mon profil</h1>
        <button className="btn" onClick={()=>setEdit(!edit)}><Icon d="edit" size={14}/> {edit ? "Terminer" : "Modifier"}</button>
      </div>
      <div className="grid" style={{gridTemplateColumns:"300px 1fr",alignItems:"start"}}>
        <div className="surface pad" style={{textAlign:"center"}}>
          <img className="avatar-lg" src={AVATAR} alt="Photo de profil fictive" style={{margin:"6px auto 12px",display:"block"}}/>
          <div style={{fontWeight:750,fontSize:17}}>{USER.name}</div>
          <div className="muted" style={{fontSize:13,marginBottom:4}}>{USER.role}</div>
          <span className="badge b-accent">Compte local</span>
          <div className="note" style={{marginTop:14,fontSize:11}}><Icon d="info" size={12}/> Photo fictive — stockée localement</div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>Informations professionnelles</h2>
          <div className="grid" style={{gridTemplateColumns:"1fr 1fr"}}>
            <div className="field"><label className="f">Nom complet</label><input className="input" defaultValue={USER.name} disabled={!edit}/></div>
            <div className="field"><label className="f">Entreprise</label><input className="input" defaultValue={USER.company} disabled={!edit}/></div>
            <div className="field"><label className="f">E-mail</label><input className="input" defaultValue={USER.email} disabled={!edit}/></div>
            <div className="field"><label className="f">Téléphone</label><input className="input" defaultValue={USER.phone} disabled={!edit}/></div>
            <div className="field"><label className="f">SIRET</label><input className="input" defaultValue={USER.siret} disabled={!edit}/></div>
            <div className="field"><label className="f">Mentions TVA</label><input className="input" defaultValue="TVA non applicable, art. 293 B du CGI" disabled={!edit}/></div>
          </div>
          {edit && <button className="btn btn-primary" onClick={()=>{notify("Modifications enregistrées (simulation).");setEdit(false);}}><Icon d="check" size={14}/> Enregistrer</button>}
        </div>
      </div>
    </>
  );
}

function Parametres({ dark, setDark, notify, back }) {
  return (
    <>
      <div className="breadcrumb">
        <button className="back" onClick={back}><Icon d="chevL" size={13}/> Accueil</button> <span>/</span> <b>Paramètres</b>
      </div>
      <h1 className="page-title">Paramètres</h1>
      <p className="page-sub">Préférences locales — rien n'est synchronisé avec un service distant.</p>
      <div className="grid" style={{gridTemplateColumns:"repeat(auto-fit,minmax(330px,1fr))"}}>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>Apparence</h2>
          <label className="f">Thème de l'interface</label>
          <div className="row" style={{gap:10,marginBottom:16}}>
            <ThemeCard active={!dark} onClick={()=>setDark(false)} label="Clair" icon="sun" bg="#F6F3EE" dot="#C05F2C"/>
            <ThemeCard active={dark} onClick={()=>setDark(true)} label="Sombre" icon="moon" bg="#191613" dot="#E08B57"/>
          </div>
          <div className="field"><label className="f">Taille du texte</label><select className="input"><option>Normal (recommandé)</option><option>Grand</option><option>Petit</option></select></div>
          <div className="field"><label className="f">Densité des listes</label><select className="input"><option>Confortable</option><option>Compacte</option></select></div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>Entreprise</h2>
          <div className="field"><label className="f">Devise</label><select className="input"><option>Euro (€)</option></select></div>
          <div className="field"><label className="f">Régime de TVA</label><select className="input"><option>Franchise — TVA non applicable</option><option>Assujetti (20 %)</option></select></div>
          <div className="field"><label className="f">Validité par défaut des devis</label><input className="input" defaultValue="30 jours"/></div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>Données & stockage</h2>
          <Info icon="lock" label="Emplacement" value="Dossier local BATORYA — cet ordinateur uniquement"/>
          <Info icon="folder" label="Sauvegarde" value="Sauvegarde manuelle conseillée chaque semaine"/>
          <div className="row" style={{marginTop:12}}>
            <button className="btn" onClick={()=>notify("Sauvegarde simulée : aucun fichier réel n'a été créé.")}><Icon d="download" size={14}/> Créer une sauvegarde</button>
          </div>
        </div>
        <div className="surface pad">
          <h2 style={{margin:"0 0 14px",fontSize:15,fontWeight:700}}>À propos</h2>
          <Info icon="info" label="Version" value="BATORYA Essentiel V6 — prototype de conception"/>
          <Info icon="lock" label="Licence" value="Démonstration locale"/>
          <Info icon="spark" label="Assistant Léon" value="Intégré, fonctionne localement"/>
        </div>
      </div>
    </>
  );
}
const ThemeCard = ({active,onClick,label,icon,bg,dot}) => (
  <button onClick={onClick} className="surface-flat" style={{flex:1,padding:10,background:bg,cursor:"pointer",outline:active?"2px solid var(--accent)":"none",outlineOffset:2,borderRadius:12}}>
    <div className="row" style={{justifyContent:"space-between",color:active?dot:"#888"}}>
      <Icon d={icon} size={16}/> {active && <Icon d="check" size={15}/>}
    </div>
    <div style={{fontSize:12.5,fontWeight:600,marginTop:8,color:bg==="#191613"?"#ECE6DC":"#2A2621"}}>{label}</div>
    <div style={{display:"flex",gap:4,marginTop:6}}>
      <span style={{width:14,height:14,borderRadius:99,background:bg==="#191613"?"#2A2520":"#FFFFFF"}}/>
      <span style={{width:14,height:14,borderRadius:99,background:dot}}/>
    </div>
  </button>
);

/* ============================================================ LÉON */
function Leon({ close, notify, go }) {
  const [msgs, setMsgs] = useState([
    { who:"bot", text:"Bonjour Rémy ! Je suis Léon, votre assistant intégré. Je fonctionne entièrement sur cet ordinateur : vos données ne quittent jamais BATORYA." },
  ]);
  const [val, setVal] = useState("");
  const reply = (q) => {
    let r = "Je peux vous aider à retrouver un document, préparer un devis ou suivre vos encaissements. Que souhaitez-vous faire ?";
    if (/devis/i.test(q)) { r = "Vous avez 3 devis en attente. Le devis DEV-2026-021 (SCI Bellevue, 4 820 €) mérite une relance. Je peux ouvrir le module Devis."; setTimeout(()=>go("commerce","devis"),900); }
    else if (/fact|pay|encaiss/i.test(q)) { r = "Restant dû : 1 830 €. La facture F-2026-029 (1 450 €) est en retard depuis le 17/09. Je peux ouvrir la facturation."; setTimeout(()=>go("factu","factures"),900); }
    else if (/chantier|travaux/i.test(q)) { r = "1 chantier en cours : chaudière Haddad (70 %). 1 chantier planifié la semaine prochaine. J'ouvre le suivi des chantiers."; setTimeout(()=>go("travaux","chantiers"),900); }
    else if (/client/i.test(q)) { r = "6 fiches : 4 clients et 2 prospects. Marie Bertrand attend un solde de 380 €."; }
    return r;
  };
  const send = (text) => {
    if (!text.trim()) return;
    setMsgs(m => [...m, { who:"me", text }, { who:"bot", text: reply(text) }]);
    setVal("");
  };
  return (
    <div className="leon-panel">
      <div className="row" style={{padding:"12px 14px",borderBottom:"1px solid var(--line)"}}>
        <span style={{width:30,height:30,borderRadius:99,background:"linear-gradient(135deg,var(--accent),#8F3F1B)",display:"flex",alignItems:"center",justifyContent:"center",color:"#fff"}}><Icon d="spark" size={15}/></span>
        <div style={{flex:1}}>
          <div style={{fontWeight:700,fontSize:13.5}}>Léon</div>
          <div className="muted" style={{fontSize:11}}>Assistant intégré · local</div>
        </div>
        <button className="btn-ghost btn btn-sm" onClick={close} style={{padding:6}}><Icon d="x" size={15}/></button>
      </div>
      <div style={{flex:1,overflow:"auto",padding:14,display:"flex",flexDirection:"column",gap:9}}>
        {msgs.map((m,i)=>(
          <div key={i} className={"leon-msg "+(m.who==="bot"?"bot":"me")}>{m.text}</div>
        ))}
      </div>
      <div style={{padding:"10px 12px",borderTop:"1px solid var(--line)"}}>
        <div className="row" style={{gap:6,marginBottom:8,overflowX:"auto"}}>
          {["Où en sont mes devis ?","Qui me doit de l'argent ?","Mes chantiers en cours"].map(s=>(
            <button key={s} className="chip" onClick={()=>send(s)} style={{border:"1px solid var(--line)"}}>{s}</button>
          ))}
        </div>
        <div className="row" style={{gap:8}}>
          <input className="input" style={{fontSize:13}} placeholder="Posez une question à Léon…" value={val} onChange={(e)=>setVal(e.target.value)} onKeyDown={(e)=>e.key==="Enter"&&send(val)}/>
          <button className="btn btn-primary btn-sm" style={{padding:"8px 11px"}} onClick={()=>send(val)}><Icon d="send" size={14}/></button>
        </div>
      </div>
    </div>
  );
}