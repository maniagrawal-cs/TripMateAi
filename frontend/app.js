const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let token = localStorage.getItem("ev_token"), user = null, trip = null, charts = [], timer = null, session = "";
const toast = m => { const t = $("#toast"); t.textContent = m; t.style.display = "block"; setTimeout(() => t.style.display = "none", 3500); };

// Leave EDUVOYAGE_API_BASE empty when frontend and FastAPI are served from
// the same origin (the recommended setup). For a separately hosted frontend,
// set window.EDUVOYAGE_API_BASE to the full backend origin before app.js loads.
const API_BASE = (window.EDUVOYAGE_API_BASE || "").replace(/\/$/, "");

async function api(path, opts = {}) {
  const h = token ? { Authorization: "Bearer " + token } : {};
  let body = opts.body;
  if (body && !(body instanceof FormData)) {
    h["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  let r;
  try {
    r = await fetch(API_BASE + "/api" + path, {
      method: opts.method || (body ? "POST" : "GET"),
      headers: h,
      body
    });
  } catch (err) {
    const target = API_BASE || window.location.origin;
    throw new Error(
      `Cannot connect to the EduVoyage backend at ${target}. ` +
      `Make sure FastAPI is running and open the website from that backend URL.`
    );
  }

  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    const msg = Array.isArray(e.detail)
      ? e.detail.map(x => x.msg).join("; ")
      : (e.detail || `Request failed (${r.status})`);
    throw new Error(msg);
  }
  if (opts.raw) return r;
  return r.json();
}
const safe = fn => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message); } };
const kill = () => { charts.forEach(c => c.destroy()); charts = []; clearInterval(timer); };
const chart = (id, type, labels, data, label) => charts.push(new Chart($("#" + id), { type, data: { labels, datasets: [{ label, data, backgroundColor: ["#173F35", "#F4B860", "#E87955", "#8fb8a0", "#c9a66b"] , borderColor: "#173F35" }] }, options: { responsive: true } }));

// ---------- auth ----------
function landing(mode = "login") {
  $("#app").innerHTML = `<div class="hero"><div class="box"><h1>🧭 EduVoyage</h1><p>Turn every field trip into a learning adventure.</p>
  <div id="f">${mode === "login" ? `<input id="em" placeholder="Email"><input id="pw" type="password" placeholder="Password">
   <button id="go" style="width:100%">Log in</button><p>New here? <a href="#" id="sw">Create an account</a></p>
   <p style="font-size:.8rem">Demo: teacher@demo.com / aarav@demo.com (password demo12345)</p>` :
  `<input id="nm" placeholder="Your name"><input id="em" placeholder="Email"><input id="pw" type="password" placeholder="Password (8+ chars)">
   <select id="ro"><option value="student">I'm a student</option><option value="teacher">I'm a teacher</option></select>
   <input id="ag" type="number" placeholder="Age" value="13"><input id="cl" placeholder="Class (e.g. 8A)">
   <button id="go" style="width:100%">Register</button><p>Have an account? <a href="#" id="sw">Log in</a></p>`}</div></div></div>`;
  $("#sw").onclick = e => { e.preventDefault(); landing(mode === "login" ? "register" : "login"); };
  $("#go").onclick = safe(async () => {
    const d = mode === "login" ? { email: $("#em").value, password: $("#pw").value } :
      { name: $("#nm").value, email: $("#em").value, password: $("#pw").value, role: $("#ro").value, age: +$("#ag").value, class_name: $("#cl").value };
    const r = await api(mode === "login" ? "/auth/login" : "/auth/register", { body: d });
    token = r.token; localStorage.setItem("ev_token", token); user = r.user; shell();
  });
}
const logout = () => { localStorage.removeItem("ev_token"); token = null; landing(); };

