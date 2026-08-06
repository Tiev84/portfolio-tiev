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
    backToTop.classList.toggle("show", window.scrollY > 400);
  };

  window.addEventListener("scroll", toggleBackToTop);

  backToTop.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });

  toggleBackToTop();
}
