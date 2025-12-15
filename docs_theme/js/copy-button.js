document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("pre > code").forEach(function (codeBlock) {
    const button = document.createElement("button");
    button.className = "copy-block-button btn btn-inverse btn-mini";
    button.type = "button";
    button.textContent = "Copy";

    button.addEventListener("click", function () {
      navigator.clipboard.writeText(codeBlock.textContent)
        .then(() => {
          button.textContent = "Copied!";
          setTimeout(() => button.textContent = "Copy", 1200);
        })
        .catch(() => {
          button.textContent = "Failed";
          setTimeout(() => button.textContent = "Copy", 1200);
        });
    });

    const pre = codeBlock.parentNode;
    pre.style.position = "relative";
    pre.appendChild(button);
  });
});