// ---------- shell ----------
const NAV = {
  student: [["home", "🏠 Home"], ["trips", "🎒 My Trips"], ["explore", "🗺️ Explore Destination"], ["companion", "🤖 AI Companion"], ["hunt", "📸 Treasure Hunt"], ["quiz", "🎯 Quiz Arena"], ["groups", "👥 My Groups"], ["ach", "🏅 Achievements"], ["progress", "📈 Progress"], ["profile", "👤 Profile"]],
  teacher: [["home", "📊 Overview"], ["create", "➕ Create Trip"], ["manage", "🧳 Manage Trips"], ["explore", "🗺️ Destinations"], ["people", "👥 Students & Groups"], ["gen", "✨ Generate Activities"], ["review", "🔍 Review AI Photos"], ["analytics", "📈 Analytics & Reports"], ["profile", "👤 Profile"]]
};
async function shell() {
  if (!user) user = await api("/auth/me");
  document.body.className = user.role;
  const trips = await api("/trips"); trip = trips.find(t => t.id === (trip && trip.id)) || trips[0] || null;
  $("#app").innerHTML = `<div class="layout"><nav class="side"><h2>🧭 EduVoyage</h2>${NAV[user.role].map(([k, l]) => `<a data-k="${k}">${l}</a>`).join("")}<a id="lo">🚪 Log out</a></nav>
  <div class="main"><div class="top"><div><b>${esc(trip ? trip.name : "No trip yet")}</b>
  ${trips.length > 1 ? `<select id="tsel" style="width:auto">${trips.map(t => `<option value="${t.id}" ${trip && t.id === trip.id ? "selected" : ""}>${esc(t.name)}</option>`).join("")}</select>` : ""}</div>
  <div>🔔 <span id="notif"></span> ${esc(user.name)} <span class="badge">${user.role}</span></div></div><div class="content" id="view"></div></div></div>`;
  document.querySelectorAll(".side a[data-k]").forEach(a => a.onclick = () => go(a.dataset.k));
  $("#lo").onclick = logout;
  if ($("#tsel")) $("#tsel").onchange = e => { trip = trips.find(t => t.id == e.target.value); go(window.cur || "home"); };
  go("home");
}
function go(k) {
  kill(); window.cur = k;
  document.querySelectorAll(".side a").forEach(a => a.classList.toggle("on", a.dataset.k === k));
  const fn = VIEWS[user.role][k] || VIEWS.both[k];
  if (!trip && !["create", "trips", "profile"].includes(k) && user.role === "student" || (!trip && user.role === "teacher" && !["create", "profile", "home"].includes(k)))
    return $("#view").innerHTML = `<div class="card"><h2>No trip selected</h2><p>${user.role === "student" ? "Join a trip with an invitation code in My Trips." : "Create your first trip."}</p></div>`;
  safe(fn)();
}
const V = html => $("#view").innerHTML = html;
const bar = p => `<div class="bar"><i style="width:${p}%"></i></div>`;

