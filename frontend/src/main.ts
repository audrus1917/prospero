import { createApp } from "vue";

import App from "./App.vue";
import "./styles.css";

// Create one Vue application and attach it to the root element declared in
// index.html. Global styles are imported here so every view shares them.
createApp(App).mount("#app");
