import { Search } from "lucide-react";

import { StatePanel } from "@/components/ui/state-panel";
import { PageHeader } from "@/components/ui/page-header";
import { RiskLevelPill } from "@/components/ui/risk-level-pill";
import { frontendApi } from "@/lib/api";

export default async function HistoryPage() {
  const history = await frontendApi.fetchHistory();

  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="历史记录页面"
        title="历史分析记录"
        description="支持按上传时间、风险等级、医生复核状态进行浏览、搜索和筛选。删除操作应在后端保留审计记录。"
      />

      <section className="card-medical p-6 sm:p-8">
        <div className="grid gap-4 lg:grid-cols-[1fr_180px_180px]">
          <label className="relative block">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-textMuted" />
            <input placeholder="搜索匿名文件名或记录编号" className="w-full rounded-full border border-border bg-surface px-11 py-3 text-sm outline-none transition focus:border-primary" />
          </label>
          <select className="rounded-full border border-border bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary">
            <option>全部风险等级</option>
            <option>低风险</option>
            <option>中风险</option>
            <option>高风险</option>
            <option>需优先复核</option>
          </select>
          <select className="rounded-full border border-border bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary">
            <option>全部复核状态</option>
            <option>已医生复核</option>
            <option>待医生复核</option>
          </select>
        </div>

        {history.length === 0 ? (
          <div className="mt-6">
            <StatePanel title="暂无历史记录" description="当用户上传胸片并完成辅助分析后，记录会显示在此处。" actionLabel="去上传页面" actionHref="/upload" />
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-y-3">
              <thead>
                <tr className="text-left text-sm text-textMuted">
                  <th className="px-4 py-2 font-medium">上传时间</th>
                  <th className="px-4 py-2 font-medium">匿名文件名</th>
                  <th className="px-4 py-2 font-medium">风险等级</th>
                  <th className="px-4 py-2 font-medium">医生复核</th>
                  <th className="px-4 py-2 font-medium">不确定性</th>
                  <th className="px-4 py-2 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id} className="rounded-2xl bg-surface text-sm text-text shadow-soft">
                    <td className="rounded-l-2xl px-4 py-4">{item.uploaded_at}</td>
                    <td className="px-4 py-4">{item.image_name}</td>
                    <td className="px-4 py-4"><RiskLevelPill level={item.overall_risk_level} /></td>
                    <td className="px-4 py-4">{item.doctor_reviewed ? "已复核" : "待复核"}</td>
                    <td className="px-4 py-4">{item.uncertainty_flag ? "存在不确定性" : "未见明显不确定性"}</td>
                    <td className="rounded-r-2xl px-4 py-4">
                      <div className="flex gap-3">
                        <button className="text-primary transition hover:opacity-80">查看</button>
                        <button className="text-danger transition hover:opacity-80">删除记录</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
