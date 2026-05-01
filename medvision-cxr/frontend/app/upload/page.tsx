import { PageHeader } from "@/components/ui/page-header";
import { UploadForm } from "@/components/upload/upload-form";

export default function UploadPage() {
  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="上传页面"
        title="上传胸部 X 光进行辅助分析"
        description="支持 PNG、JPG、JPEG，可选 DICOM。上传前请确认已获得合法授权，并避免提交包含明显身份信息的截图或患者资料页面。"
      />
      <UploadForm />
    </div>
  );
}
