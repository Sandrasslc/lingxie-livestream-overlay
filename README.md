# 灵蟹直播底板 Skill

把活动海报和群二维码制作成 1920×1080 的透明直播底板：顶部保留品牌与主题，左侧为真实透明直播窗口，右侧竖排嘉宾信息与可扫描二维码。

## 功能

- 沿用活动海报的视觉风格生成 16:9 直播底板
- 支持两位或三位嘉宾的右侧信息栏
- 保留大面积透明直播窗口（PNG RGBA）
- 使用用户提供的原始二维码覆盖生成占位码
- 自动检测二维码区域、统一输出尺寸并检查透明度

## 安装

将整个目录复制到 Codex skills 目录：

```bash
cp -R lingxie-livestream-overlay ~/.codex/skills/
```

安装成品脚本依赖：

```bash
python3 -m pip install -r requirements.txt
```

重启 Codex 或开始新会话后即可使用。

## 使用

可以直接提出类似请求：

> 用今天的海报和这个二维码生成直播底板，中空部分要透明。

生成基础图后，Skill 会调用成品脚本，把用户提供的原始二维码覆盖到右侧，并验证透明窗口：

```bash
python3 scripts/finalize_overlay.py \
  --base /path/to/generated.png \
  --qr-source /path/to/qr-image.jpg \
  --output /path/to/直播画面底板-主题-16x9-透明.png
```

更多参数见 [SKILL.md](SKILL.md)。

## 目录

```text
lingxie-livestream-overlay/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── requirements.txt
└── scripts/
    └── finalize_overlay.py
```

## 隐私说明

仓库不包含活动海报、头像或群二维码。实际使用时由用户自行提供素材。
