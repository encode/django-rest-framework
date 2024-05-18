import "../../node_modules/bootstrap/js/dist/alert";
import "../../node_modules/bootstrap/js/dist/button";
import "../../node_modules/bootstrap/js/dist/carousel";
import "../../node_modules/bootstrap/js/dist/collapse";
import "../../node_modules/bootstrap/js/dist/dropdown";
import "../../node_modules/bootstrap/js/dist//modal";
import "../../node_modules/bootstrap/js/dist/offcanvas";
import "../../node_modules/bootstrap/js/dist/popover";
import "../../node_modules/bootstrap/js/dist/scrollspy";
import "../../node_modules/bootstrap/js/dist/tab";
import "../../node_modules/bootstrap/js/dist/toast";
import "../../node_modules/bootstrap/js/dist/tooltip";

import "../scss/styles.scss";

function setupPrettify() {
  const codeBlocks = document.querySelectorAll("pre code");
  codeBlocks.forEach((block) => {
    block.parentElement.classList.add("prettyprint", "well");
  });
}

setupPrettify();
