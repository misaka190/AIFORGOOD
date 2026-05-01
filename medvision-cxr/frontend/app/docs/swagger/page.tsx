import Link from "next/link";

import { SwaggerViewer } from "@/components/docs/swagger-viewer";


export default function SwaggerDocsPage() {
  return (
    <section className="container-page space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-3">
          <div className="chip">Swagger UI</div>
          <h1 className="headline">MedVision-CXR API Swagger UI</h1>
          <p className="subheadline">
            当前页面直接读取同步后的 OpenAPI YAML，适合联调上传、结果、删除审批、audit log 与模型接口。
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm font-medium text-textMuted">
          <Link href="/docs/redoc" className="rounded-full border border-border px-4 py-2 hover:bg-surfaceMuted hover:text-text">
            切换到 Redoc
          </Link>
          <a href="/openapi/medvision-cxr-openapi.yaml" className="rounded-full border border-border px-4 py-2 hover:bg-surfaceMuted hover:text-text">
            查看原始 YAML
          </a>
        </div>
      </div>

      <div className="card-medical glass-panel overflow-hidden p-3 sm:p-4">
        <SwaggerViewer />
      </div>
    </section>
  );
}