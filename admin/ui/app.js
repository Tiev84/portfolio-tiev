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
  if (current) {
    const fresh = PROJECTS.find((p) => p.id === current.id);
    if (fresh) openProject(fresh.id);
    else showList();
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

  enableCardDrag(grid);
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

$("#btn-new").onclick = () => {
  const name = el("input");
  name.type = "text";
  name.placeholder = "VD: KING JADES";
  const title = el("input");
  title.type = "text";
  title.placeholder = "VD: Campaign 8.3 King Jades";
  const category = el("input");
  category.type = "text";
  category.placeholder = "VD: SOCIAL MEDIA | POSM";

  const body = el("div");
  body.append(
    tagged("Tên thư mục trên máy", name),
    tagged("Tên project hiện trên web", title),
    tagged("Danh mục", category)
  );

  modal({
    title: "Tạo project mới",
    body,
    actions: [
      { label: "Hủy", onClick: closeModal },
      {
        label: "Tạo",
        kind: "primary",
        onClick: async () => {
          if (!name.value.trim()) return toast("Chưa nhập tên thư mục", "err");
          closeModal();
          const created = await guard("Đang tạo…", async () => {
            const res = await post("/api/project/create", {
              name: name.value,
              title: title.value || name.value,
              category: category.value,
            });
            scheduleBuild();
            await load();
            return res;
          });
          toast("Đã tạo project", "ok");
          openProject(created.id);
        },
      },
    ],
  });

  setTimeout(() => name.focus(), 50);
};

function tagged(labelText, input) {
  const wrap = el("div");
  wrap.appendChild(el("label", null, labelText));
  wrap.appendChild(input);
  return wrap;
}

/* ---- Đăng lên web ---- */

$("#btn-publish").onclick = async () => {
  const status = await guard("Đang kiểm tra thay đổi…", async () => {
    await post("/api/build");
    return api("/api/git/status");
  });

  const body = el("div");

  if (!status.changes.length) {
    body.appendChild(el("p", "hint", "Không có thay đổi nào so với bản đang chạy trên web."));
    return modal({
      title: "Đăng lên web",
      body,
      actions: [{ label: "Đóng", onClick: closeModal }],
    });
  }

  body.appendChild(
    el(
      "p",
      "hint",
      `Sẽ đẩy <b>${status.changes.length}</b> thay đổi lên nhánh <code>${escapeHtml(
        status.branch
      )}</code> của GitHub. Web sẽ tự cập nhật sau 1–2 phút.`
    )
  );

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
                    ? "Thay đổi đã được lưu (commit) nhưng chưa đẩy lên được. Bạn có thể mở GitHub Desktop bấm Push, hoặc thử lại."
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
