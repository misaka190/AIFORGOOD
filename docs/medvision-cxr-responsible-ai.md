# MedVision-CXR Responsible AI 与隐私保护方案

## 一、伦理原则

### 1. AI 仅作辅助分诊

MedVision-CXR 的设计目标是帮助医疗团队进行胸部 X 光的辅助分诊、辅助筛查和医生复核优先级排序，而不是提供自动化临床结论。系统输出应被理解为风险提示与复核建议，不应被当作独立结论使用。

### 2. 不替代医生

系统不替代影像科医生、临床医生或其他具备资质的医疗专业人员。任何高风险、复杂、不确定或与临床表现不一致的结果，都必须进入人工复核流程。

### 3. 不输出确定性诊断

系统输出必须使用 `risk_assessment`、`triage_result`、`ai_assisted_findings` 等风险导向术语，不使用 `diagnosis`、`confirmed`、`definitive`、`确诊` 等确定性表述。

### 4. 不提供治疗建议

系统不得输出药物、手术、处置路径或其他治疗建议。系统只可提示“建议医生复核”“建议优先复核”“建议结合临床信息进一步判断”等非处置性文本。

### 5. 人类医生最终决策

任何临床决策都必须由具备资质的医生结合患者病史、体征、实验室检查、影像表现和医疗环境综合判断。系统只能提供辅助排序与解释支持。

### 6. 透明可解释

平台应向用户清晰说明：

- 模型的用途是辅助分诊而非诊断
- 输出包含局限性与不确定性
- 热力图仅用于可解释性展示
- 模型版本、主要标签、风险等级和复核建议可被追踪

### 7. 公平性

系统应持续评估不同性别、年龄、设备来源、医院来源、图像质量和疾病标签上的性能差异，避免只优化总体指标而忽略亚群体风险。

### 8. 隐私保护

系统遵循最小必要原则，不强制收集真实姓名、身份证号、手机号等直接身份标识符。上传文件默认匿名化命名，图像元数据在进入分析流程前做必要清洗和去标识化处理。

### 9. 安全性

系统必须具备传输加密、存储保护、访问控制、审计记录、删除机制和异常操作监控能力，以降低未授权访问、数据泄露、滥用和错误配置风险。

### 10. 问责机制

系统需要支持责任追踪，包括：

- 模型版本追踪
- 上传、查看、复核、删除的审计日志
- 错误案例复盘
- 风险事件上报与修复流程
- 数据删除请求与审批留痕

## 二、上传前知情同意文案

在上传胸部 X 光图像前，请用户勾选并确认以下声明：

> **MedVision-CXR 上传前知情同意**
>
> 我已知晓并理解：
>
> 1. 本系统提供的 AI 分析结果不是医学诊断，也不能替代医生判断。
> 2. 本系统仅用于胸部 X 光的辅助分诊、辅助筛查和医生复核支持。
> 3. 由于模型能力、图像质量、设备差异、数据偏差或外部环境影响，系统结果可能出现错误、遗漏或偏差。
> 4. 当系统提示高风险或存在不确定性时，我应当及时咨询具备资质的医生，并结合临床信息进一步判断。
> 5. 我同意系统在本次分析和合规审计所必需的范围内处理我上传的图像数据。
> 6. 我知晓自己可以依据平台规则请求删除相关数据或发起删除审批流程。
>
> 勾选确认即表示我理解上述内容，并同意在本次辅助分析中按上述方式处理我上传的图像。

## 三、结果页免责声明

### 中文版

> **医疗免责声明**
>
> 本页面展示的 AI 辅助结果不是医学诊断，不应作为临床决策的唯一依据。若需做出诊疗、转诊或其他临床决策，请咨询具备资质的医疗专业人员。Grad-CAM 热力图仅用于帮助理解模型关注区域，不代表病灶定位结论。本系统可能因数据分布、图像质量、设备差异和模型局限性而存在误差、偏差或泛化不足。

### English Version

> **Medical Disclaimer**
>
> The AI-assisted result shown on this page is not a medical diagnosis and must not be used as the sole basis for clinical decision-making. For any clinical decision, please consult a qualified healthcare professional. Heatmaps are provided for interpretability only and do not represent definitive lesion localization. This system may have limitations, errors, and biases due to data distribution, image quality, device differences, and model generalization constraints.

## 四、数据保护方案

### 1. 文件名 UUID 化

