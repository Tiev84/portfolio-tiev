const projects = {
  "event-droppii": {
    category: "SOCIAL MEDIA | EVENT | POSM | UI - UX DESIGN",
    title: "Event Đại hội năm 2026 Droppii",

    description:
      "Trong khuôn khổ Đại hội năm Droppii 2026, Tiến trực tiếp đảm nhiệm việc thực thi toàn bộ giải pháp hình ảnh cho sự kiện, từ các thiết kế Social Post truyền thông trước, trong và sau chương trình, hệ thống POSM in ấn đồng bộ (standee, backdrop, photobooth, thẻ đeo...) cho đến các ấn phẩm in ấn cỡ lớn và hiệu ứng màn hình LED trình chiếu trên sân khấu. Sự tỉ mỉ và đồng bộ trong từng nét vẽ đã góp phần tạo nên một không gian sự kiện chỉn chu, chuyên nghiệp và đầy cảm xúc.",

    images: [
      "assets/project/GALA/thumb dhn.jpg",
      "assets/project/GALA/video.mp4",
      "assets/project/GALA/3.jpg",
      "assets/project/GALA/4.jpg",
      "assets/project/GALA/5.jpg",
      "assets/project/GALA/6.png",
      "assets/project/GALA/7.png",
      "assets/project/GALA/8.png",
      "assets/project/GALA/9.png",
      "assets/project/GALA/10.png",
      "assets/project/GALA/11.png",
      "assets/project/GALA/12.png",
      "assets/project/GALA/13.png",
      "assets/project/GALA/14.jpg",
      "assets/project/GALA/15.jpg",
      "assets/project/GALA/16.png",
      "assets/project/GALA/17.png",
      "assets/project/GALA/18.jpg",
      "assets/project/GALA/19.png",
      "assets/project/GALA/20.jpg",
      "assets/project/GALA/21.jpg",
      "assets/project/GALA/22.jpg",
      "assets/project/GALA/23.jpg",
      "assets/project/GALA/24.jpg",
    ],
  },

  "digital-advertising-droppii": {
    category: "SOCIAL MEDIA | UI - UX DESIGN",

    title: "Digital advertising Droppii",

    description:
      "Các thiết kế Digital Advertising được phát triển nhằm đảm bảo tính đồng nhất thương hiệu, khả năng truyền tải thông tin nhanh và hiệu quả trên các nền tảng số.",

    images: [
      "assets/project/thumb ads (1).png",
      "assets/project/153 OPT2.png",
      "assets/project/180.png",
      "assets/project/ADS 5.png",
      "assets/project/2.png",
      "assets/project/5.png",
      "assets/project/ADS 4.png",
      "assets/project/ADS PT TEXT 2.png",
      "assets/project/181.png",
      "assets/project/ADS 6.png",
      "assets/project/LP ADS.png",
      "assets/project/Landingpage droppii mall sua.png",
      "assets/project/LP AI (1).png",
    ],
  },

  "expo-hang-moi-droppii": {
    category: "SOCIAL MEDIA | POSM",

    title: "Expo hàng mới lên kệ Droppii",

    description:
      "Hệ thống thiết kế truyền thông và POSM phục vụ hoạt động giới thiệu các sản phẩm mới trên nền tảng Droppii.",

    images: [
      "assets/projects/expo-hang-moi/01.jpg",
      "assets/projects/expo-hang-moi/02.jpg",
      "assets/projects/expo-hang-moi/03.jpg",
      "assets/projects/expo-hang-moi/04.jpg",
      "assets/projects/expo-hang-moi/05.jpg",
      "assets/projects/expo-hang-moi/06.jpg",
      "assets/projects/expo-hang-moi/07.jpg",
      "assets/projects/expo-hang-moi/08.jpg",
      "assets/projects/expo-hang-moi/09.jpg",
    ],
  },

  "expo-health": {
    category: "SOCIAL MEDIA | POSM",

    title: "Expo sức khỏe Droppii",

    description: "Meta meta meta",

    images: [
      "assets/project/thumb expo (1).png",
      "assets/project/DIEM HEN SUC KHOE TEASER 2.png",
      "assets/project/bia km.png",
      "assets/project/TRAI NGHIEM GI.png",
      "assets/project/backdrop.png",
      "assets/project/standee.png",
      "assets/project/pic.png",
    ],
  },

  "sale-event": {
    category: "SOCIAL MEDIA | UI - UX DESIGN",

    title: "Sale event Droppii",

    description: "Meta meta meta",

    images: [
      "assets/project/thumb 283 (1).png",
      "assets/project/teaser.png",
      "assets/project/full rule 28 vuong.png",
      "assets/project/full rule 28 vuong 2.png",
      "assets/project/bia km (1).png",
      "assets/project/LP.png",
    ],
  },

  "bingto-vlog": {
    category: "Social Media",

    title: "Bingto Vlog - Điền Quân Network",

    description: "Meta meta meta",

    images: [
      "assets/project/ĐIỀN QUÂN NETWORK/cbcbec8a-38d6-4b37-9fd6-b3ad05e4fda9.jpg",
      "assets/project/ĐIỀN QUÂN NETWORK/bingto vlog poster.png",
    ],
  },
};

/* =========================
   GET PROJECT FROM URL
========================= */

const params = new URLSearchParams(window.location.search);

const projectId = params.get("project");

const project = projects[projectId] || projects["event-droppii"];

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

  const isVideo = src.match(/\.(mp4|webm|mov|ogg)$/i);

  if (isVideo) {
    item.classList.add("landscape");
    const video = document.createElement("video");
    video.controls = true;
    video.autoplay = true;
    video.muted = true;
    video.loop = true;
    video.playsInline = true;

    // Dùng ảnh thumb làm poster để hiển thị tức thì
    if (
      project.images[0] &&
      !project.images[0].match(/\.(mp4|webm|mov|ogg)$/i)
    ) {
      video.poster = project.images[0];
    }

    video.dataset.src = src;
    lazyObserver.observe(video);
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