// ---------- shared views ----------
const both = {
  async explore() {
    const d = await api(`/trips/${trip.id}/destination`);
    V(`<h1>${esc(d.name)}</h1><div class="grid"><div class="card"><div id="map"></div></div>
    <div class="card"><h3>Timeline</h3>${d.timeline.map(t => `<p><b>${t[0]}</b> ${esc(t[1])}</p>`).join("")}<h3>Related subjects</h3>${d.subjects.map(s => `<span class="badge">${esc(s)}</span>`).join("")}
    <h3>Did you know?</h3>${d.facts.map(f => `<p>✨ ${esc(f)}</p>`).join("")}</div></div>
    ${Object.entries(d.sections).map(([k, v]) => `<div class="card"><h3>${esc(k[0].toUpperCase() + k.slice(1))}</h3><p>${esc(v)}</p></div>`).join("")}
    <div class="card"><h3>Sources</h3>${d.sources.map(s => `<p><a href="${esc(s[1])}" target="_blank" rel="noopener">${esc(s[0])}</a></p>`).join("")}</div>
    ${user.role === "teacher" ? `<div class="card"><h3>Choose what students see</h3>${d.all_sections.map(s => `<label><input type="checkbox" class="sec" value="${s}" ${(trip.shared_topics || []).includes(s) ? "checked" : ""} style="width:auto"> ${s}</label> `).join("")}
    <br><button id="sv">Save selection</button></div>` : ""}
    <div class="card"><h3>Ask AI about this place</h3><button id="ask">Open AI Companion</button></div>`);
    const m = L.map("map").setView([d.lat, d.lng], 16); L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(m); L.marker([d.lat, d.lng]).addTo(m).bindPopup(esc(d.name));
    $("#ask").onclick = () => go("companion");
    if ($("#sv")) $("#sv").onclick = safe(async () => { const t = [...document.querySelectorAll(".sec:checked")].map(c => c.value); await api(`/trips/${trip.id}`, { method: "PUT", body: { ...trip, shared_topics: t } }); trip.shared_topics = t; toast("Saved"); });
  },
  async profile() { V(`<div class="card"><h2>${esc(user.name)}</h2><p>${esc(user.email)} · ${user.role}</p><p>Class: ${esc(user.class_name || "-")}</p><button id="lo2">Log out</button></div>`); $("#lo2").onclick = logout; },
  async companion() {
    V(`<h1>🤖 AI Learning Companion</h1><div class="card"><div class="chat" id="chat"><div class="msg a">Hi ${esc(user.name)}! Ask me anything about the monument 🌍 (any language works).</div></div>
    <div style="display:flex;gap:6px;margin-top:8px"><input id="q" placeholder="Why is the Taj Mahal white?" style="margin:0"><button id="send">Send</button></div></div>`);
    const add = (c, t) => { $("#chat").insertAdjacentHTML("beforeend", `<div class="msg ${c}">${esc(t)}</div>`); $("#chat").scrollTop = 1e9; };
    const send = safe(async () => {
      const m = $("#q").value.trim(); if (!m) return; $("#q").value = ""; add("u", m); $("#send").innerHTML = '<span class="spin"></span>';
      try { const r = await api("/ai/chat", { body: { message: m, trip_id: trip.id, session_id: session } }); session = r.session_id; add("a", r.reply + (r.sources.length ? `\n\n📚 Sources: ${r.sources.join(", ")}` : "")); }
      finally { $("#send").textContent = "Send"; }
    });
    $("#send").onclick = send; $("#q").onkeydown = e => e.key === "Enter" && send();
  },
};

