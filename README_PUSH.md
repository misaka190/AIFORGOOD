README — 离线推送到 GitHub（使用 bundle / zip）
=============================================

概述
---
本文件说明如何在一台可以访问 GitHub 的机器上，使用仓库根目录下生成的 `AIFORGOOD_import_724b5ba.bundle`（推荐）或 `AIFORGOOD_repo_724b5ba.zip` 将清理后的提交推送到远端仓库 `misaka190/AIFORGOOD`。

前提
---
- 你已把 `AIFORGOOD_import_724b5ba.bundle` 或 `AIFORGOOD_repo_724b5ba.zip` 复制到目标机器。
- 目标机器上安装了 `git`（支持 2.14+）。
- 推荐使用 SSH 认证（目标机器已配置可推送到 GitHub 的 SSH key）；也可使用 HTTPS + PAT。

推荐流程（使用 bundle，Windows PowerShell 示例）
---
1) 将 `AIFORGOOD_import_724b5ba.bundle` 复制到目标机器（例如 `C:\temp`）。

2) 在目标机器克隆 bundle：

```powershell
cd C:\temp
git clone .\AIFORGOOD_import_724b5ba.bundle AIFORGOOD_repo
cd AIFORGOOD_repo
```

3) 添加远程并推送到导入分支（不覆盖 `main`）：

```powershell
# 推荐：SSH（目标机器已配置可用的 SSH key）
git remote add origin git@github.com:misaka190/AIFORGOOD.git
git push -u origin HEAD:import-local-724b5ba

# 或使用 HTTPS（需 PAT）：
# git remote add origin https://github.com/misaka190/AIFORGOOD.git
# git push -u origin HEAD:import-local-724b5ba
```

4) 在 GitHub 页面确认新分支：

打开 https://github.com/misaka190/AIFORGOOD/branches 并检查 `import-local-724b5ba` 分支是否存在。

可选：如果确实需要把本次提交直接覆盖 `main`（非常谨慎，可能影响历史），在确认无误后可以强推：

```powershell
git push -u origin HEAD:main --force
```

使用 zip（含 bundle）
---
如果你使用 `AIFORGOOD_repo_724b5ba.zip`：先解压并定位到解压目录；如果 zip 中包含 `.bundle`，优先使用 bundle 方法；若只有源码且没有 `.git`，不推荐直接初始化新的仓库并推送（将丢失历史）。

Linux / macOS 示例（scp + clone）：

```bash
# 将 bundle 传到服务器
scp AIFORGOOD_import_724b5ba.bundle user@host:/tmp/
ssh user@host
cd /tmp
git clone AIFORGOOD_import_724b5ba.bundle AIFORGOOD_repo
cd AIFORGOOD_repo
git remote add origin git@github.com:misaka190/AIFORGOOD.git
git push -u origin HEAD:import-local-724b5ba
```

验证与常用命令
---
- 查看当前提交 Short SHA（本地）：

```powershell
git rev-parse --short HEAD
```

- 列出远端 refs：

```powershell
git ls-remote origin
```

故障排查
---
- 推送被拒绝并提示“大文件超过 100MB”：说明历史中仍包含大文件。请把错误粘贴给我，我可以协助使用 `git filter-repo` 或 BFG 清理历史，或改用 Git LFS（需在远端启用 LFS）。
- SSH 权限错误 `Permission denied (publickey)`：请确保目标机器的 SSH key 已添加到对应 GitHub 账户或仓库的 Deploy keys（写权限）。可用 `ssh -T git@github.com` 验证连接。
- HTTPS 推送出现 401/403：确认 PAT 权限包含 repo 权限并用 `git remote set-url origin https://<TOKEN>@github.com/owner/repo.git`（注意凭据安全）。

额外说明
---
- 本仓库根已包含生成的 bundle 与 zip：`AIFORGOOD_import_724b5ba.bundle` 与 `AIFORGOOD_repo_724b5ba.zip`。
- 我已把此说明写入仓库以便在目标机器上复现。如果你需要我替你在一台可以访问 GitHub 的远程机器/容器上完成推送，请授权或提供可用方式（SSH key 或短期 PAT），我可以代为执行。

联系方式
---
如遇到任何错误，复制终端输出并粘贴给我（或把 pre-receive hook 的完整错误信息给我），我会继续协助清理或解决权限问题。

EOF