/* =========================================================
   Portfolio Manager — logic giao diện
   ========================================================= */

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (html !== undefined) node.innerHTML = html;
  return node;
};

let PROJECTS = [];
let PLACEHOLDER = "assets/images/client.jpg";
let current = null; // project đang mở trong màn sửa

/* ---------------------------------------------------------
   Gọi API
--------------------------------------------------------- */

async function api(path, options = {}) {
  const res = await fetch(path, options);
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Máy chủ trả về lỗi ${res.status}`);
  }
  if (!res.ok || data.ok === false) throw new Error(data.error || `Lỗi ${res.status}`);
  return data;
}

const post = (path, body) =>
  api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });

/* ---------------------------------------------------------
   Thông báo / loading
--------------------------------------------------------- */

function toast(message, kind = "") {
  const node = el("div", `toast ${kind}`, message);
  $("#toasts").appendChild(node);
  setTimeout(() => {
    node.style.transition = "opacity .3s";
    node.style.opacity = "0";
    setTimeout(() => node.remove(), 300);
  }, 3600);
}

function busy(text) {
  $("#busy-text").textContent = text || "Đang xử lý…";
  $("#busy").classList.remove("hidden");
}

const idle = () => $("#busy").classList.add("hidden");

async function guard(text, fn) {
  busy(text);
  try {
    return await fn();
  } catch (err) {
    toast(err.message, "err");
    throw err;
  } finally {
    idle();
  }
}

/* ---------------------------------------------------------
   Modal
--------------------------------------------------------- */

function modal({ title, body, actions }) {
  $("#modal-title").textContent = title;
  $("#modal-body").innerHTML = "";
  $("#modal-body").append(...(Array.isArray(body) ? body : [body]));
  $("#modal-actions").innerHTML = "";
  actions.forEach(({ label, kind, onClick, id }) => {
    const button = el("button", `btn ${kind || "ghost"}`, label);
    if (id) button.id = id;
    button.onclick = onClick;
    $("#modal-actions").appendChild(button);
  });
  $("#modal").classList.remove("hidden");
}

const closeModal = () => $("#modal").classList.add("hidden");

$("#modal").addEventListener("click", (e) => {
  if (e.target.id === "modal") closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

function confirmBox(title, message, confirmLabel, onConfirm) {
  modal({
    title,
    body: el("p", "hint", message),
    actions: [
      { label: "Hủy", onClick: closeModal },
      {
        label: confirmLabel,
        kind: "danger",
        onClick: () => {
          closeModal();
          onConfirm();
        },
      },
    ],
  });
}

/* ---------------------------------------------------------
   Tải dữ liệu + dựng lại file cho web
--------------------------------------------------------- */

async function load() {
  const data = await api("/api/projects");
  PROJECTS = data.projects;
  PLACEHOLDER = data.placeholder;
  $("#repo-path").textContent = data.repo;
  renderList();
  refreshPublishBadge();
  if (current) {
    const fresh = PROJECTS.find((p) => p.id === current.id);
    if (fresh) openProject(fresh.id);
    else showList();
  }
}

/** Nhắc trên nút khi có thay đổi đã lưu ở máy nhưng chưa lên GitHub. */
async function refreshPublishBadge() {
  const button = $("#btn-publish");
  try {
    const status = await api("/api/git/status");
    const waiting = status.ahead || 0;
    button.textContent = waiting ? `Đăng lên web · ${waiting} chờ` : "Đăng lên web";
    button.classList.toggle("pending", waiting > 0);
    button.title = waiting
      ? `${waiting} lần lưu đang chờ đẩy lên GitHub`
      : "Lưu và đẩy thay đổi lên GitHub";
  } catch {
    /* không lấy được trạng thái git thì cứ để nút như cũ */
  }
}

let buildTimer = null;
function scheduleBuild() {
  clearTimeout(buildTimer);
  buildTimer = setTimeout(() => post("/api/build").catch(() => {}), 400);
}

const thumb = (url, w = 420) => `/api/thumb?path=${encodeURIComponent(url)}&w=${w}`;

/* ---------------------------------------------------------
   MÀN 1 — danh sách project
--------------------------------------------------------- */

function showList() {
  current = null;
  $("#view-edit").classList.add("hidden");
  $("#view-list").classList.remove("hidden");
  window.scrollTo(0, 0);
}

function renderList() {
  const grid = $("#project-grid");
  grid.innerHTML = "";

  PROJECTS.forEach((p) => {
    const card = el("article", `project-card${p.wide ? " project-wide" : ""}`);
    card.dataset.id = p.id;
    card.draggable = true;

    const hasCover = p.cover_url !== PLACEHOLDER;
    const frame = el("div", `project-image${hasCover ? "" : " empty"}`);
    if (hasCover) {
      const img = el("img");
      img.src = thumb(p.cover_url, 560);
      img.alt = p.title;
      img.loading = "lazy";
      frame.appendChild(img);
    }

    if (p.new_count > 0) {
      frame.appendChild(el("div", "badge", `+${p.new_count} ảnh mới`));
    }
    frame.appendChild(el("div", "drag-handle", "⠿"));

    const overlay = el("div", "card-overlay");
    const edit = el("button", "btn primary small", "Sửa");
    edit.onclick = (e) => {
      e.stopPropagation();
      openProject(p.id);
    };
    const openFolder = el("button", "btn ghost small", "Thư mục");
    openFolder.onclick = (e) => {
      e.stopPropagation();
      post("/api/open-folder", { id: p.id }).catch((err) => toast(err.message, "err"));
    };
    overlay.append(edit, openFolder);
    frame.appendChild(overlay);
    frame.onclick = () => openProject(p.id);

    const info = el("div", "project-info");
    info.appendChild(el("p", "project-category", escapeHtml(p.category || "—")));
    info.appendChild(el("h2", null, escapeHtml(p.title)));
    info.appendChild(
      el("p", "sub", `${p.images.length} ảnh · 📁 ${escapeHtml(p.folder)}`)
    );

    card.append(frame, info);
    grid.appendChild(card);
  });

  applyGridTokens();
  enableCardDrag(grid);
}

/**
 * Lưới trong app phải hiện y như web thật — nên lấy thẳng tỉ lệ, bo góc và
 * khoảng cách từ cấu hình giao diện, thay vì để số cứng trong css của app.
 */
function applyGridTokens() {
  const grid = $("#project-grid");
  if (!grid || typeof THEME === "undefined" || !THEME) return;
  const l = THEME.layout;
  grid.style.setProperty("--card-ratio", l.card_ratio);
  grid.style.setProperty("--card-ratio-wide", l.card_ratio_wide);
  grid.style.setProperty("--card-radius", l.card_radius + "px");
  grid.style.setProperty("--grid-col-gap", l.grid_col_gap + "px");
  grid.style.setProperty("--grid-row-gap", l.grid_row_gap + "px");
}

function escapeHtml(text) {
  return String(text ?? "").replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]
  );
}

/* ---- kéo thả đổi thứ tự project ---- */

function enableCardDrag(grid) {
  let dragged = null;

  grid.querySelectorAll(".project-card").forEach((card) => {
    card.addEventListener("dragstart", (e) => {
      dragged = card;
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", card.dataset.id);
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      grid.querySelectorAll(".drop-target").forEach((n) => n.classList.remove("drop-target"));
      dragged = null;
    });

    card.addEventListener("dragover", (e) => {
      if (!dragged || dragged === card) return;
      e.preventDefault();
      card.classList.add("drop-target");
    });

    card.addEventListener("dragleave", () => card.classList.remove("drop-target"));

    card.addEventListener("drop", async (e) => {
      e.preventDefault();
      card.classList.remove("drop-target");
      if (!dragged || dragged === card) return;

      const cards = [...grid.querySelectorAll(".project-card")];
      const from = cards.indexOf(dragged);
      const to = cards.indexOf(card);
      grid.insertBefore(dragged, from < to ? card.nextSibling : card);

      const ids = [...grid.querySelectorAll(".project-card")].map((c) => c.dataset.id);
      await guard("Đang lưu thứ tự…", async () => {
        await post("/api/projects/reorder", { ids });
        scheduleBuild();
        await load();
      });
      toast("Đã đổi thứ tự", "ok");
    });
  });
}

/* ---------------------------------------------------------
   MÀN 2 — sửa một project
--------------------------------------------------------- */

function openProject(id) {
  const project = PROJECTS.find((p) => p.id === id);
  if (!project) return;
  current = project;

  $("#view-list").classList.add("hidden");
  $("#view-edit").classList.remove("hidden");

  $("#edit-title-display").textContent = project.title;
  $("#f-title").value = project.title;
  $("#f-category").value = project.category;
  $("#f-description").value = project.description;
  $("#f-wide").checked = !!project.wide;
  $("#f-folder").textContent = `assets/project/${project.folder}/`;
  $("#f-id").textContent = `project-detail.html?project=${project.id}`;

  renderImages();
  window.scrollTo(0, 0);
}

function renderImages() {
  const grid = $("#image-grid");
  grid.innerHTML = "";

  const visible = current.items.filter((i) => !i.hidden);
  const hidden = current.items.filter((i) => i.hidden);
  $("#img-count").textContent =
    `(${visible.length} hiện${hidden.length ? ` · ${hidden.length} ẩn` : ""})`;

  current.items.forEach((item) => {
    const tile = el("div", `tile${item.hidden ? " is-hidden" : ""}`);
    tile.dataset.name = item.name;
    tile.draggable = true;

    if (item.video) {
      tile.appendChild(
        el("div", "file-video", `🎬<br />${escapeHtml(item.name)}<br />${fmtSize(item.size)}`)
      );
    } else {
      const img = el("img");
      img.src = thumb(item.url, 320);
      img.alt = item.name;
      img.loading = "lazy";
      tile.appendChild(img);
    }

    if (!item.hidden) {
      const index = visible.indexOf(item) + 1;
      tile.appendChild(el("div", "idx", String(index)));
    }
    if (item.name === current.cover) tile.appendChild(el("div", "star", "⭐"));

    tile.appendChild(el("div", "name", escapeHtml(item.name)));

    const tools = el("div", "tile-tools");

    if (!item.hidden) {
      const cover = el("button", null, "⭐ Bìa");
      cover.title = "Dùng làm ảnh bìa";
      cover.onclick = () => setCover(item.name);
      tools.appendChild(cover);
    }

    const toggle = el("button", null, item.hidden ? "👁 Hiện" : "🚫 Ẩn");
    toggle.title = item.hidden ? "Hiện lại trên web" : "Giữ file nhưng không hiện trên web";
    toggle.onclick = () => toggleHidden(item.name);
    tools.appendChild(toggle);

    const del = el("button", "del", "🗑");
    del.title = "Xóa ảnh";
    del.onclick = () => deleteImage(item.name);
    tools.appendChild(del);

    tile.appendChild(tools);
    grid.appendChild(tile);
  });

  enableTileDrag(grid);
}

function fmtSize(bytes) {
  return bytes > 1048576
    ? `${(bytes / 1048576).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function currentOrder() {
  const names = [...$("#image-grid").querySelectorAll(".tile")].map((t) => t.dataset.name);
  const hiddenSet = new Set(current.items.filter((i) => i.hidden).map((i) => i.name));
  return {
    images: names.filter((n) => !hiddenSet.has(n)),
    hidden: names.filter((n) => hiddenSet.has(n)),
  };
}

async function saveOrder(order) {
  await guard("Đang lưu…", async () => {
    await post("/api/images/order", { id: current.id, ...order });
    scheduleBuild();
    await load();
  });
}

function enableTileDrag(grid) {
  let dragged = null;

  grid.querySelectorAll(".tile").forEach((tile) => {
    tile.addEventListener("dragstart", (e) => {
      dragged = tile;
      tile.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", tile.dataset.name);
    });

    tile.addEventListener("dragend", () => {
      tile.classList.remove("dragging");
      grid.querySelectorAll(".drop-target").forEach((n) => n.classList.remove("drop-target"));
      dragged = null;
    });

    tile.addEventListener("dragover", (e) => {
      if (!dragged || dragged === tile) return;
      e.preventDefault();
      e.stopPropagation();
      tile.classList.add("drop-target");
    });

    tile.addEventListener("dragleave", () => tile.classList.remove("drop-target"));

    tile.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      tile.classList.remove("drop-target");
      if (!dragged || dragged === tile) return;

      const tiles = [...grid.querySelectorAll(".tile")];
      const from = tiles.indexOf(dragged);
      const to = tiles.indexOf(tile);
      grid.insertBefore(dragged, from < to ? tile.nextSibling : tile);

      saveOrder(currentOrder());
    });
  });
}