// ---------- student ----------
const student = {
  async home() {
    const [a, lb, ms] = await Promise.all([api("/analytics/student"), api(`/leaderboard?trip_id=${trip.id}`), api(`/missions?trip_id=${trip.id}`)]);
    const done = ms.filter(m => m.status === "completed").length, pct = ms.length ? Math.round(100 * done / ms.length) : 0;
    const days = Math.ceil((new Date(trip.trip_date) - new Date()) / 864e5);
    V(`<h1>Welcome, ${esc(user.name)} 👋</h1><div class="grid">
    <div class="card"><h3>⭐ ${a.xp} XP</h3><p>${done}/${ms.length} missions completed</p>${bar(pct)}</div>
    <div class="card"><h3>Active trip</h3><p><b>${esc(trip.name)}</b></p><p>${days > 0 ? `⏳ ${days} days to go` : "Trip day is here or past!"}</p></div>
    <div class="card"><h3>Badges</h3>${a.badges.map(b => `<span class="badge gold">🏅 ${esc(b)}</span>`).join("") || "Complete missions to earn badges!"}</div></div>
    <div class="card"><h3>🏆 Leaderboard</h3><table>${lb.students.map((s, i) => `<tr><td>${i + 1}</td><td>${esc(s.name)}</td><td>${s.xp} XP</td></tr>`).join("")}</table></div>
    <div class="card"><h3>🎲 Daily challenge</h3><p>Find something with mirror symmetry and tell the AI Companion why it matters in maths!</p><button id="dc" class="alt">Ask the companion</button></div>`);
    $("#dc").onclick = () => go("companion"); $("#notif").textContent = ms.filter(m => m.status === "active").length + " active missions";
  },
  async trips() {
    const ts = await api("/trips");
    V(`<h1>🎒 My Trips</h1><div class="grid">${ts.map(t => `<div class="card"><h3>${esc(t.name)}</h3><p>${esc(t.trip_date)} · ${esc(t.duration)}</p><p>${esc(t.objectives)}</p><button data-t="${t.id}">Open trip</button></div>`).join("")}</div>
    <div class="card"><h3>Join with invitation code</h3><input id="code" placeholder="e.g. TAJ123"><button id="jn" class="alt">Join trip</button></div>`);
    document.querySelectorAll("[data-t]").forEach(b => b.onclick = () => { trip = ts.find(t => t.id == b.dataset.t); go("home"); });
    $("#jn").onclick = safe(async () => { const r = await api("/trips/join", { body: { code: $("#code").value } }); toast("Joined " + r.name); trip = { id: r.trip_id }; shell(); });
  },
  async hunt() {
    const ms = await api(`/missions?trip_id=${trip.id}`);
    V(`<h1>📸 Treasure Hunt</h1><div class="grid">${ms.map(m => `<div class="card"><span class="tag ${m.status === "completed" ? "ok" : m.status === "locked" ? "warn" : ""}">${m.status}</span> <span class="tag">${m.game}</span> <span class="tag">${m.difficulty}</span>
    <h3>${esc(m.title)} (+${m.points} XP)</h3><p>${esc(m.task)}</p>${m.hint ? `<details><summary>💡 Hint</summary>${esc(m.hint)}</details>` : ""}
    ${m.last ? `<p>Last result: <span class="tag ${m.last.status === "verified" || m.last.status === "approved" ? "ok" : m.last.status === "try_again" ? "bad" : "warn"}">${m.last.status.replace("_", " ")}</span><br>${esc(m.last.result.explanation || "")}</p>` : ""}
    ${m.status === "active" ? `<input type="file" accept="image/jpeg,image/png" capture="environment" id="f${m.id}"><button data-m="${m.id}" class="alt">Upload photo</button>` : ""}</div>`).join("")}</div>
    <div id="lbt"></div>`);
    document.querySelectorAll("[data-m]").forEach(b => b.onclick = safe(async () => {
      const f = $("#f" + b.dataset.m).files[0]; if (!f) return toast("Choose or take a photo first");
      const fd = new FormData(); fd.append("file", f); b.innerHTML = '<span class="spin"></span> AI is checking…'; b.disabled = true;
      try {
        const r = await api(`/missions/${b.dataset.m}/upload`, { body: fd });
        const msg = { verified: `✅ Verified! +${r.points_awarded} XP`, try_again: "🔁 Try again", needs_review: "🕐 Sent to your teacher for review" }[r.status];
        alert(`${msg}\n\n${r.explanation || ""}\n${r.learning_fact ? "\n💡 " + r.learning_fact : ""}${r.status === "try_again" ? "\n\nHint: " + (r.hint || "") : ""}`);
      } finally { go("hunt"); }
    }));
    const lb = await api(`/leaderboard?trip_id=${trip.id}`);
    $("#lbt").innerHTML = `<div class="card"><h3>👥 Team leaderboard</h3><table>${lb.teams.map((t, i) => `<tr><td>${i + 1}</td><td>${esc(t.name)}</td><td>${t.xp} XP</td></tr>`).join("") || "<tr><td>No teams yet</td></tr>"}</table></div>`;
  },
  async quiz() {
    const qs = await api(`/quizzes?trip_id=${trip.id}`);
    V(`<h1>🎯 Quiz Arena</h1><div class="grid">${qs.map(q => `<div class="card"><h3>${esc(q.title)}</h3><p>${q.questions} questions · ${q.minutes} min · ${q.kind}</p>
    <button data-q="${q.id}" class="${q.done ? "ghost" : "alt"}">${q.done ? "View results" : "Start quiz"}</button></div>`).join("") || "<p>No quizzes yet.</p>"}</div>`);
    document.querySelectorAll("[data-q]").forEach(b => b.onclick = safe(async () => { const q = qs.find(x => x.id == b.dataset.q); q.done ? showResult(await api(`/quizzes/${q.id}/results`)) : runQuiz(q.id); }));
  },
  async groups() {
    const gs = await api(`/groups?trip_id=${trip.id}`);
    V(`<h1>👥 My Groups</h1>${gs.map(g => `<div class="card"><h3>${esc(g.name)}</h3>${g.members.map(m => `<span class="badge">${esc(m.name)}${m.id === g.leader_id ? " ⭐ leader" : ""}</span>`).join("")}</div>`).join("") || "<p>Your teacher hasn't added you to a group yet.</p>"}`);
  },
  async ach() {
    const a = await api("/analytics/student"); const all = ["History Explorer", "Architecture Detective", "Curious Mind", "Treasure Hunter", "Quiz Champion", "Team Player"];
    V(`<h1>🏅 Achievements</h1><div class="grid">${all.map(b => `<div class="card" style="opacity:${a.badges.includes(b) ? 1 : .4}"><h3>🏅 ${b}</h3><p>${a.badges.includes(b) ? "Earned!" : "Locked"}</p></div>`).join("")}</div>`);
  },
  async progress() {
    const a = await api("/analytics/student");
    V(`<h1>📈 Learning Progress</h1><div class="card"><p>XP: <b>${a.xp}</b> · Questions asked: <b>${a.questions_asked}</b> · Missions: <b>${a.missions_done}</b></p><canvas id="c1"></canvas></div>`);
    chart("c1", "bar", a.quizzes.map(q => q.quiz), a.quizzes.map(q => q.percent), "Quiz %");
  },
};
function runQuiz(id) {
  safe(async () => {
    const q = await api(`/quizzes/${id}`); let i = 0, ans = {}, left = q.minutes * 60, start = Date.now();
    const submit = safe(async () => { clearInterval(timer); showResult(await api(`/quizzes/${id}/submit`, { body: { answers: ans, seconds: Math.round((Date.now() - start) / 1000) } })); });
    const draw = () => {
      const x = q.questions[i];
      V(`<h1>${esc(q.title)}</h1><div class="card"><div style="display:flex;justify-content:space-between"><span>Question ${i + 1}/${q.questions.length}</span><b id="tm"></b></div>${bar(100 * (i + 1) / q.questions.length)}
      <h3>${esc(x.text)}</h3>${x.type === "short" ? `<input id="sa" value="${esc(ans[x.id] || "")}" placeholder="Your answer">` : x.options.map(o => `<button class="opt ${ans[x.id] === o ? "sel" : ""}" data-o="${esc(o)}">${esc(o)}</button>`).join("")}
      <div style="margin-top:1rem"><button id="pv" class="ghost" ${i ? "" : "disabled"}>◀ Previous</button> <button id="nx" ${i < q.questions.length - 1 ? "" : "disabled"}>Next ▶</button> <button id="sb" class="alt">Submit quiz</button></div>
      <div class="qnav">${q.questions.map((y, n) => `<button data-n="${n}" class="${ans[y.id] ? "ans" : ""}">${n + 1}</button>`).join("")}</div></div>`);
      document.querySelectorAll("[data-o]").forEach(b => b.onclick = () => { ans[x.id] = b.dataset.o; draw(); });
      if ($("#sa")) $("#sa").oninput = e => ans[x.id] = e.target.value;
      $("#pv").onclick = () => { i--; draw(); }; $("#nx").onclick = () => { i++; draw(); };
      document.querySelectorAll("[data-n]").forEach(b => b.onclick = () => { i = +b.dataset.n; draw(); });
      $("#sb").onclick = () => { const un = q.questions.length - Object.values(ans).filter(Boolean).length; if (confirm(`Submit now? ${un} question(s) unanswered. You cannot change answers afterwards.`)) submit(); };
      tick();
    };
    const tick = () => { const t = $("#tm"); if (t) t.textContent = `⏱ ${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`; };
    timer = setInterval(() => { left--; tick(); if (left <= 0) { clearInterval(timer); toast("Time is up!"); submit(); } }, 1000);
    draw();
  })();
}
function showResult(r) {
  V(`<h1>Results</h1><div class="card"><h2>${r.score}/${r.total} · ${r.percent}%</h2><p>Time taken: ${Math.floor(r.seconds / 60)}m ${r.seconds % 60}s · Correct ${r.score} · Incorrect ${r.total - r.score}</p>
  ${r.revise.length ? `<p>📚 Revise: ${r.revise.map(t => `<span class="badge">${esc(t)}</span>`).join("")}</p>` : "<p>🎉 Perfect!</p>"}</div>
  ${r.detail.map(d => `<div class="card"><span class="tag ${d.correct ? "ok" : "bad"}">${d.correct ? "Correct" : "Incorrect"}</span><h4>${esc(d.text)}</h4><p>Your answer: ${esc(d.given || "-")} · Right answer: <b>${esc(d.answer)}</b></p><p>${esc(d.explanation)}</p></div>`).join("")}`);
}

