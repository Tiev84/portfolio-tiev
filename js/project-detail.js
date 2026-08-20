const projects = {
  "event-droppii": {
    category: "SOCIAL MEDIA | EVENT | POSM | UI - UX DESIGN",
    title: "Event Đại hội năm 2026 Droppii",

    description:
      "Trong khuôn khổ Đại hội năm Droppii 2026, Tiến trực tiếp đảm nhiệm việc thực thi toàn bộ giải pháp hình ảnh cho sự kiện, từ các thiết kế Social Post truyền thông trước, trong và sau chương trình, hệ thống POSM in ấn đồng bộ (standee, backdrop, photobooth, thẻ đeo...) cho đến các ấn phẩm in ấn cỡ lớn và hiệu ứng màn hình LED trình chiếu trên sân khấu. Sự tỉ mỉ và đồng bộ trong từng nét vẽ đã góp phần tạo nên một không gian sự kiện chỉn chu, chuyên nghiệp và đầy cảm xúc.",

    images: [
      "assets/projects/event-droppii/01.jpg",
      "assets/projects/event-droppii/02.jpg",
      "assets/projects/event-droppii/03.jpg",
      "assets/projects/event-droppii/04.jpg",
      "assets/projects/event-droppii/05.jpg",
      "assets/projects/event-droppii/06.jpg",
      "assets/projects/event-droppii/07.jpg",
      "assets/projects/event-droppii/08.jpg",
      "assets/projects/event-droppii/09.jpg",
    ],
  },

  "digital-advertising-droppii": {
    category: "SOCIAL MEDIA | UI - UX DESIGN",

    title: "Digital advertising Droppii",

    description:
      "Các thiết kế Digital Advertising được phát triển nhằm đảm bảo tính đồng nhất thương hiệu, khả năng truyền tải thông tin nhanh và hiệu quả trên các nền tảng số.",

    images: [
      "assets/project/thumb ads.png",
      "assets/project/153 OPT2.png",
      "assets/project/180.png",
      "assets/projects/digital-advertising/04.jpg",
      "assets/projects/digital-advertising/05.jpg",
      "assets/projects/digital-advertising/06.jpg",
      "assets/projects/digital-advertising/07.jpg",
      "assets/projects/digital-advertising/08.jpg",
      "assets/projects/digital-advertising/09.jpg",
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
      "assets/project/thumb expo.png",
      "assets/project/DIEM HEN SUC KHOE TEASER 2.png",
      "assets/project/bia km.png",
      "assets/project/TRAI NGHIEM GI.png",
      "assets/project/backdrop.png",
      "assets/project/standee.png",
      "assets/project/pic.png",
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
   INSERT IMAGES
========================= */
// const galleryItems = document.querySelectorAll(".gallery-item");

// const loadedImages = [];

// project.images.forEach((image, index) => {
//   const item = galleryItems[index];
//   const imageElement = document.getElementById(`project-image-${index + 1}`);

//   if (!imageElement || !item) return;

//   imageElement.src = image;
//   imageElement.alt = `${project.title} - ${index + 1}`;

//   loadedImages.push(
//     new Promise((resolve) => {
//       imageElement.onload = () => resolve(imageElement);
//     }),
//   );
// });

// /* Ẩn các slot dư */
// galleryItems.forEach((item, index) => {
//   if (!project.images[index]) {
//     item.style.display = "none";
//   }
// });
const galleryItems = document.querySelectorAll(".gallery-item");

const loadedImages = [];

project.images.forEach((image, index) => {
  const item = galleryItems[index];
  const imageElement = document.getElementById(`project-image-${index + 1}`);

  if (!imageElement || !item) return;

  imageElement.alt = `${project.title} - ${index + 1}`;

  const loadPromise = new Promise((resolve) => {
    const done = () => resolve(imageElement);

    // GẮN onload TRƯỚC khi set src
    imageElement.addEventListener("load", done, {
      once: true,
    });

    imageElement.src = image;

    // Nếu ảnh đã có trong cache
    if (imageElement.complete && imageElement.naturalWidth > 0) {
      resolve(imageElement);
    }
  });

  loadedImages.push(loadPromise);
});

/* Ẩn slot không có ảnh */
galleryItems.forEach((item, index) => {
  if (!project.images[index]) {
    item.style.display = "none";
  } else {
    item.style.display = "";
  }
});

/* Scale ảnh theo kích thước gốc */
Promise.all(loadedImages).then((images) => {
  const gallery = document.querySelector(".project-gallery");

  const maxNaturalWidth = Math.max(...images.map((img) => img.naturalWidth));

  const containerWidth = gallery.clientWidth;

  images.forEach((img) => {
    const ratio = img.naturalWidth / maxNaturalWidth;
    const scale = Math.max(ratio, 0.9);

    const displayWidth = containerWidth * scale;

    img.style.width = `${displayWidth}px`;
    img.style.height = "auto";
  });
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

const galleryImages = document.querySelectorAll(".gallery-item img");

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
  lightboxImg.src = galleryImages[current].src;

  lightboxImg.alt = galleryImages[current].alt;
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