async function setCover(name) {
  await guard("Đang đặt ảnh bìa…", async () => {
    await post("/api/images/cover", { id: current.id, name });
    scheduleBuild();
    await load();
  });
  toast("Đã đổi ảnh bìa", "ok");
}

async function toggleHidden(name) {
  const order = currentOrder();
  if (order.hidden.includes(name)) {
    order.hidden = order.hidden.filter((n) => n !== name);
    order.images.push(name);
  } else {
    order.images = order.images.filter((n) => n !== name);
    order.hidden.push(name);
  }
  await saveOrder(order);
}

function deleteImage(name) {
  confirmBox(
    "Xóa ảnh?",
    `“${name}” sẽ được chuyển vào admin/_trash/ (vẫn lấy lại được), và bị gỡ khỏi web sau khi bạn đăng lên.`,
    "Xóa ảnh",
    async () => {
      await guard("Đang xóa…", async () => {
        await post("/api/images/delete", { id: current.id, name });
        scheduleBuild();
        await load();
      });
      toast("Đã xóa ảnh", "ok");
    }
  );
}

/* ---- tải ảnh lên ---- */

async function uploadFiles(files) {
  const list = [...files];
  if (!list.length) return;

  const projectId = current.id;
  let done = 0;

  busy(`Đang thêm ảnh 0/${list.length}…`);
  try {
    for (const file of list) {
      $("#busy-text").textContent = `Đang thêm ảnh ${done + 1}/${list.length} — ${file.name}`;
      const res = await fetch("/api/images/upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "X-Project-Id": b64(projectId),
          "X-Filename": b64(file.name),
        },
        body: file,
      });
      const data = await res.json().catch(() => ({ ok: false, error: "Lỗi không rõ" }));
      if (!res.ok || data.ok === false) {
        toast(`${file.name}: ${data.error}`, "err");
      } else {
        done += 1;
      }
    }
    scheduleBuild();
    await load();
  } finally {
    idle();
  }

  if (done) toast(`Đã thêm ${done} ảnh`, "ok");
}