- 上传后的原始文件名不直接用于存储。
- 后端使用随机 UUID 或匿名化文件名进行命名，降低从文件名反推身份的风险。

### 2. 删除 EXIF

- 对 PNG、JPG、JPEG 等图像文件移除 EXIF 信息。
- 避免泄露拍摄时间、设备信息、地理位置、作者信息等元数据。

### 3. DICOM 去标识化

- 对 DICOM 文件执行必要的去标识化流程。
- 删除或脱敏患者姓名、病历号、检查号、机构标识等直接或间接身份字段。

### 4. 数据最小化

- 仅处理完成本次分析和必要审计所需的最小数据集。
- 默认不要求用户输入真实身份信息。
- 仅保留最小必要的角色、时间、对象和动作记录。

### 5. 默认不长期保存原图

- 默认策略应优先采用短期缓存或按需保留。
- 原图长期保留必须有明确业务或合规依据。
- 非必要场景应优先保存匿名化分析结果摘要，而非原图长期副本。

### 6. 加密存储

- 对数据库、对象存储、备份和日志介质使用静态加密。
- 高敏感环境建议使用 KMS 或 HSM 管理密钥。
- 密钥与业务配置分离管理，禁止硬编码在仓库中。

### 7. HTTPS

- 所有用户访问与系统间调用默认使用 HTTPS/TLS。
- 禁止在生产环境下通过明文 HTTP 传输图像和访问令牌。

### 8. JWT 权限控制

- 所有受保护接口通过 JWT 做身份认证。
- 令牌设置合理过期时间，并限制泄露后的可利用窗口。

### 9. RBAC 角色权限

- `clinician` 仅可上传、查看自身历史、请求分析和发起删除请求。
- `doctor` 可执行复核、查看复核详情和删除审批决策。
- `admin` 具备审计和系统治理能力。

### 10. 审计日志

- 记录上传、分析、查看结果、生成热力图、提交复核、提交删除请求、审批删除、直接删除等动作。
- 审计日志至少保留行为类型、资源类型、时间、操作者、请求 ID 和必要上下文。

### 11. 数据删除机制

- 支持软删除和硬删除。
- 默认优先采用带审批的 governed deletion workflow。
- 删除理由、审批备注、拒绝原因和完成时间应保留合规留痕。

## 五、模型风险控制

### 1. 阈值策略

- 各标签使用独立阈值，而非单一全局阈值。
- 阈值应通过验证集校准，而不是凭经验设定。

### 2. 低置信度标记为不确定

- 当 `confidence_score` 低于设定阈值，或模型集成差异较大时，设置 `uncertainty_flag = true`。

### 3. 高风险自动进入医生复核

- `overall_risk_level` 达到 `high` 或 `critical` 时，自动进入医生复核队列。

### 4. 不确定结果进入医生复核

- 即使总体风险不高，只要 `uncertainty_flag = true`，也必须进入人工复核。

### 5. 模型版本追踪

- 每条预测结果都绑定 `model_version`。
- 前端与 API 必须展示当前结果使用的模型版本。

### 6. 错误案例复盘

- 建立假阳性、假阴性、高不确定性和高争议案例清单。
- 与医生一起复盘错误来源，包括数据质量、标签噪声、域偏移和流程问题。

### 7. 外部验证

- 在外部医院或外部数据分布上进行独立验证。
- 不将单中心结果误当作普适性能。

### 8. 定期再评估

- 模型上线后定期回顾性能、错误案例和公平性指标。
- 数据源、设备分布或临床流程变化后应重新评估。

## 六、公平性评估方案

### 1. 不同性别

- 分别统计男性、女性及可获得的其他性别标记子集上的 AUC、灵敏度、特异度、PPV、NPV、校准误差。
- 重点关注高风险标签上的漏报差异。

### 2. 不同年龄

- 按年龄段分层，例如儿童、青年、中年、老年。
- 比较不同年龄段的误差率与不确定性标记率。

### 3. 不同设备来源

- 按设备厂商、成像协议、数字化来源进行分层。
- 评估模型对不同设备来源的鲁棒性与域偏移敏感性。

### 4. 不同医院来源

- 比较不同医院、地区、筛查项目的性能差异。
- 外部验证集结果必须单独报告，而非混入总体结果掩盖差异。

### 5. 不同图像质量

