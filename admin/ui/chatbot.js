/* =========================================================
   KỊCH BẢN CHATBOT

   Soạn và kiểm tra ở đây, rồi chép sang tawk.to.

   Vì sao không đẩy thẳng lên tawk.to: REST API của họ không có
   endpoint nào tạo/sửa hội thoại (chỉ có property, ticket, thống
   kê, webhook, Knowledge Base), còn JavaScript API thì không chèn
   được tin nhắn bot hay nút trả lời nhanh. Chi tiết ở đầu file
   admin/chatbot.py.

   File này chạy sau app.js nên dùng chung được các hàm tiện ích
   ($, el, api, post, modal, toast, guard, escapeHtml...).
   ========================================================= */

let BOT = null;
let BOT_MAX = 4;

/* ---- chuyển tab ---------------------------------------- */

const _homeTruoc = showHome;
const _themeTruoc = showTheme;
const _projectsTruoc = showProjects;

function hideChatbot() {
  $("#view-chatbot").classList.add("hidden");
  $("#tab-chatbot").classList.remove("is-on");
}

function showChatbot() {
  ["#view-list", "#view-edit", "#view-theme", "#view-home"].forEach((v) =>
    $(v).classList.add("hidden")
  );
  ["#tab-projects", "#tab-home", "#tab-theme"].forEach((t) =>
    $(t).classList.remove("is-on")
  );
  $("#view-chatbot").classList.remove("hidden");
  $("#tab-chatbot").classList.add("is-on");
  window.scrollTo(0, 0);
  if (!BOT) loadBot().catch(() => {});
}

$("#tab-chatbot").onclick = showChatbot;
$("#tab-home").onclick = () => {
  hideChatbot();
  _homeTruoc();
};
$("#tab-theme").onclick = () => {
  hideChatbot();
  hideHome();
  _themeTruoc();
};
$("#tab-projects").onclick = () => {
  hideChatbot();
  hideHome();
  _projectsTruoc();
};

/* ---- nạp & lưu ----------------------------------------- */

async function loadBot() {
  const d = await guard("Đang tải kịch bản…", () => api("/api/chatbot"));
  BOT = d.chatbot;
  BOT_MAX = d.max_replies;
  renderBot(d.issues);
}

async function saveBot() {
  const d = await guard("Đang lưu kịch bản…", () =>
    post("/api/chatbot/save", { chatbot: BOT })
  );
  BOT = d.chatbot;
  renderBot(d.issues);
  toast("Đã lưu kịch bản", "ok");
}

/* ---- trình soạn ---------------------------------------- */