function b64(text) {
  return btoa(String.fromCharCode(...new TextEncoder().encode(text)));
}

/* ---------------------------------------------------------
   Sự kiện màn sửa
--------------------------------------------------------- */

$("#btn-back").onclick = showList;

$("#btn-save-meta").onclick = async () => {
  await guard("Đang lưu…", async () => {
    await post("/api/project/save", {
      id: current.id,
      title: $("#f-title").value,
      category: $("#f-category").value,
      description: $("#f-description").value,
      wide: $("#f-wide").checked,
    });
    scheduleBuild();
    await load();
  });
  toast("Đã lưu thông tin", "ok");
};

$("#btn-open-project").onclick = () =>
  post("/api/open-folder", { id: current.id }).catch((err) => toast(err.message, "err"));

$("#btn-delete-project").onclick = () =>
  confirmBox(
    "Xóa project?",
    `Cả thư mục “${current.folder}” và toàn bộ ảnh bên trong sẽ được chuyển vào admin/_trash/. Vẫn lấy lại được nếu cần.`,
    "Xóa project",
    async () => {
      await guard("Đang xóa…", async () => {
        await post("/api/project/delete", { id: current.id });
        current = null;
        scheduleBuild();
        await load();
      });
      showList();
      toast("Đã xóa project", "ok");
    }
  );

$("#btn-add-image").onclick = () => $("#file-input").click();

$("#file-input").onchange = (e) => {
  uploadFiles(e.target.files);
  e.target.value = "";
};

const dropzone = $("#dropzone");
["dragenter", "dragover"].forEach((type) =>
  dropzone.addEventListener(type, (e) => {
    if (!e.dataTransfer.types.includes("Files")) return;
    e.preventDefault();
    dropzone.classList.add("over");
  })
);
["dragleave", "drop"].forEach((type) =>
  dropzone.addEventListener(type, (e) => {
    if (type === "drop" && e.dataTransfer.types.includes("Files")) e.preventDefault();
    dropzone.classList.remove("over");
  })
);
dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files?.length) uploadFiles(e.dataTransfer.files);
});

/* ---------------------------------------------------------
   Thanh trên
--------------------------------------------------------- */

$("#btn-rescan").onclick = async () => {
  await guard("Đang quét thư mục…", async () => {
    await post("/api/build");
    await load();
  });
  const added = PROJECTS.reduce((sum, p) => sum + p.new_count, 0);
  toast(added ? `Tìm thấy ${added} ảnh mới` : "Đã quét xong, không có ảnh mới", "ok");
};

$("#btn-quit").onclick = () =>
  confirmBox(
    "Tắt app?",
    "Máy chủ localhost sẽ dừng. Ảnh và thay đổi đã lưu vẫn còn nguyên trên máy — chỉ những gì chưa bấm “Đăng lên web” là chưa lên mạng.",
    "Tắt app",
    async () => {
      try {
        await post("/api/quit");
      } catch {
        /* máy chủ tắt giữa chừng nên không kịp trả lời — bình thường */
      }
      document.body.innerHTML =
        '<div style="display:grid;place-items:center;height:80vh;gap:14px;text-align:center">' +
        '<img src="/admin/icon.png" width="64" height="64" style="border-radius:14px;opacity:.5" />' +
        '<p style="color:#8f8f8f;font-size:14px">Đã tắt app. Bạn có thể đóng tab này.<br />' +
        "Mở lại bằng icon <b>Portfolio Manager</b> trên Desktop.</p></div>";
    }
  );

