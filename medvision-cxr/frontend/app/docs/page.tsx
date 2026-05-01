import type { Route } from "next";
import Link from "next/link";
import { BookOpenText, FileCode2, Orbit } from "lucide-react";


type DocsLink =
  | {
      href: Route;
      title: string;
      description: string;
      kind: "route";
    }
  | {
      href: string;
      title: string;
      description: string;
      kind: "file";
    };


const docsLinks: DocsLink[] = [
  {
    href: "/docs/swagger" as Route,
    title: "Swagger UI",
    description: "适合接口联调、参数查看与响应结构核对。",
    kind: "route"
  },
  {
    href: "/docs/redoc" as Route,
    title: "Redoc",
    description: "适合面向评审、合作方和文档站展示的长文档阅读。",
    kind: "route"
  },
  {
    href: "/openapi/medvision-cxr-openapi.yaml",
    title: "OpenAPI YAML",
    description: "由后端脚本自动生成并同步到前端静态资源，避免文档漂移。",
    kind: "file"
  }
];


export default function DocsHomePage() {
  return (
    <section className="container-page space-y-8">
      <div className="max-w-3xl space-y-4">
        <div className="chip">API Documentation</div>
        <h1 className="headline">可直接访问的 Swagger UI / Redoc 文档站</h1>
        <p className="subheadline">
          当前页面直接消费同步后的 OpenAPI YAML，既能服务前端联调，也能作为比赛演示和治理审查时的文档入口。
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {docsLinks.map((item, index) => {
          const Icon = index === 0 ? BookOpenText : index === 1 ? Orbit : FileCode2;
          const content = (
            <>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <h2 className="font-display text-xl font-semibold text-text">{item.title}</h2>
              <p className="mt-3 text-sm leading-7 text-textMuted">{item.description}</p>
            </>
          );

          if (item.kind === "file") {
            return (
              <a
                key={item.href}
                href={item.href}
                className="card-medical glass-panel group p-6 transition hover:-translate-y-1 hover:shadow-lg"
              >
                {content}
              </a>
            );
          }

          return (
            <Link key={item.href} href={item.href} className="card-medical glass-panel group p-6 transition hover:-translate-y-1 hover:shadow-lg">
              {content}
            </Link>
          );
        })}
      </div>
    </section>
  );
}