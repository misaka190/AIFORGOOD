import Link from "next/link";

import { RedocViewer } from "@/components/docs/redoc-viewer";


export default function RedocDocsPage() {
  return (
    <section className="container-page space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-3">
          <div className="chip">Redoc</div>
          <h1 className="headline">MedVision-CXR API Redoc</h1>
          <p className="subheadline">
            适合长篇阅读和评审展示，当前页面同样直接消费脚本同步后的 OpenAPI YAML。
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm font-medium text-textMuted">
          <Link href="/docs/swagger" className="rounded-full border border-border px-4 py-2 hover:bg-surfaceMuted hover:text-text">
            切换到 Swagger UI
          </Link>
          <a href="/openapi/medvision-cxr-openapi.yaml" className="rounded-full border border-border px-4 py-2 hover:bg-surfaceMuted hover:text-text">
            查看原始 YAML
          </a>
        </div>
      </div>

      <div className="card-medical glass-panel overflow-hidden p-3 sm:p-4">
        <RedocViewer />
      </div>
    </section>
  );
}