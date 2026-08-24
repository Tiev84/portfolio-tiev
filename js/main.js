const button = document.querySelector(".menu-btn");
const nav = document.querySelector(".nav-links");
button?.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  button.setAttribute("aria-expanded", String(open));
});
document
  .querySelectorAll(".nav-links a")
  .forEach((a) =>
    a.addEventListener("click", () => nav.classList.remove("open")),
  );

const backToTop = document.getElementById("backToTop");

if (backToTop) {
  const toggleBackToTop = () => {
    const scrollPos =
      window.scrollY ||
      window.pageYOffset ||
      document.documentElement.scrollTop ||
      document.body.scrollTop ||
      0;
    backToTop.classList.toggle("show", scrollPos > 150);
  };

  window.addEventListener("scroll", toggleBackToTop, { passive: true });
  document.addEventListener("scroll", toggleBackToTop, { passive: true });

  backToTop.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });

  toggleBackToTop();
}

/* =========================
   PROJECT ASSET PREFETCH ON HOVER
========================= */
const prefetchedProjects = new Set();
document.querySelectorAll('a[href*="project-detail.html"]').forEach((link) => {
  const prefetchAssets = () => {
    try {
      const url = new URL(link.href, window.location.href);
      const projId = url.searchParams.get("project");
      if (!projId || prefetchedProjects.has(projId)) return;
      prefetchedProjects.add(projId);

      if (projId === "event-droppii") {
        const linkEl = document.createElement("link");
        linkEl.rel = "prefetch";
        linkEl.href = "assets/project/GALA/video.mp4";
        document.head.appendChild(linkEl);
      }
    } catch (e) {}
  };

  link.addEventListener("mouseenter", prefetchAssets, { once: true });
  link.addEventListener("touchstart", prefetchAssets, { once: true });
});
