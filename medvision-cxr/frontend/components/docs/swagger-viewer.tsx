"use client";

import { useEffect, useId } from "react";


declare global {
  interface Window {
    SwaggerUIBundle?: (config: Record<string, unknown>) => void;
  }
}


const SWAGGER_CSS_ID = "medvision-swagger-css";
const SWAGGER_BUNDLE_ID = "medvision-swagger-bundle";


function ensureStylesheet() {
  let link = document.getElementById(SWAGGER_CSS_ID) as HTMLLinkElement | null;
  if (!link) {
    link = document.createElement("link");
    link.id = SWAGGER_CSS_ID;
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css";
    document.head.appendChild(link);
  }
}


function ensureScript(id: string, src: string): Promise<void> {
  const existing = document.getElementById(id) as HTMLScriptElement | null;
  if (existing?.dataset.loaded === "true") {
    return Promise.resolve();
  }

  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = id;
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(script);
  });
}


export function SwaggerViewer() {
  const containerId = useId().replace(/:/g, "");

  useEffect(() => {
    let cancelled = false;

    async function loadSwagger() {
      ensureStylesheet();
      await ensureScript(SWAGGER_BUNDLE_ID, "https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js");
      if (cancelled || !window.SwaggerUIBundle) {
        return;
      }

      window.SwaggerUIBundle({
        dom_id: `#${containerId}`,
        url: "/openapi/medvision-cxr-openapi.yaml",
        deepLinking: true,
        displayRequestDuration: true,
        tryItOutEnabled: false,
        defaultModelsExpandDepth: 1,
        docExpansion: "list"
      });
    }

    loadSwagger().catch((error) => {
      const element = document.getElementById(containerId);
      if (element) {
        element.innerHTML = `<div style="padding:24px;color:#c95d4a;font-weight:600;">${String(error)}</div>`;
      }
    });

    return () => {
      cancelled = true;
    };
  }, [containerId]);

  return <div id={containerId} className="min-h-[70vh] rounded-2xl bg-white" />;
}