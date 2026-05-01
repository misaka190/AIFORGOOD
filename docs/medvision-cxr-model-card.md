# MedVision-CXR Model Card

## 1. Model Details | 模型基本信息

### English

- Model name: MedVision-CXR DenseNet121 Multi-Label Risk Model
- Version: `cxr-densenet121-v1.3.0`
- Architecture: DenseNet121 multi-label chest X-ray classifier with sigmoid output head
- Input: frontal chest X-ray images in PNG, JPG, JPEG, or de-identified DICOM format, resized to `320 x 320`
- Output:
	- `risk_assessment`
	- `triage_result`
	- `ai_assisted_findings`
	- `doctor_review_required`
	- `uncertainty_flag`
	- `disclaimer`
- Developer: MedVision-CXR project team
- Date: 2026-05-01

### 中文

- 模型名称：MedVision-CXR DenseNet121 胸片多标签风险模型
- 版本：`cxr-densenet121-v1.3.0`
- 架构：基于 DenseNet121 的胸部 X 光多标签分类模型，输出层采用 sigmoid
- 输入：PNG、JPG、JPEG 或经去标识化处理的 DICOM 胸片图像，统一缩放为 `320 x 320`
- 输出：
	- `risk_assessment`
	- `triage_result`
	- `ai_assisted_findings`
	- `doctor_review_required`
	- `uncertainty_flag`
	- `disclaimer`
- 开发者：MedVision-CXR 项目团队
- 日期：2026-05-01

## 2. Intended Use | 预期用途

### English

This model is intended for:

- AI-assisted chest X-ray triage
- prioritization for medical review
- educational or research demo environments

The model is designed to support clinical workflow prioritization and human review, not to replace medical professionals.

### 中文

本模型的预期用途包括：

- 胸部 X 光 AI 辅助分诊
- 医疗复核优先级排序
- 教学、研究或竞赛演示场景

模型设计目标是支持临床工作流排序和人工复核，而不是替代医疗专业人员。

## 3. Out-of-Scope Use | 非适用用途

### English

This model must not be used for:

- autonomous diagnosis
- emergency decision-making without clinician confirmation
- treatment recommendation
- use without clinician oversight
- deployment without local validation

### 中文

本模型不得用于以下场景：

- 自动化诊断
- 未经医生确认的急诊决策
- 治疗方案推荐
- 没有临床人员监督的独立使用
- 未经过本地验证即直接部署到真实医疗环境

## 4. Training Data | 训练数据

### English

- Dataset source: CheXpert-style multi-label chest X-ray training pipeline, with project design compatibility for public datasets such as NIH ChestX-ray14, MIMIC-CXR, and PadChest where governance allows
- Labels:
	- Atelectasis
	- Cardiomegaly
	- Consolidation
	- Edema
	- Pleural Effusion
	- Pneumonia
	- Pneumothorax
	- Lung Opacity
	- Enlarged Cardiomediastinum
	- Fracture
	- Support Devices
	- No Finding
- Preprocessing:
	- resize to `320 x 320`
	- optional CLAHE enhancement
	- normalization for model input
	- patient-level label handling with CheXpert-style uncertain label mapping
	- randomized augmentation in training and deterministic resize in evaluation
- Known limitations:
	- label noise may exist in public chest X-ray datasets
	- uncertain labels may be mapped or ignored depending on policy
	- performance may be weaker on rare labels or out-of-distribution sites
	- training data may underrepresent some demographic groups, device sources, or care settings

### 中文

- 数据来源：以 CheXpert 风格的多标签胸片训练流程为主，设计上兼容 NIH ChestX-ray14、MIMIC-CXR、PadChest 等公开数据集，前提是满足数据治理要求
- 标签体系：
	- Atelectasis
	- Cardiomegaly
	- Consolidation
	- Edema
	- Pleural Effusion
	- Pneumonia
	- Pneumothorax
	- Lung Opacity
	- Enlarged Cardiomediastinum
	- Fracture
	- Support Devices
	- No Finding