$("#btn-open-root").onclick = () =>
  post("/api/open-folder", {}).catch((err) => toast(err.message, "err"));

$("#btn-new").onclick = async () => {
  if (!THEME) {
    try {
      const data = await api("/api/theme");
      THEME = data.theme;
      THEME_FIELDS = data.fields;
      THEME_DEFAULTS = data.defaults;
    } catch {
      THEME = { grid: { auto_pattern: true, wide_per_block: 2, narrow_per_block: 3 } };
    }
  }

  const wideCount = Math.max(0, THEME.grid.wide_per_block);
  const narrowCount = Math.max(0, THEME.grid.narrow_per_block);
  const blockSize = wideCount + narrowCount || 1;

  // Nhãn phải tính từ VỊ TRÍ THẬT của project mới trong lưới, không phải
  // từ đầu khối — đang có 12 project thì cái thứ 13 rơi vào giữa nhịp.
  const batDau = PROJECTS.length;
  const slots = [];
  for (let i = 0; i < blockSize; i++) {
    const viTri = batDau + i;
    const big = THEME.grid.auto_pattern ? viTri % blockSize < wideCount : i < wideCount;
    slots.push({ big, label: big ? "Thẻ lớn" : "Thẻ nhỏ", stt: viTri + 1 });
  }

  const body = el("div");
  body.appendChild(
    el(
      "p",
      "hint",
      `Trang portfolio xếp theo nhịp <b>${wideCount} thẻ lớn + ${narrowCount} thẻ nhỏ</b> lặp lại.
       Tạo trọn <b>${blockSize}</b> cái một lần thì nhịp không bị lệch.<br />
       Nhãn bên dưới là kích thước thật của thẻ khi lên web.
       Ô nào bỏ trống sẽ được đặt tên tạm, đổi lại sau cũng được.`
    )
  );

  const rows = slots.map((slot, i) => {
    const input = el("input");
    input.type = "text";
    input.placeholder = `PROJECT MOI ${i + 1}`;
    const wrap = el("div", "slot-row");
    wrap.appendChild(
      el("label", slot.big ? "slot big" : "slot", `#${slot.stt} · ${slot.label}`)
    );
    wrap.appendChild(input);
    body.appendChild(wrap);
    return input;
  });

  const one = el("input");
  one.type = "checkbox";
  const oneWrap = el("label", "check");
  oneWrap.append(one, document.createTextNode(" Chỉ tạo 1 project (bố cục có thể lệch nhịp)"));
  body.appendChild(oneWrap);

  one.onchange = () => {
    rows.forEach((input, i) => {
      input.closest(".slot-row").style.display = one.checked && i > 0 ? "none" : "";
    });
  };

  const doCreate = async () => {
    const wanted = one.checked ? rows.slice(0, 1) : rows;
    const items = wanted.map((input, i) => {
      const name = input.value.trim() || input.placeholder;
      return { name, title: name };
    });

    const names = items.map((x) => x.name.toLowerCase());
    if (new Set(names).size !== names.length) {
      return toast("Có hai ô trùng tên thư mục", "err");
    }

    closeModal();
    const res = await guard("Đang tạo…", async () => {
      const r = await post("/api/project/create", { items });
      scheduleBuild();
      await load();
      return r;
    });

    if (res.errors && res.errors.length) toast(res.errors.join(" · "), "err");
    toast(`Đã tạo ${res.created.length} project`, "ok");
    if (res.created.length === 1) openProject(res.created[0].id);
  };

  modal({
    title: "Tạo project mới",
    body,
    actions: [
      { label: "Hủy", onClick: closeModal },
      { label: "Tạo", kind: "primary", onClick: doCreate },
    ],
  });

  setTimeout(() => rows[0].focus(), 50);
};

function tagged(labelText, input) {
  const wrap = el("div");
  wrap.appendChild(el("label", null, labelText));
  wrap.appendChild(input);
  return wrap;
}

/* ---- Chưa đăng nhập GitHub ---- */

function showLoginNeeded(data) {
  modal({
    title: "Cần đăng nhập GitHub một lần",
    body: [
      el(
        "p",
        "hint",
        `Thay đổi đã được <b>lưu trên máy</b> (${data.ahead || 1} lần lưu chờ đăng), nhưng GitHub
         chưa biết bạn là ai nên không cho đẩy lên.<br /><br />
         Bấm nút bên dưới — một <b>cửa sổ đen</b> sẽ mở ra và hiện ô đăng nhập GitHub.
         Đăng nhập xong, cửa sổ đó báo thành công thì đóng lại, quay về đây bấm
         “Đăng lên web” lần nữa. Chỉ phải làm một lần duy nhất.`
      ),
      el("div", "log error", escapeHtml(data.error || "")),
    ],
    actions: [
      { label: "Để sau", onClick: closeModal },
      {
        label: "Mở cửa sổ đăng nhập",
        kind: "primary",
        onClick: async () => {
          closeModal();
          try {
            await post("/api/git/terminal");
            toast("Đã mở cửa sổ đăng nhập — làm theo hướng dẫn trong đó", "ok");
          } catch (err) {
            toast(err.message, "err");
          }
        },
      },
    ],
  });
}

/* ---- Đăng lên web ---- */

