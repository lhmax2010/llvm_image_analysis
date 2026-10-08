# stage3补充补丁

实际交付位于docs/complementary.patch，按用户本轮指定位置保存；只修改mic/archive.py的imports和_call_external，不重改总部四压缩函数、tar回退、config或imager。

基线需包含真实3cc580e诊断依赖及c446578、eadc8fd5；dry-run与28组普通用户测试、真实日志验证通过。两份总部Git format-patch原文准入downloads/src/hq_mic/0001-*.patch；clone忽略。详情见docs/hq_patch_review.md、docs/patch_proposal.md。流式只写方案，未实现；mktemp等其余风险明确保留，不冒充已修。
