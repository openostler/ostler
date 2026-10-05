import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";
// Composition root: each vehicle pack registers its Drive views (vehicles/registry.ts).
import "./vehicles/lr_d2";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