function renderBot(issues) {
  const host = $("#bot-nodes");
  host.innerHTML = "";

  BOT.nodes.forEach((node, i) => {
    const card = el("div", "card bot-node");
    const head = el("div", "bot-node-head");
    head.appendChild(el("span", "bot-num", String(i + 1)));

    const tieuDe = el("input");
    tieuDe.className = "bot-title";
    tieuDe.value = node.title;
    tieuDe.placeholder = "Tên nút (chỉ bạn thấy)";
    tieuDe.oninput = () => {
      node.title = tieuDe.value;
      veSoDo();
    };
    head.appendChild(tieuDe);

    head.appendChild(el("span", "bot-slash", "/"));
    const ten = el("input");
    ten.className = "bot-key";
    ten.value = node.key;
    ten.spellcheck = false;
    ten.title = "Tên tắt bên tawk.to — nhân viên gõ /tên-tắt để gọi câu này";
    ten.oninput = () => {
      node.key = ten.value.trim();
      veSoDo();
    };
    head.appendChild(ten);

    const xoa = el("button", "btn danger small", "🗑");
    xoa.title = "Xóa nút này";
    xoa.onclick = () => {
      const key = node.key;
      BOT.nodes.splice(i, 1);
      // Gỡ luôn nút bấm nào đang trỏ tới nó, kẻo để lại nhánh gãy
      BOT.nodes.forEach((n) =>
        n.replies.forEach((r) => {
          if (r.to === key) r.to = "";
        })
      );
      renderBot();
    };
    head.appendChild(xoa);
    card.appendChild(head);

    const noiDung = el("textarea");
    noiDung.className = "bot-msg";
    noiDung.rows = 4;
    noiDung.value = node.message;
    noiDung.placeholder = "Câu bot trả lời khách…";
    noiDung.oninput = () => {
      node.message = noiDung.value;
    };
    card.appendChild(noiDung);

    card.appendChild(
      el("p", "hint", `Nút bấm khách thấy — tawk.to cho tối đa ${BOT_MAX} nút mỗi câu`)
    );

    node.replies.forEach((r, j) => {
      const dong = el("div", "bot-reply");

      const chu = el("input");
      chu.value = r.text;
      chu.placeholder = "Chữ trên nút";
      chu.oninput = () => {
        r.text = chu.value;
        veSoDo();
      };

      const den = el("select");
      den.appendChild(new Option("— chưa nối —", ""));
      BOT.nodes.forEach((n) => {
        if (n.key && n.key !== node.key) {
          den.appendChild(new Option(n.title || n.key, n.key));
        }
      });
      den.value = r.to;
      den.onchange = () => {
        r.to = den.value;
        veSoDo();
      };

      const bo = el("button", "btn danger small", "×");
      bo.title = "Bỏ nút bấm này";
      bo.onclick = () => {
        node.replies.splice(j, 1);
        renderBot();
      };

      dong.append(chu, el("span", "bot-arrow", "→"), den, bo);
      card.appendChild(dong);
    });

    if (node.replies.length < BOT_MAX) {
      const them = el("button", "btn ghost small", "+ Thêm nút bấm");
      them.onclick = () => {
        node.replies.push({ text: "", to: "" });
        renderBot();
      };
      card.appendChild(them);
    } else {
      card.appendChild(el("p", "hint", `Đã đủ ${BOT_MAX} nút — tawk.to không nhận thêm.`));
    }

    host.appendChild(card);
  });

  veSoDo();
  if (issues) veLoi(issues);
}

function veLoi(issues) {
  const box = $("#bot-issues");
  if (!issues.length) {
    box.classList.add("hidden");
    return;
  }
  box.classList.remove("hidden");
  box.innerHTML =
    `<b>${issues.length} chỗ cần xem lại trước khi chép sang tawk.to:</b><br />` +
    issues.map((i) => "• " + escapeHtml(i.y)).join("<br />");
}

function veSoDo() {
  const map = $("#bot-map");
  map.innerHTML = "";
  const ten = (k) => {
    const n = BOT.nodes.find((x) => x.key === k);
    return n ? n.title || n.key : "⚠ " + (k || "chưa nối");
  };
  BOT.nodes.forEach((n) => {
    const b = el("div", "map-node");
    b.appendChild(el("b", null, escapeHtml(n.title || n.key || "(chưa đặt tên)")));
    if (n.replies.length) {
      n.replies.forEach((r) => {
        const gay = !r.to || !BOT.nodes.some((x) => x.key === r.to);
        b.appendChild(
          el(
            "div",
            "map-edge" + (gay ? " bad" : ""),
            "↳ " + escapeHtml(r.text || "(chưa có chữ)") + " → " + escapeHtml(ten(r.to))
          )
        );
      });
    } else {
      b.appendChild(el("div", "map-edge end", "↳ kết thúc"));
    }
    map.appendChild(b);
  });
}

/* ---- các nút trên đầu trang ---------------------------- */

$("#btn-bot-add").onclick = () => {
  if (!BOT) return;
  BOT.nodes.push({ key: "", title: "Câu trả lời mới", message: "", replies: [] });
  renderBot();
  $("#bot-nodes").lastChild.scrollIntoView({ block: "center" });
};

$("#btn-bot-save").onclick = () => saveBot().catch(() => {});