- 预处理：
	- 缩放到 `320 x 320`
	- 可选 CLAHE 增强
	- 归一化处理
	- 采用 CheXpert 风格的不确定标签映射策略
	- 训练阶段做随机增强，评估阶段做确定性缩放
- 已知局限：
	- 公共胸片数据集可能存在标签噪声
	- 不确定标签的映射策略会影响训练目标
	- 稀有标签和分布外医院场景表现可能较弱
	- 训练数据可能对某些性别、年龄、设备来源或临床环境代表性不足

## 5. Evaluation Data | 评估数据

### English

- Validation split: held-out validation data used for threshold tuning, calibration, and model selection
- Test split: independent test set used for final performance reporting
- Patient-level split: required to avoid leakage between train, validation, and test sets

Recommended practice:

- maintain patient-level stratification across all splits
- report hospital/source-level composition for each split
- separate internal evaluation from external validation

### 中文

- 验证集：用于阈值调优、校准和模型选择的留出数据
- 测试集：用于最终性能报告的独立测试数据
- 按患者级别切分：必须按患者而不是按图像切分，避免训练集与评估集之间的数据泄露

推荐做法：

- 在所有切分中保持患者级别分层
- 报告各切分中的医院来源和设备来源组成
- 区分内部评估与外部验证结果

## 6. Metrics | 评估指标

### English

Recommended metrics to report:

- AUROC
- AUPRC
- Sensitivity
- Specificity
- F1-score
- Calibration:
	- expected calibration error
	- reliability curves
	- threshold-specific operating points
- Fairness metrics:
	- subgroup AUROC
	- subgroup sensitivity gap
	- subgroup specificity gap
	- calibration gap across subgroups

At minimum, all metrics should be reported both overall and per label.

### 中文

建议报告的指标包括：

- AUROC
- AUPRC
- Sensitivity（灵敏度）
- Specificity（特异度）
- F1-score
- Calibration（校准）：
	- 期望校准误差
	- 可靠性曲线
	- 阈值对应的操作点
- Fairness metrics（公平性指标）：
	- 亚群 AUROC
	- 亚群灵敏度差异
	- 亚群特异度差异
	- 不同亚群之间的校准差异

至少应同时报告总体指标和逐标签指标，不能只给宏平均结果。

## 7. Ethical Considerations | 伦理考量

### English

- Bias:
	- model performance may differ across sex, age, device source, hospital source, image quality, and disease prevalence
	- underrepresented groups may experience higher false negative or false positive rates
- Privacy:
	- uploaded images should be anonymized, EXIF-stripped, and DICOM de-identified before long-term handling
	- only minimum necessary metadata should be retained
- Human oversight:
	- the model must operate in a human-in-the-loop workflow
	- high-risk or uncertain outputs should trigger doctor review
- Transparency:
	- outputs must be framed as risk prompts and triage support, not diagnosis
	- user-facing disclaimer is mandatory
- Low-resource deployment risks:
	- image acquisition quality may be lower
	- device variability and network limitations may increase operational failure risk
	- external validation is especially important before deployment in underserved regions

### 中文

- 偏差：
	- 模型在不同性别、年龄、设备来源、医院来源、图像质量和疾病流行率上的表现可能不同
	- 代表性不足的亚群体可能面临更高的假阴性或假阳性风险
- 隐私：
	- 上传图像应在长期处理前完成匿名化、EXIF 清除和 DICOM 去标识化
	- 仅保留最小必要元数据
- 人类监督：
	- 模型必须运行在“人类在环”的工作流中
	- 高风险或不确定结果必须触发医生复核
- 透明性：
	- 输出必须被表述为风险提示和分诊支持，而不是诊断结论
	- 必须向用户展示免责声明
- 低资源部署风险：
	- 图像采集质量可能更低
	- 设备差异和网络限制可能提高运行失败风险
	- 在基层和低资源地区部署前尤其需要外部验证