$("#btn-publish").onclick = async () => {
  const status = await guard("Đang kiểm tra thay đổi…", async () => {
    await post("/api/build");
    return api("/api/git/status");
  });

  const body = el("div");

  if (!status.changes.length && !status.ahead) {
    body.appendChild(el("p", "hint", "Không có thay đổi nào so với bản đang chạy trên web."));
    return modal({
      title: "Đăng lên web",
      body,
      actions: [{ label: "Đóng", onClick: closeModal }],
    });
  }

  const parts = [];
  if (status.changes.length) parts.push(`<b>${status.changes.length}</b> thay đổi mới`);
  if (status.ahead) {
    parts.push(
      `<b>${status.ahead}</b> lần lưu trước đó <b style="color:var(--red)">chưa lên được GitHub</b>`
    );
  }

  body.appendChild(
    el(
      "p",
      "hint",
      `Sẽ đẩy ${parts.join(" và ")} lên nhánh <code>${escapeHtml(
        status.branch
      )}</code>. Web tự cập nhật sau 1–2 phút.`
    )
  );

  if (status.changes.length) {
    const files = el("div", "file-list");
    status.changes.slice(0, 300).forEach((change) => {
      files.innerHTML += `<span class="st">${escapeHtml(change.state)}</span>${escapeHtml(
        change.path
      )}<br />`;
    });
    if (status.changes.length > 300) {
      files.innerHTML += `… và ${status.changes.length - 300} file nữa`;
    }
    body.appendChild(files);
  }

  const message = el("input");
  message.type = "text";
  message.value = "Cập nhật ảnh portfolio";
  body.appendChild(tagged("Ghi chú thay đổi", message));

  modal({
    title: "Đăng lên web",
    body,
    actions: [
      { label: "Hủy", onClick: closeModal },
      {
        label: "Đăng ngay",
        kind: "primary",
        onClick: async () => {
          closeModal();
          busy("Đang đẩy lên GitHub… (ảnh nặng có thể mất vài phút)");
          try {
            const res = await fetch("/api/git/publish", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: message.value }),
            });
            const data = await res.json();
            idle();

            if (data.ok && data.nothing) return toast(data.message, "ok");

            if (data.ok) {
              toast("Đã đăng lên web thành công!", "ok");
              return modal({
                title: "Đã đăng lên web ✅",
                body: [
                  el(
                    "p",
                    "hint",
                    'GitHub Pages và Vercel sẽ tự build lại. Chờ khoảng 1–2 phút rồi bấm "Mở web thật".'
                  ),
                  el("div", "log", escapeHtml(data.log || "")),
                ],
                actions: [
                  {
                    label: "Mở web thật",
                    onClick: () =>
                      window.open("https://portfolio-tiev.vercel.app/portfolio.html", "_blank"),
                  },
                  { label: "Đóng", kind: "primary", onClick: closeModal },
                ],
              });
            }

            if (data.auth) return showLoginNeeded(data);

            const stepText =
              { add: "gom file", commit: "lưu thay đổi", push: "đẩy lên GitHub" }[data.step] ||
              "xử lý";
            modal({
              title: `Lỗi khi ${stepText}`,
              body: [
                el(
                  "p",
                  "hint",
                  data.committed
                    ? "Thay đổi đã được <b>lưu trên máy</b> nhưng <b>chưa lên GitHub</b>. Sửa lỗi bên dưới rồi bấm “Đăng lên web” lại — app sẽ đẩy tiếp, không mất gì cả."
                    : "Chưa có gì được đẩy lên. Nội dung lỗi từ git:"
                ),
                el("div", "log error", escapeHtml(data.error || "")),
              ],
              actions: [{ label: "Đóng", kind: "primary", onClick: closeModal }],
            });
          } catch (err) {
            idle();
            toast(err.message, "err");
          }
        },
      },
    ],
  });
};

/* ---------------------------------------------------------
   Khởi động
--------------------------------------------------------- */

load().catch((err) => toast(err.message, "err"));

/* =========================================================
   MÀN GIAO DIỆN — màu sắc, chữ, bố cục cho TOÀN BỘ web
   ========================================================= */

let THEME = null;
let THEME_FIELDS = [];
let THEME_DEFAULTS = null;

// Nạp sớm để lưới project trong app hiện đúng tỉ lệ ngay từ lần mở đầu tiên
api("/api/theme")
  .then((data) => {
    THEME = data.theme;
    THEME_FIELDS = data.fields;
    THEME_DEFAULTS = data.defaults;
    applyGridTokens();
  })
  .catch(() => {});

const T = {
  auto: "#t-auto-pattern",
  wide: "#t-wide",
  narrow: "#t-narrow",
  font: "#t-font",
  fallback: "#t-fallback",
  container: "#t-container",
  radius: "#t-radius",
  cardRadius: "#t-card-radius",
  colGap: "#t-col-gap",
  rowGap: "#t-row-gap",
  ratio: "#t-ratio",
  ratioWide: "#t-ratio-wide",
  ratioMobile: "#t-ratio-mobile",
};

/* ---- chuyển màn ---- */

function showTheme() {
  $("#view-list").classList.add("hidden");
  $("#view-edit").classList.add("hidden");
  $("#view-theme").classList.remove("hidden");
  $("#tab-projects").classList.remove("is-on");
  $("#tab-theme").classList.add("is-on");
  window.scrollTo(0, 0);
  if (!THEME) loadTheme();
  else refreshPreview();
}

function showProjects() {
  $("#view-theme").classList.add("hidden");
  $("#tab-theme").classList.remove("is-on");
  $("#tab-projects").classList.add("is-on");
  if (current) openProject(current.id);
  else showList();
}

$("#tab-theme").onclick = showTheme;
$("#tab-projects").onclick = showProjects;

/* ---- nạp cấu hình ---- */

async function loadTheme() {
  const data = await guard("Đang tải giao diện…", () => api("/api/theme"));
  THEME = data.theme;
  THEME_FIELDS = data.fields;
  THEME_DEFAULTS = data.defaults;
  renderColorFields();
  fillThemeForm();
  refreshPreview();
}

