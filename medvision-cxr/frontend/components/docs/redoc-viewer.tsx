"use client";

import { useEffect, useId } from "react";


declare global {
  interface Window {
    Redoc?: {
      init: (specOrSpecUrl: string, options: Record<string, unknown>, element: HTMLElement) => void;
    };
  }
}


const REDOC_SCRIPT_ID = "medvision-redoc-script";


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


export function RedocViewer() {
  const containerId = useId().replace(/:/g, "");

  useEffect(() => {
    let cancelled = false;

    async function loadRedoc() {
      await ensureScript(REDOC_SCRIPT_ID, "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js");
      if (cancelled || !window.Redoc) {
        return;
      }

      const element = document.getElementById(containerId);
      if (!element) {
        return;
      }

      window.Redoc.init(
        "/openapi/medvision-cxr-openapi.yaml",
        {
          hideDownloadButton: false,
          pathInMiddlePanel: true,
          expandResponses: "200,201",
          theme: {
            colors: {
              primary: { main: "#0d5c63" },
              success: { main: "#2d8f61" },
              warning: { main: "#b67d26" },
              error: { main: "#c95d4a" }
            },
            typography: {
              fontFamily: "'IBM Plex Sans', sans-serif",
              headings: {
                fontFamily: "'Space Grotesk', sans-serif"
              }
            }
          }
        },
        element
      );
    }

    loadRedoc().catch((error) => {
      const element = document.getElementById(containerId);
      if (element) {
        element.innerHTML = `<div style="padding:24px;color:#c95d4a;font-weight:600;">${String(error)}</div>`;
      }
    });

    return () => {
      cancelled = true;
    };
  }, [containerId]);

  return <div id={containerId} className="min-h-[70vh] overflow-hidden rounded-2xl border border-border bg-white" />;
}