- 对低质量、模糊、欠曝、过曝、裁切、方向异常图像单独统计性能与拒识率。
- 关注低质量图像是否显著提高误报或漏报风险。

### 6. 不同疾病标签

- 对每个标签分别报告性能，不仅报告宏平均。
- 关注少见标签或高风险标签是否存在明显性能劣化。

## 七、可直接落地的文案产物

### 1. 隐私政策页面文案

> **隐私政策与数据处理说明**
>
> MedVision-CXR 旨在为胸部 X 光场景提供 AI 辅助分诊与医生复核支持。为完成本次分析，系统会对上传图像执行格式校验、匿名化命名、必要的图像处理、风险评估和审计留痕。系统默认遵循最小必要原则，不要求录入真实姓名、身份证号、手机号等直接身份信息。对常见图像文件会移除 EXIF 信息，对 DICOM 文件会执行必要的去标识化处理。平台支持基于权限的访问控制、JWT 鉴权、RBAC 角色权限、审计日志和数据删除机制。除满足合规、审计与必要业务要求外，平台不建议长期保存原始图像。若你认为某项图像或结果不应继续保留，可按平台规则发起删除请求。

### 2. 伦理说明页面文案

> **伦理与 Responsible AI 说明**
>
> MedVision-CXR 的核心原则是“AI 赋能医生，而不是替代医生”。系统只输出风险提示、风险分层、可解释热力图和复核建议，不输出确定性诊断，不提供治疗建议。平台特别强调人工复核、可解释性、公平性评估、隐私保护和问责机制。高风险或不确定性结果必须由具备资质的医生进一步判断。平台同时持续评估不同性别、年龄、设备来源、医院来源、图像质量和标签上的性能差异，以降低潜在偏差带来的不公平影响。

### 3. 医疗免责声明

> 本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。系统输出仅反映 AI 辅助风险提示，可能存在误差、偏差和外部泛化限制。任何临床决策都必须由具备资质的医疗专业人员结合临床信息作出。

### 4. 比赛路演伦理说明

> MedVision-CXR 不是“替代医生做诊断”的项目，而是一个面向基层和低资源医疗场景的 Responsible AI 辅助分诊系统。它通过多标签风险提示、总体风险等级、Grad-CAM 可解释结果和不确定性标记，帮助医生优先复核高风险或高不确定性的胸片。我们在设计中明确限制了系统能力边界，不输出确诊结论、不提供治疗建议，并将知情同意、隐私保护、公平性评估、模型版本追踪、删除机制和审计日志纳入产品与工程实现中。这种“人类在环”的设计更符合医疗伦理，也更适合 AI for Good 的社会价值导向。

### 5. README 中的 Responsible AI 章节

下面这段内容可直接放入 README：

```md
## Responsible AI

MedVision-CXR is designed as a human-in-the-loop chest X-ray triage system rather than an automated diagnosis product.

- The system provides AI-assisted risk prompts, triage prioritization, Grad-CAM interpretability, and doctor review support.
- It does not provide deterministic diagnosis or treatment advice.
- Final clinical judgment must always be made by qualified healthcare professionals.
- High-risk or uncertain outputs should automatically enter doctor review.
- The platform uses anonymized file naming, EXIF stripping, DICOM de-identification, JWT authentication, RBAC, audit logging, and governed deletion workflows.
- Fairness should be evaluated across sex, age, device source, hospital source, image quality, and disease labels.
- All outputs must include a disclaimer and be presented as AI-assisted risk assessment only.

See [docs/medvision-cxr-responsible-ai.md](docs/medvision-cxr-responsible-ai.md) for the full Responsible AI, privacy, fairness, and governance design.
```

### 6. Model Card 中的 Ethical Considerations 章节

下面这段内容可直接放入 Model Card：

```md
## Ethical Considerations

This model is intended for AI-assisted chest X-ray triage and doctor review prioritization only. It is not a medical diagnosis system and must not be used as the sole basis for clinical decision-making. The model does not provide treatment recommendations.

Potential risks include false positives, false negatives, domain shift, reduced performance on underrepresented populations, and bias related to sex, age, image quality, equipment source, hospital source, and disease prevalence. Heatmaps are provided only for interpretability support and do not constitute definitive lesion localization.

The model should be deployed only in workflows that include qualified healthcare professionals, explicit user-facing disclaimers, uncertainty handling, human review escalation, audit logging, model version traceability, and data deletion mechanisms.
```