function renderColorFields() {
  const host = $("#color-groups");
  host.innerHTML = "";

  const groups = [];
  THEME_FIELDS.forEach((f) => {
    let g = groups.find((x) => x.name === f.group);
    if (!g) groups.push((g = { name: f.group, items: [] }));
    g.items.push(f);
  });

  groups.forEach((g) => {
    const box = el("div", "color-group");
    box.appendChild(el("h3", null, escapeHtml(g.name)));

    g.items.forEach((f) => {
      const row = el("div", "color-row");

      const swatch = el("input");
      swatch.type = "color";
      swatch.dataset.token = f.token;

      const hex = el("input");
      hex.type = "text";
      hex.dataset.token = f.token;
      hex.spellcheck = false;

      const label = el(
        "div",
        "cl",
        `${escapeHtml(f.label)}${f.hint ? `<small>${escapeHtml(f.hint)}</small>` : ""}`
      );

      // Hai ô luôn đi cùng nhau
      swatch.oninput = () => {
        hex.value = swatch.value;
        THEME.colors[f.token] = swatch.value;
        applyPreviewTheme();
      };
      hex.oninput = () => {
        const v = hex.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(v)) {
          swatch.value = v;
          THEME.colors[f.token] = v;
          applyPreviewTheme();
        }
      };

      row.append(swatch, hex, label);
      box.appendChild(row);
    });

    host.appendChild(box);
  });
}

function fillThemeForm() {
  Object.entries(THEME.colors).forEach(([token, value]) => {
    document.querySelectorAll(`[data-token="${token}"]`).forEach((input) => {
      input.value = value;
    });
  });

  $(T.auto).checked = !!THEME.grid.auto_pattern;
  $(T.wide).value = THEME.grid.wide_per_block;
  $(T.narrow).value = THEME.grid.narrow_per_block;
  $(T.font).value = THEME.font.family;
  $(T.fallback).value = THEME.font.fallback;
  $(T.container).value = THEME.layout.container;
  $(T.radius).value = THEME.layout.radius;
  $(T.cardRadius).value = THEME.layout.card_radius;
  $(T.colGap).value = THEME.layout.grid_col_gap;
  $(T.rowGap).value = THEME.layout.grid_row_gap;
  $(T.ratio).value = THEME.layout.card_ratio;
  $(T.ratioWide).value = THEME.layout.card_ratio_wide;
  $(T.ratioMobile).value = THEME.layout.card_ratio_mobile;
}

function readThemeForm() {
  const num = (sel, fallback) => {
    const v = parseInt($(sel).value, 10);
    return Number.isFinite(v) ? v : fallback;
  };
  THEME.grid.auto_pattern = $(T.auto).checked;
  THEME.grid.wide_per_block = num(T.wide, 2);
  THEME.grid.narrow_per_block = num(T.narrow, 3);
  THEME.font.family = $(T.font).value.trim() || "Montserrat";
  THEME.font.fallback = $(T.fallback).value.trim() || "Arial, sans-serif";
  THEME.layout.container = num(T.container, 850);
  THEME.layout.radius = num(T.radius, 8);
  THEME.layout.card_radius = num(T.cardRadius, 7);
  THEME.layout.grid_col_gap = num(T.colGap, 18);
  THEME.layout.grid_row_gap = num(T.rowGap, 31);
  THEME.layout.card_ratio = $(T.ratio).value.trim() || "1 / 1";
  THEME.layout.card_ratio_wide = $(T.ratioWide).value.trim() || "4500 / 3519";
  THEME.layout.card_ratio_mobile = $(T.ratioMobile).value.trim() || "1.55 / 1";
}

Object.values(T).forEach((sel) => {
  const input = $(sel);
  if (!input) return;
  input.addEventListener("input", () => {
    readThemeForm();
    applyPreviewTheme();
  });
});

/* ---- xem trước trực tiếp ---- */

function themeCss() {
  const c = THEME.colors;
  const l = THEME.layout;
  const decls = Object.entries(c).map(([k, v]) => `--${k}:${v};`);
  decls.push(`--font-main:"${THEME.font.family}", ${THEME.font.fallback};`);
  decls.push(`--container:${l.container}px;`);
  decls.push(`--radius:${l.radius}px;`);
  decls.push(`--card-radius:${l.card_radius}px;`);
  decls.push(`--grid-col-gap:${l.grid_col_gap}px;`);
  decls.push(`--grid-row-gap:${l.grid_row_gap}px;`);
  decls.push(`--card-ratio:${l.card_ratio};`);
  decls.push(`--card-ratio-wide:${l.card_ratio_wide};`);
  decls.push(`--card-ratio-mobile:${l.card_ratio_mobile};`);
  decls.push("--yellow:var(--accent);");
  return `:root{${decls.join("")}}`;
}

/** Bơm thẳng css vào khung xem trước — thấy ngay, chưa ghi ra file. */
function applyPreviewTheme() {
  const frame = $("#preview-frame");
  const doc = frame?.contentDocument;
  if (!doc || !THEME) return;
  let tag = doc.getElementById("preview-theme");
  if (!tag) {
    tag = doc.createElement("style");
    tag.id = "preview-theme";
    doc.head.appendChild(tag);
  }
  tag.textContent = themeCss();
  applyGridTokens();
}

let previewPage = "index.html";

function refreshPreview() {
  const frame = $("#preview-frame");
  const url = previewPage === "project-detail.html" ? `${previewPage}?preview=1` : previewPage;
  frame.src = `/${url}#t=${Date.now()}`;
  frame.onload = applyPreviewTheme;
}

document.querySelectorAll(".preview-tabs .tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".preview-tabs .tab").forEach((t) => t.classList.remove("is-on"));
    tab.classList.add("is-on");
    previewPage = tab.dataset.page;
    refreshPreview();
  };
});

document.querySelectorAll(".preview-sizes .tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".preview-sizes .tab").forEach((t) => t.classList.remove("is-on"));
    tab.classList.add("is-on");
    $("#preview-frame").style.width = tab.dataset.w;
  };
});

/* ---- lưu / đặt lại ---- */

$("#btn-theme-save").onclick = async () => {
  readThemeForm();
  await guard("Đang lưu giao diện…", async () => {
    await post("/api/theme/save", { theme: THEME });
    await load();
  });
  toast("Đã lưu giao diện cho toàn bộ web", "ok");
  refreshPreview();
};

$("#btn-theme-reset").onclick = () =>
  confirmBox(
    "Về giao diện mặc định?",
    "Toàn bộ màu sắc, chữ và bố cục sẽ quay lại như bản gốc. Ảnh và project không bị ảnh hưởng.",
    "Đặt lại",
    async () => {
      await guard("Đang đặt lại…", async () => {
        const res = await post("/api/theme/reset");
        THEME = res.theme;
        fillThemeForm();
        await load();
      });
      refreshPreview();
      toast("Đã về mặc định", "ok");
    }
  );