// ---------- teacher ----------
const teacher = {
  async home() {
    if (!trip) return V(`<div class="card"><h2>Welcome!</h2><p>Create your first trip to get started.</p><button id="ct">Create trip</button></div>`), $("#ct").onclick = () => go("create");
    const a = await api(`/analytics/trip/${trip.id}`), lb = await api(`/leaderboard?trip_id=${trip.id}`);
    V(`<h1>${esc(trip.name)}</h1><div class="grid"><div class="card"><h3>Invitation code</h3><h2>${trip.code}</h2><p>${trip.published ? "Published" : "Draft"}</p></div>
    <div class="card"><h3>Students</h3><h2>${a.students.length}</h2></div><div class="card"><h3>Missions</h3><h2>${a.mission_total}</h2></div></div>
    <div class="grid"><div class="card"><h3>Participation (AI questions)</h3><canvas id="c1"></canvas></div><div class="card"><h3>Mission completion</h3><canvas id="c2"></canvas></div>
    <div class="card"><h3>Group performance</h3><canvas id="c3"></canvas></div><div class="card"><h3>Quiz averages</h3><canvas id="c4"></canvas></div></div>`);
    const n = a.students.map(s => s.name);
    chart("c1", "bar", n, a.students.map(s => s.questions), "Questions"); chart("c2", "bar", n, a.students.map(s => s.missions), "Missions");
    chart("c3", "doughnut", lb.teams.map(t => t.name), lb.teams.map(t => t.xp), "XP"); chart("c4", "bar", n, a.students.map(s => s.quiz_avg || 0), "Quiz %");
  },
  async create(t = null) {
    V(`<h1>${t ? "Edit" : "Create"} trip</h1><div class="card"><input id="n" placeholder="Trip name" value="${esc(t?.name)}"><input id="dt" type="date" value="${esc(t?.trip_date)}"><input id="du" placeholder="Duration" value="${esc(t?.duration)}">
    <input id="cl" placeholder="Class" value="${esc(t?.class_name)}"><input id="ag" placeholder="Age group (e.g. 12-14)" value="${esc(t?.age_group)}"><input id="su" placeholder="Subjects" value="${esc(t?.subjects)}">
    <textarea id="ob" placeholder="Learning objectives">${esc(t?.objectives)}</textarea><p>Destination: Taj Mahal (demo)</p><button id="sv" class="alt">${t ? "Save changes" : "Create trip"}</button></div>`);
    $("#sv").onclick = safe(async () => {
      const body = { name: $("#n").value, trip_date: $("#dt").value, duration: $("#du").value, class_name: $("#cl").value, age_group: $("#ag").value, subjects: $("#su").value, objectives: $("#ob").value, shared_topics: t?.shared_topics || [] };
      const r = await api(t ? `/trips/${t.id}` : "/trips", { method: t ? "PUT" : "POST", body }); trip = r; toast("Saved"); shell();
    });
  },
  async manage() {
    const ts = await api("/trips");
    V(`<h1>Manage trips</h1>${ts.map(t => `<div class="card"><h3>${esc(t.name)} <span class="tag">${t.published ? "published" : "draft"}</span></h3><p>Code: <b>${t.code}</b> · ${t.students} students</p>
    <button data-e="${t.id}" class="ghost">Edit</button> ${t.published ? "" : `<button data-p="${t.id}" class="alt">Publish</button> <button data-d="${t.id}" class="ghost">Delete</button>`}</div>`).join("")}`);
    const on = (a, f) => document.querySelectorAll(`[data-${a}]`).forEach(b => b.onclick = safe(() => f(+b.dataset[a])));
    on("e", id => teacher.create(ts.find(t => t.id === id))); on("p", async id => { await api(`/trips/${id}/publish`, { method: "POST" }); shell(); });
    on("d", async id => { if (confirm("Delete this draft trip?")) { await api(`/trips/${id}`, { method: "DELETE" }); trip = null; shell(); } });
  },
  async people() {
    const [st, gs] = await Promise.all([api(`/trips/${trip.id}/students`), api(`/groups?trip_id=${trip.id}`)]);
    V(`<h1>Students & groups</h1><div class="grid"><div class="card"><h3>Students</h3>${st.map(s => `<p>${esc(s.name)} (${esc(s.email)}) <button data-r="${s.id}" class="ghost">Remove</button></p>`).join("")}
    <input id="se" placeholder="Student email"><button id="as">Add student</button></div>
    <div class="card"><h3>Create group</h3><input id="gn" placeholder="Group name"><select id="gl"><option value="">Leader (optional)</option>${st.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join("")}</select><button id="cg" class="alt">Create group</button></div></div>
    ${gs.map(g => `<div class="card"><h3>${esc(g.name)}</h3>${g.members.map(m => `<span class="badge">${esc(m.name)}</span>`).join("")}<br>
    <select id="m${g.id}">${st.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join("")}</select><button data-g="${g.id}">Add to group</button></div>`).join("")}`);
    $("#as").onclick = safe(async () => { await api(`/trips/${trip.id}/students`, { body: { email: $("#se").value } }); teacher.people(); });
    $("#cg").onclick = safe(async () => { await api("/groups", { body: { trip_id: trip.id, name: $("#gn").value, leader_id: $("#gl").value ? +$("#gl").value : null } }); teacher.people(); });
    document.querySelectorAll("[data-r]").forEach(b => b.onclick = safe(async () => { await api(`/trips/${trip.id}/students/${b.dataset.r}`, { method: "DELETE" }); teacher.people(); }));
    document.querySelectorAll("[data-g]").forEach(b => b.onclick = safe(async () => { await api(`/groups/${b.dataset.g}/members`, { body: { user_id: +$("#m" + b.dataset.g).value } }); teacher.people(); }));
  },
  async gen() {
    const gs = await api(`/groups?trip_id=${trip.id}`), go_ = `<option value="">Whole class</option>` + gs.map(g => `<option value="${g.id}">${esc(g.name)}</option>`).join("");
    V(`<h1>Generate activities</h1><div class="grid"><div class="card"><h3>Quiz (min 10 questions)</h3><input id="qs" value="History"><select id="qd"><option>easy</option><option selected>medium</option><option>hard</option></select>
    <input id="qn" type="number" min="10" value="10"><select id="qk"><option value="practice">Practice</option><option value="pre">Pre-trip</option><option value="post">Post-trip</option></select><select id="qg">${go_}</select><button id="gq" class="alt">Generate quiz</button></div>
    <div class="card"><h3>Treasure hunt missions</h3><input id="hn" type="number" min="1" max="8" value="3"><select id="hg">${go_}</select><button id="gh" class="alt">Generate missions</button></div></div>`);
    const run = (id, path, body) => $(id).onclick = safe(async () => { const b = $(id); b.innerHTML = '<span class="spin"></span>'; try { await api(path, { body: body() }); toast("Created!"); } finally { b.textContent = "Done – generate more"; } });
    run("#gq", "/ai/generate-quiz", () => ({ trip_id: trip.id, subject: $("#qs").value, difficulty: $("#qd").value, count: +$("#qn").value, kind: $("#qk").value, group_id: $("#qg").value ? +$("#qg").value : null }));
    run("#gh", "/ai/generate-treasure-hunt", () => ({ trip_id: trip.id, count: +$("#hn").value, group_id: $("#hg").value ? +$("#hg").value : null }));
  },
  async review() {
    const p = await api(`/missions/review/pending?trip_id=${trip.id}`);
    V(`<h1>Review AI photos</h1>${p.map(s => `<div class="card"><h3>${esc(s.student)} · ${esc(s.mission)}</h3><img data-i="${s.id}" style="max-width:300px;border-radius:12px"><p>AI note: ${esc(s.result.explanation || "")}</p>
    <button data-a="${s.id}" class="alt">Approve</button> <button data-x="${s.id}" class="ghost">Reject</button></div>`).join("") || "<p>Nothing waiting 🎉</p>"}`);
    for (const img of document.querySelectorAll("[data-i]")) { const r = await api(`/missions/submissions/${img.dataset.i}/image`, { raw: true }); img.src = URL.createObjectURL(await r.blob()); }
    const rv = (a, ok) => document.querySelectorAll(`[data-${a}]`).forEach(b => b.onclick = safe(async () => { await api(`/missions/submissions/${b.dataset[a]}/review`, { body: { approve: ok } }); teacher.review(); }));
    rv("a", true); rv("x", false);
  },
  async analytics() {
    const a = await api(`/analytics/trip/${trip.id}`);
    V(`<h1>Analytics & reports</h1><div class="card"><canvas id="c1"></canvas></div><div class="card"><table><tr><th>Student</th><th>XP</th><th>Missions</th><th>Pre %</th><th>Post %</th><th>AI questions</th></tr>
    ${a.students.map(s => `<tr><td>${esc(s.name)}</td><td>${s.xp}</td><td>${s.missions}/${a.mission_total}</td><td>${s.pre ?? "-"}</td><td>${s.post ?? "-"}</td><td>${s.questions}</td></tr>`).join("")}</table><br><button id="dl" class="alt">⬇ Download CSV report</button></div>`);
    const n = a.students.map(s => s.name);
    charts.push(new Chart($("#c1"), { type: "bar", data: { labels: n, datasets: [{ label: "Pre-trip %", data: a.students.map(s => s.pre || 0), backgroundColor: "#F4B860" }, { label: "Post-trip %", data: a.students.map(s => s.post || 0), backgroundColor: "#173F35" }] } }));
    $("#dl").onclick = safe(async () => { const r = await api(`/analytics/trip/${trip.id}/report.csv`, { raw: true }); const u = URL.createObjectURL(await r.blob()); Object.assign(document.createElement("a"), { href: u, download: "report.csv" }).click(); });
  },
};
const VIEWS = { both, student, teacher };
VIEWS.student = { ...both, ...student }; VIEWS.teacher = { ...both, ...teacher };
(async () => { if (token) { try { user = await api("/auth/me"); return shell(); } catch { } } landing(); })();
