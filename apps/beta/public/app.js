// If this runs at all, the stylesheet and script were served with the right
// content types - which means the prefix rewrite at the edge is correct.
document.getElementById("asset-check").textContent =
  "assets loaded correctly from " + document.baseURI;