/* =========================================================
   MÀN TRANG CHỦ — chữ và ảnh của index.html
   ========================================================= */

let HOME = null;
let HOME_SLOTS = [];
let HOME_ICONS = [];
let HOME_LABELS = {};

const H = {
  title: "#h-title",
  subLeft: "#h-sub-left",
  subRight: "#h-sub-right",
  btnText: "#h-btn-text",
  btnHref: "#h-btn-href",
  aHeading: "#a-heading",
  aText: "#a-text",
  aBtnText: "#a-btn-text",
  aBtnHref: "#a-btn-href",
  aImgAlt: "#a-img-alt",
  cHeading: "#c-heading",
  cText: "#c-text",
  cImgAlt: "#c-img-alt",
  sHeading: "#s-heading",
};

function showHome() {
  ["#view-list", "#view-edit", "#view-theme"].forEach((v) => $(v).classList.add("hidden"));
  $("#view-home").classList.remove("hidden");
  ["#tab-projects", "#tab-theme"].forEach((t) => $(t).classList.remove("is-on"));
  $("#tab-home").classList.add("is-on");
  window.scrollTo(0, 0);
  if (!HOME) loadHome();
}

// Ba tab loại trừ nhau — hai màn kia phải tắt màn trang chủ khi bật lên
const _showTheme = showTheme;
const _showProjects = showProjects;

function hideHome() {
  $("#view-home").classList.add("hidden");
  $("#tab-home").classList.remove("is-on");
}

$("#tab-home").onclick = showHome;
$("#tab-theme").onclick = () => {
  hideHome();
  _showTheme();
};
$("#tab-projects").onclick = () => {
  hideHome();
  _showProjects();
};

/* ---- nạp ---- */

async function loadHome() {
  const data = await guard("Đang tải trang chủ…", () => api("/api/home"));
  HOME = data.home;
  HOME_SLOTS = data.slots;
  HOME_ICONS = data.icons;
  HOME_LABELS = data.labels;
  fillHomeForm();
  renderSections();
  renderSkills();
  renderSlots();
}

function fillHomeForm() {
  $(H.title).value = HOME.hero.title;
  $(H.subLeft).value = HOME.hero.subtitle_left;
  $(H.subRight).value = HOME.hero.subtitle_right;
  $(H.btnText).value = HOME.hero.button_text;
  $(H.btnHref).value = HOME.hero.button_href;

  $(H.aHeading).value = HOME.about.heading;
  $(H.aText).value = HOME.about.text;
  $(H.aBtnText).value = HOME.about.button_text;
  $(H.aBtnHref).value = HOME.about.button_href;
  $(H.aImgAlt).value = HOME.about.image_alt;

  $(H.cHeading).value = HOME.clients.heading;
  $(H.cText).value = HOME.clients.text;
  $(H.cImgAlt).value = HOME.clients.image_alt;

  $(H.sHeading).value = HOME.skills.heading;
}

function readHomeForm() {
  HOME.hero = {
    title: $(H.title).value,
    subtitle_left: $(H.subLeft).value,
    subtitle_right: $(H.subRight).value,
    button_text: $(H.btnText).value,
    button_href: $(H.btnHref).value,
  };
  HOME.about = {
    heading: $(H.aHeading).value,
    text: $(H.aText).value,
    button_text: $(H.aBtnText).value,
    button_href: $(H.aBtnHref).value,
    image_alt: $(H.aImgAlt).value,
  };
  HOME.clients = {
    heading: $(H.cHeading).value,
    text: $(H.cText).value,
    image_alt: $(H.cImgAlt).value,
  };
  HOME.skills = {
    heading: $(H.sHeading).value,
    items: [...document.querySelectorAll("#skill-rows .skill-row")].map((row) => ({
      icon: row.querySelector("select").value,
      text: row.querySelector('input[type="text"]').value,
    })),
  };
  HOME.sections = [...document.querySelectorAll("#section-list .section-item")].map(
    (item) => item.dataset.key
  );
  HOME.hidden = [...document.querySelectorAll("#section-list .section-item")]
    .filter((item) => !item.querySelector("input").checked)
    .map((item) => item.dataset.key);
}

/* ---- thứ tự & ẩn hiện các khối ---- */

function renderSections() {
  const host = $("#section-list");
  host.innerHTML = "";

  HOME.sections.forEach((key) => {
    const off = HOME.hidden.includes(key);
    const item = el("div", "section-item" + (off ? " off" : ""));
    item.dataset.key = key;
    item.draggable = true;

    const check = el("input");
    check.type = "checkbox";
    check.checked = !off;
    check.onchange = () => item.classList.toggle("off", !check.checked);

    item.append(
      el("span", "grip", "⠿"),
      check,
      el("span", null, escapeHtml(HOME_LABELS[key] || key))
    );
    host.appendChild(item);
  });

  let dragged = null;
  host.querySelectorAll(".section-item").forEach((item) => {
    item.addEventListener("dragstart", () => {
      dragged = item;
      item.classList.add("dragging");
    });
    item.addEventListener("dragend", () => {
      item.classList.remove("dragging");
      host.querySelectorAll(".drop-target").forEach((n) => n.classList.remove("drop-target"));
      dragged = null;
    });
    item.addEventListener("dragover", (e) => {
      if (!dragged || dragged === item) return;
      e.preventDefault();
      item.classList.add("drop-target");
    });
    item.addEventListener("dragleave", () => item.classList.remove("drop-target"));
    item.addEventListener("drop", (e) => {
      e.preventDefault();
      item.classList.remove("drop-target");
      if (!dragged || dragged === item) return;
      const all = [...host.querySelectorAll(".section-item")];
      const from = all.indexOf(dragged);
      const to = all.indexOf(item);
      host.insertBefore(dragged, from < to ? item.nextSibling : item);
    });
  });
}

