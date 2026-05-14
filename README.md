# ComfyUI-AssetLibrary

> Smart Asset Library Manager for AI Short Drama & Film Production

[![ComfyUI Custom Node](https://img.shields.io/badge/ComfyUI-Custom%20Node-green)](https://comfyui.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Overview

ComfyUI-AssetLibrary is a powerful custom node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that provides unified asset management for AI short drama and film production. It enables **consistent character appearance** across multiple frames without the need for LoRA training.

**No LoRA training required. Just plug in and use.**

---

## Key Features

### 🎭 Smart Character Asset Management
- Organize character reference images by angles: front, left, right, back, lookup, lookdown, side, closeup, halfbody, fullbody, wide
- **Chinese angle matching**: Use `(角色名:左侧)` syntax for precise angle control
- Fuzzy matching fallback: Automatically finds the best available angle if exact match not found

### 🖼️ Background & Prop Support
- Background variants: default, day, dusk, night, dawn
- Prop assets with default fallback
- Automatic scene-time detection from prompts

### 🔗 Clean Integration
- **Bracket reference syntax**: `(character_name:angle)` - works with Chinese angles
- **Cleaned prompt output**: Seamlessly feeds into Qwen/text-to-image models
- Compatible with K9B (Flux2) workflow

---

## Installation

### Option 1: Git Clone (Recommended)

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/18235063136/ComfyUI-AssetLibrary.git
Option 2: Manual Download
Download or clone this repository
Copy the ComfyUI-AssetLibrary folder to ComfyUI/custom_nodes/
Directory Structure
Organize your asset library with this structure:
asset_library/
├── 角色/                          # Characters folder
│   ├── 小明_Jack/
│   │   ├── 正面_front.png
│   │   ├── 左侧_left.png
│   │   ├── 右侧_right.png
│   │   ├── 背面_back.png
│   │   ├── 仰视_lookup.png
│   │   └── 俯视_lookdown.png
│   └── 林晚宁_LinWanNing/
│       ├── 正面_front.png
│       ├── 左侧_left.png
│       └── ...
├── 背景/                          # Backgrounds folder
│   ├── 咖啡厅_Cafe/
│   │   ├── 默认_default.png
│   │   ├── 白天_day.png
│   │   ├── 黄昏_dusk.png
│   │   └── 夜晚_night.png
│   └── ...
└── 道具/                          # Props folder
    ├── 咖啡杯_CoffeeCup/
    │   └── 默认_default.png
    └── ...
Naming Convention
Asset Type	Format	Description
Character	中文名_EnglishName.png	Chinese for fuzzy match, English for precise angle detection
Background	场景名_EnglishName.png	Scene name + time variant suffix
Prop	道具名_EnglishName.png	Prop name
Usage
Basic Workflow
Create asset library folder at asset_library/ (or custom path)
Organize your reference images following the directory structure above
Add node to workflow: Find 📚 资产库智能加载器 under category K9B多锚点
Prompt Syntax
Bracket Reference (Recommended)
Use parentheses () or Chinese brackets （） to reference assets:
(小明:左侧) 站在咖啡厅与（林晚宁:右侧）闲聊
Supported Chinese angles:
Chinese	English	Description
正面	front	Front view
左侧	left	Left side view
右侧	right	Right side view
背面	back	Back view
回眸	lookback	Looking back
仰视	lookup	Looking up
俯视	lookdown	Looking down
侧面	side	Side view
特写	closeup	Close-up shot
半身	halfbody	Half body
全身	fullbody	Full body
远景	wide	Wide shot
Background Variants
（咖啡厅:白天）在阳光下喝咖啡
（咖啡厅:夜晚）烛光晚餐
Node Parameters
Parameter	Type	Default	Description
prompt	STRING	-	Input prompt text
library_path	STRING	asset_library	Path to asset library folder
enabled	BOOLEAN	True	Enable/disable auto-matching
max_characters	INT	3	Max character assets (1-5)
max_backgrounds	INT	1	Max background assets (0-3)
max_props	INT	1	Max prop assets (0-3)
Outputs
Output	Type	Description
character_image1-3	IMAGE	Matched character reference images
character_name1-3	STRING	Character names
background_image1	IMAGE	Matched background image
background_name1	STRING	Background name
prop_image1	IMAGE	Matched prop image
prop_name1	STRING	Prop name
matched_info	STRING	Matching debug info
cleaned_prompt	STRING	Cleaned prompt for downstream nodes
Example Workflow
[CLIP Text Encode] → [AssetLibraryLoader] → [Flux/K9B Model]
                        ↓                         ↓
                   Reference Images        Cleaned Prompt
Integration with K9B Workflow
This node is designed to work seamlessly with the K9B (Flux2) multi-anchor workflow:
Connect your prompt to AssetLibraryLoader
Use bracket syntax for precise character positioning
Outputs connect to K9B's character reference inputs
cleaned_prompt feeds into text encoding for image generation
Notes & Tips
For Best Results
Provide multiple angles: More angle references = better consistency
Use consistent naming: Folder names should match character names in prompts
High-quality references: Use clear, well-lit images as references
Match aspect ratio: Reference images similar to your target output size
Fallback Behavior
If exact angle not found → uses front/default image
If no default found → uses first available image
If no match at all → outputs empty/black tensor
Compatibility
✅ ComfyUI (tested with latest stable)
✅ K9B Workflow (Flux2 multi-anchor)
✅ Works with PrecisePersonReplace v3 for precise character replacement
Use Cases
🎬 AI Short Drama Automation: Maintain character consistency across scenes
🎥 AI Film Frame Generation: Multi-character scenes without face mixing
📸 Character Turnaround: Generate multiple angles from single references
🎮 Game Asset Creation: Consistent character sprites from reference sheets
License
This project is licensed under the MIT License - see the LICENSE file for details.
Author
HuaJun (华军) - ComfyUI Custom Node Developer
Contributing
Contributions are welcome! Please feel free to submit issues and pull requests.
Star History
If this project helps you, please give it a ⭐