$("#btn-bot-reset").onclick = () =>
  confirmBox(
    "Về mẫu gốc?",
    "Toàn bộ kịch bản bạn đang soạn sẽ bị thay bằng mẫu có sẵn.",
    "Về mẫu gốc",
    async () => {
      const d = await guard("Đang đặt lại…", () => post("/api/chatbot/reset"));
      BOT = d.chatbot;
      renderBot(d.issues);
      toast("Đã về mẫu gốc", "ok");
    }
  );

/* ---- chạy thử: bấm qua kịch bản y như khách sẽ thấy ----- */

$("#btn-bot-preview").onclick = () => {
  if (!BOT || !BOT.nodes.length) {
    toast("Chưa có nút nào", "err");
    return;
  }

  const dong = el("div", "bot-sim-log");
  const nut = el("div", "bot-sim-btns");
  const khung = el("div", "bot-sim");
  khung.append(dong, nut);

  function di(key) {
    const n = BOT.nodes.find((x) => x.key === key);
    if (!n) {
      dong.appendChild(el("div", "sim-err", "⚠ Không có nút “" + escapeHtml(key) + "” — nhánh gãy."));
      nut.innerHTML = "";
      return;
    }
    dong.appendChild(el("div", "sim-bot", escapeHtml(n.message).replace(/\n/g, "<br />")));
    dong.scrollTop = dong.scrollHeight;

    nut.innerHTML = "";
    if (!n.replies.length) {
      nut.appendChild(el("div", "hint", "— hết nhánh, từ đây khách nhắn tự do —"));
      return;
    }
    n.replies.forEach((r) => {
      const b = el("button", "btn ghost small", escapeHtml(r.text || "(chưa có chữ)"));
      b.onclick = () => {
        dong.appendChild(el("div", "sim-khach", escapeHtml(r.text)));
        di(r.to);
      };
      nut.appendChild(b);
    });
  }

  modal({
    title: "Chạy thử kịch bản",
    body: khung,
    actions: [{ label: "Đóng", kind: "primary", onClick: closeModal }],
  });
  di(BOT.nodes[0].key);
};

/* ---- xuất để chép sang tawk.to ------------------------- */

async function chepVao(text, btn) {
  const cu = btn.textContent;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "✓ đã chép";
    setTimeout(() => (btn.textContent = cu), 1400);
  } catch {
    toast("Trình duyệt không cho chép tự động — bôi đen rồi Ctrl+C", "err");
  }
}

$("#btn-bot-export").onclick = () => {
  if (!BOT) return;

  const body = [
    el(
      "p",
      "hint",
      "Mở <b>dashboard.tawk.to → Shortcuts → Add Shortcut</b>. Mỗi thẻ dưới đây là " +
        "một shortcut: chép từng ô sang đúng ô cùng tên bên đó."
    ),
  ];

  BOT.nodes.forEach((n, i) => {
    const card = el("div", "export-card");
    card.appendChild(el("h4", null, i + 1 + ". " + escapeHtml(n.title || n.key)));

    const o = (nhan, giaTri) => {
      const r = el("div", "export-row");
      r.appendChild(el("span", "export-label", nhan));
      r.appendChild(el("code", "export-val", escapeHtml(giaTri)));
      const b = el("button", "btn ghost small", "chép");
      b.onclick = () => chepVao(giaTri, b);
      r.appendChild(b);
      card.appendChild(r);
    };

    o("Shortcut name", n.key);
    o("Message", n.message);
    n.replies.forEach((r, j) => o("Suggested " + (j + 1), r.text));
    if (!n.replies.length) {
      card.appendChild(el("p", "hint", "Không có gợi ý — đây là nút kết thúc."));
    }
    body.push(card);
  });

  modal({
    title: "Chép sang tawk.to",
    body,
    actions: [
      { label: "Đóng", onClick: closeModal },
      {
        label: "📄 Chép tất cả",
        kind: "primary",
        onClick: async (e) => {
          const d = await api("/api/chatbot/export", { method: "POST" });
          chepVao(d.text, e.target);
        },
      },
    ],
  });
};