/* ---- danh sách kỹ năng ---- */

function countSkills() {
  $("#skill-count").textContent =
    "(" + document.querySelectorAll("#skill-rows .skill-row").length + ")";
}

function renderSkills() {
  const host = $("#skill-rows");
  host.innerHTML = "";
  HOME.skills.items.forEach((item) => host.appendChild(skillRow(item)));
  countSkills();
}

function skillRow(item) {
  const row = el("div", "skill-row");

  const preview = el("img");
  preview.src = "/assets/icons/" + item.icon;
  preview.alt = "";

  const select = el("select");
  HOME_ICONS.forEach((name) => {
    const opt = el("option", null, name.replace(".svg", ""));
    opt.value = name;
    if (name === item.icon) opt.selected = true;
    select.appendChild(opt);
  });
  select.onchange = () => {
    preview.src = "/assets/icons/" + select.value;
  };

  const text = el("input");
  text.type = "text";
  text.value = item.text;

  const remove = el("button", "rm", "✕");
  remove.title = "Bỏ dòng này";
  remove.onclick = () => {
    row.remove();
    countSkills();
  };

  row.append(preview, select, text, remove);
  return row;
}

$("#btn-add-skill").onclick = () => {
  $("#skill-rows").appendChild(skillRow({ icon: HOME_ICONS[0] || "ps.svg", text: "" }));
  countSkills();
};

/* ---- hai khung ảnh ---- */

function renderSlots() {
  document.querySelectorAll(".slot[data-slot]").forEach((host) => {
    const slot = HOME_SLOTS.find((s) => s.key === host.dataset.slot);
    if (!slot) return;

    host.innerHTML = "";
    const box = el("div", "slot-box");

    const head = el("div", "slot-head");
    head.appendChild(
      el(
        "div",
        null,
        "<strong>" +
          escapeHtml(slot.label) +
          "</strong><small>📁 assets/home/" +
          escapeHtml(slot.folder) +
          "/ · " +
          escapeHtml(slot.where) +
          "</small>"
      )
    );

    const tools = el("div");
    const add = el("button", "btn ghost small", "+ Thêm ảnh");
    const picker = el("input");
    picker.type = "file";
    picker.accept = "image/*";
    picker.hidden = true;
    picker.onchange = async (e) => {
      await uploadSlot(slot.key, e.target.files[0]);
      e.target.value = "";
    };
    add.onclick = () => picker.click();

    const openBtn = el("button", "btn ghost small", "Thư mục");
    openBtn.onclick = () =>
      post("/api/home/open-folder", { key: slot.key }).catch((err) => toast(err.message, "err"));

    tools.append(add, openBtn, picker);
    head.appendChild(tools);
    box.appendChild(head);

    if (!slot.images.length) {
      box.appendChild(
        el(
          "p",
          "slot-empty",
          "Thư mục chưa có ảnh — web đang dùng tạm <code>" +
            escapeHtml(slot.fallback) +
            "</code>."
        )
      );
    } else {
      const grid = el("div", "slot-images");
      slot.images.forEach((img) => {
        const cell = el("div", "slot-pic" + (img.name === slot.active ? " on" : ""));
        cell.title = img.name + " — bấm để dùng ảnh này";

        const pic = el("img");
        pic.src = thumb(img.url, 260);
        pic.alt = img.name;
        pic.loading = "lazy";
        cell.appendChild(pic);

        if (img.name === slot.active) cell.appendChild(el("div", "tick", "✓"));

        const rm = el("button", "rm", "Xóa");
        rm.onclick = (e) => {
          e.stopPropagation();
          confirmBox(
            "Xóa ảnh?",
            "“" + img.name + "” sẽ được chuyển vào admin/_trash/ (vẫn lấy lại được).",
            "Xóa ảnh",
            async () => {
              const res = await guard("Đang xóa…", () =>
                post("/api/home/slot-delete", { key: slot.key, name: img.name })
              );
              HOME_SLOTS = res.slots;
              renderSlots();
              toast("Đã xóa ảnh", "ok");
            }
          );
        };
        cell.appendChild(rm);

        cell.onclick = async () => {
          if (img.name === slot.active) return;
          const res = await guard("Đang đổi ảnh…", () =>
            post("/api/home/slot-active", { key: slot.key, name: img.name })
          );
          HOME_SLOTS = res.slots;
          renderSlots();
          toast("Đã đổi ảnh trên trang chủ", "ok");
        };

        grid.appendChild(cell);
      });
      box.appendChild(grid);
    }

    host.appendChild(box);
  });
}

async function uploadSlot(key, file) {
  if (!file) return;
  busy("Đang thêm " + file.name + "…");
  try {
    const res = await fetch("/api/home/slot-upload", {
      method: "POST",
      headers: {
        "Content-Type": "application/octet-stream",
        "X-Slot": b64(key),
        "X-Filename": b64(file.name),
      },
      body: file,
    });
    const data = await res.json().catch(() => ({ ok: false, error: "Lỗi không rõ" }));
    if (!res.ok || data.ok === false) throw new Error(data.error);
    HOME_SLOTS = data.slots;
    renderSlots();
    toast("Đã thêm ảnh và dùng luôn", "ok");
  } catch (err) {
    toast(err.message, "err");
  } finally {
    idle();
  }
}

/* ---- lưu / đặt lại ---- */

$("#btn-home-save").onclick = async () => {
  readHomeForm();
  await guard("Đang lưu trang chủ…", async () => {
    await post("/api/home/save", { home: HOME });
    await load();
  });
  toast("Đã lưu nội dung trang chủ", "ok");
};

$("#btn-home-reset").onclick = () =>
  confirmBox(
    "Về nội dung mặc định?",
    "Toàn bộ chữ trên trang chủ quay lại như bản gốc. Ảnh trong thư mục không bị xóa.",
    "Đặt lại",
    async () => {
      const res = await guard("Đang đặt lại…", () => post("/api/home/reset"));
      HOME = res.home;
      fillHomeForm();
      renderSections();
      renderSkills();
      toast("Đã về mặc định", "ok");
    }
  );
