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
      "assets/projects/digital-advertising/01.jpg",
      "assets/projects/digital-advertising/02.jpg",
      "assets/projects/digital-advertising/03.jpg",
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

project.images.forEach((image, index) => {
  const imageElement = document.getElementById(`project-image-${index + 1}`);

  if (imageElement) {
    imageElement.src = image;
    imageElement.alt = `${project.title} - ${index + 1}`;
  }
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
