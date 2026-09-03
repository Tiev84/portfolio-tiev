/* =========================================================
   Dữ liệu project nằm ở js/projects-data.js (do admin app tạo).
   Muốn thêm / bớt / đổi thứ tự ảnh: mở app quản lý (start.bat),
   chỉnh trong đó rồi bấm "Đăng lên web".
   ========================================================= */

const projects = window.PROJECTS || {};

/* =========================
   GET PROJECT FROM URL
========================= */

const params = new URLSearchParams(window.location.search);

const projectId = params.get("project");

const fallbackId = Object.keys(projects)[0];

const project = projects[projectId] ||
  projects[fallbackId] || { category: "", title: "", description: "", images: [] };

/* =========================
   INSERT CONTENT
========================= */

document.getElementById("project-category").textContent = project.category;

document.getElementById("project-title").textContent = project.title;

document.getElementById("project-description").textContent =
  project.description;
/* =========================
   CREATE GALLERY & LAZY OBSERVER
========================= */

const gallery = document.getElementById("project-gallery");

const lazyObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        if (el.dataset.src) {
          if (el.tagName === "VIDEO") {
            el.src = el.dataset.src;
            el.load();
          } else if (el.tagName === "IMG") {
            el.src = el.dataset.src;
          }
          delete el.dataset.src;
        }
        observer.unobserve(el);
      }
    });
  },
  { rootMargin: "300px 0px" },
);

project.images.forEach((src, index) => {
  const item = document.createElement("div");
  item.className = "gallery-item";

  const isVideo =
    src.match(/\.(mp4|webm|mov|ogg)($|\?)/i) ||
    src.includes("/releases/download/");

  if (isVideo) {
    item.classList.add("landscape");
    const video = document.createElement("video");

    // Thuộc tính bắt buộc cho trình duyệt mobile (iOS Safari & Android Chrome)
    video.setAttribute("controls", "controls");
    video.setAttribute("autoplay", "autoplay");
    video.setAttribute("muted", "muted");
    video.setAttribute("playsinline", "true");
    video.setAttribute("webkit-playsinline", "true");
    video.setAttribute("preload", "metadata");

    video.muted = true;
    video.defaultMuted = true;
    video.autoplay = true;
    video.loop = true;
    video.playsInline = true;

    // Dùng ảnh thumb làm poster
    if (
      project.images[0] &&
      !project.images[0].match(/\.(mp4|webm|mov|ogg)($|\?)/i) &&
      !project.images[0].includes("/releases/download/")
    ) {
      video.poster = project.images[0];
    }

    video.src = src;

    // Tự động phát khi cuộn tới trên mobile
    const videoObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      },
      { threshold: 0.15 },
    );
    videoObserver.observe(video);

    item.appendChild(video);
  } else {
    const img = document.createElement("img");

    img.alt = `${project.title} - ${index + 1}`;
    img.decoding = "async";

    // Đọc tỉ lệ thật của file ảnh
    img.addEventListener("load", () => {
      const ratio = img.naturalWidth / img.naturalHeight;

      if (ratio > 1.15) {
        item.classList.add("landscape");
      } else if (ratio < 0.85) {
        item.classList.add("portrait");
      } else {
        item.classList.add("square");
      }
    });

    if (index === 0) {
      img.loading = "eager";
      img.fetchPriority = "high";
      img.src = src;
    } else {
      img.dataset.src = src;
      lazyObserver.observe(img);
    }

    item.appendChild(img);
  }

  gallery.appendChild(item);
});
/* =========================
   MOBILE MENU
========================= */

const menuBtn = document.querySelector(".menu-btn");
const navLinks = document.querySelector(".nav-links");

if (menuBtn && navLinks) {
  menuBtn.addEventListener("click", () => {
    navLinks.classList.toggle("open");

    const isOpen = navLinks.classList.contains("open");

    menuBtn.setAttribute("aria-expanded", isOpen);
  });
}

const galleryImages = Array.from(
  document.querySelectorAll(".gallery-item img"),
);
const lightbox = document.getElementById("lightbox");

const lightboxImg = document.getElementById("lightbox-image");

const btnClose = document.querySelector(".lightbox-close");
const btnPrev = document.querySelector(".lightbox-prev");
const btnNext = document.querySelector(".lightbox-next");

let current = 0;

galleryImages.forEach((img, index) => {
  img.style.cursor = "zoom-in";

  img.addEventListener("click", () => {
    current = index;

    showImage();

    lightbox.classList.add("open");
  });
});

function showImage() {
  const targetImg = galleryImages[current];
  if (targetImg) {
    const src = targetImg.dataset.src || targetImg.src;
    if (!targetImg.src && targetImg.dataset.src) {
      targetImg.src = targetImg.dataset.src;
    }
    lightboxImg.src = src;
    lightboxImg.alt = targetImg.alt;
  }
}

btnClose.onclick = () => {
  lightbox.classList.remove("open");
};

lightbox.onclick = (e) => {
  if (e.target === lightbox) {
    lightbox.classList.remove("open");
  }
};

btnPrev.onclick = (e) => {
  e.stopPropagation();

  current = (current - 1 + galleryImages.length) % galleryImages.length;

  showImage();
};

btnNext.onclick = (e) => {
  e.stopPropagation();

  current = (current + 1) % galleryImages.length;

  showImage();
};

document.addEventListener("keydown", (e) => {
  if (!lightbox.classList.contains("open")) return;

  if (e.key === "Escape") lightbox.classList.remove("open");

  if (e.key === "ArrowLeft") {
    current = (current - 1 + galleryImages.length) % galleryImages.length;

    showImage();
  }

  if (e.key === "ArrowRight") {
    current = (current + 1) % galleryImages.length;

    showImage();
  }
});