## 8. Caveats and Recommendations | 注意事项与建议

### English

- This model is not a diagnostic device.
- All outputs require doctor review in clinical use.
- External validation is required before real deployment.
- Performance may differ across populations, acquisition protocols, and devices.
- Thresholds should be selected according to local operating priorities and error tolerance.

### 中文

- 本模型不是诊断设备。
- 在临床环境中，所有输出都需要医生复核。
- 真正部署前必须完成外部验证。
- 模型在不同人群、采集协议和设备上的表现可能不同。
- 阈值应根据本地业务重点和可接受错误率进行调整。

## 9. Explainability | 可解释性

### English

- Grad-CAM is used to provide a visual explanation of regions that influenced the model output.
- Heatmaps should be interpreted only as approximate attention visualization.
- Limitations of heatmaps:
	- they do not prove lesion boundaries
	- they may be unstable across architectures and preprocessing choices
	- visually plausible heatmaps do not guarantee correct predictions

### 中文

- 系统使用 Grad-CAM 提供影响模型输出的关注区域可视化。
- 热力图只能被理解为近似的注意力可视化，而不是病灶边界证明。
- 热力图局限包括：
	- 不能证明病灶真实边界
	- 可能受模型结构和预处理方式影响而不稳定
	- 热力图看起来合理并不代表预测一定正确

## 10. Human Oversight | 人类监督

### English

- A qualified clinician must remain responsible for final clinical interpretation.
- High-risk outputs and all `uncertainty_flag = true` cases should be escalated for doctor review.
- Review decisions should be stored separately from raw model outputs to preserve traceability.

### 中文

- 最终临床解释必须由具备资质的医生负责。
- 高风险结果和所有 `uncertainty_flag = true` 的结果都应升级到医生复核流程。
- 医生复核结果应与原始模型输出分开保存，以保留可追踪性。

## 11. Privacy Considerations | 隐私保护考量

### English

- Use UUID-based or anonymized file names.
- Strip EXIF metadata from common image formats.
- Apply DICOM de-identification before further processing.
- Use RBAC, JWT, HTTPS, audit logging, and controlled deletion workflows.
- Avoid collecting direct personal identifiers unless legally required.

### 中文

- 使用 UUID 或匿名化文件名。
- 对常见图像格式移除 EXIF 元数据。
- 对 DICOM 文件执行去标识化。
- 使用 RBAC、JWT、HTTPS、审计日志和受控删除流程。
- 除非法律或业务明确要求，否则避免收集直接身份标识信息。

## 12. Environmental Considerations | 环境影响

### English

- Training deep convolutional models on medical image datasets can require substantial GPU resources.
- Re-training should be scheduled only when justified by data drift, clinical need, or model improvement goals.
- Lightweight deployment options such as EfficientNet-B0 or optimized inference runtimes may reduce energy cost in resource-constrained environments.

### 中文

- 在医学影像数据上训练深度卷积模型可能需要较高的 GPU 资源消耗。
- 只有在出现数据漂移、临床需求变化或明确性能改进目标时，才应进行重新训练。
- 在资源受限环境中，可考虑 EfficientNet-B0 或优化后的推理运行时以降低能耗。

## 13. Versioning | 版本管理

### English

- Each prediction should be bound to a specific `model_version`.
- Changes in weights, preprocessing, label policy, threshold policy, or calibration should trigger a new model version.
- Historical predictions should remain traceable to the exact version used at inference time.

### 中文

- 每条预测记录都应绑定具体的 `model_version`。
- 权重、预处理、标签映射、阈值策略或校准策略发生变化时，应发布新版本。
- 历史预测结果必须能够追溯到推理时使用的精确模型版本。

## 14. Contact | 联系方式

### English

- Contact team: MedVision-CXR project maintainers
- Suggested contact route: repository issue tracker or project email alias

### 中文

- 联系团队：MedVision-CXR 项目维护者
- 建议联系渠道：仓库 issue 或项目统一邮箱别名
