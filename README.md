# ComfyUI AssetLibrary 插件

支持**角色 + 背景 + 道具**三种资产类型的智能加载器，集成角度匹配、变体切换、双模式控制。

## 功能特性

- **双模式切换**：
  - **检索模式** (enabled=True)：自动从资产库匹配并注入参考图
  - **透传模式** (enabled=False)：直接使用手动拖入工作流的参考图
- **三合一资产类型**：一个节点同时支持角色、背景、道具
- **角度智能匹配**：自动从提示词识别并加载对应角度的图片
- **变体切换**：背景支持白天/黄昏/夜晚/清晨等变体
- **优雅降级**：找不到匹配资源时自动降级，不卡死工作流
- **无外部依赖**：只使用 torch、numpy、PIL 等基础库

## 安装方法

### 方法一：复制到 ComfyUI custom_nodes 目录

```bash
# 克隆或复制到 ComfyUI 的 custom_nodes 目录
cd ComfyUI/custom_nodes
git clone https://your-repo/ComfyUI-AssetLibrary
```

### 方法二：复制到项目目录

```
ComfyUI/
├── custom_nodes/
│   └── ComfyUI-AssetLibrary/   ← 复制整个文件夹
│       ├── __init__.py
│       ├── nodes.py
│       └── README.md
```

重启 ComfyUI，等待节点加载完成。

---

## 资产库文件结构

```
asset_library/              ← 资产库根目录（可自定义名称）
├── 角色/                   ← 角色资产文件夹
│   ├── 林晚宁/
│   │   ├── 正面_front.png
│   │   ├── 左侧_left.png
│   │   ├── 右侧_right.png
│   │   ├── 背面_back.png
│   │   ├── 仰视_lookup.png
│   │   └── 俯视_lookdown.png
│   └── 顾霆轩/
│       ├── 正面_front.png
│       ├── 左侧_left.png
│       └── ...
├── 背景/                   ← 背景资产文件夹
│   ├── 天台/
│   │   └── 默认_default.png
│   ├── 教室/
│   │   ├── 白天_day.png
│   │   ├── 黄昏_dusk.png
│   │   └── 夜晚_night.png
│   └── ...
└── 道具/                   ← 道具资产文件夹
    ├── 宝剑/
    │   └── 默认_default.png
    ├── 雨伞/
    │   └── 默认_default.png
    └── ...
```

### 文件命名规则

**核心规则**：`中文标签_英文标签.扩展名`

| 示例 | 中文标签 | 英文标签 | 用途 |
|------|----------|----------|------|
| `正面_front.png` | 正面 | front | 角色正面角度 |
| `左侧_left.png` | 左侧 | left | 角色左侧角度 |
| `白天_day.png` | 白天 | day | 背景白天变体 |
| `黄昏_dusk.png` | 黄昏 | dusk | 背景黄昏变体 |
| `默认_default.png` | 默认 | default | 默认变体 |

---

## 节点参数说明

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | STRING | - | **必填**。提示词，从中提取角色名、背景名、道具名 |
| `library_path` | STRING | `asset_library` | 资产库根目录路径（支持绝对/相对路径） |
| `enabled` | BOOLEAN | `True` | **模式开关**：True=检索模式，False=透传模式 |
| `max_characters` | INT | 3 | 最大角色数量（1-5） |
| `max_backgrounds` | INT | 1 | 最大背景数量（0-3） |
| `max_props` | INT | 1 | 最大道具数量（0-3） |
| `manual_char_image1/2/3` | IMAGE | optional | 手动角色参考图（透传模式使用） |
| `manual_bg_image1` | IMAGE | optional | 手动背景参考图（透传模式使用） |
| `manual_prop_image1` | IMAGE | optional | 手动道具参考图（透传模式使用） |

### 输出端口

| 输出 | 类型 | 说明 |
|------|------|------|
| `character_image1/2/3` | IMAGE | 角色图片（按匹配顺序） |
| `character_name1/2/3` | STRING | 角色名称 |
| `background_image1` | IMAGE | 背景图片 |
| `background_name1` | STRING | 背景名称 |
| `prop_image1` | IMAGE | 道具图片 |
| `prop_name1` | STRING | 道具名称 |
| `matched_info` | STRING | 匹配详情日志 |

---

## 双模式说明

### 模式一：检索模式 (enabled=True)

自动从资产库匹配参考图：
- 根据提示词中的资产名称匹配文件夹
- 根据提示词中的角度/变体关键词匹配图片
- 检索不到时自动降级（正面→默认→第一张→空）

```
提示词：林晚宁回头看向左侧，顾霆轩站在天台

输出：
- character_image1: 林晚宁左侧图
- character_image2: 顾霆轩正面图（降级）
- background_image1: 天台默认图
```

### 模式二：透传模式 (enabled=False)

直接透传手动拖入工作流的参考图：
- 完全忽略资产库检索逻辑
- 直接输出手动输入的图片
- 用于快速对比效果或调试

```
设置 enabled = False
手动拖入参考图到 manual_char_image1

输出：
- character_image1: 手动输入的图片
- matched_info: "[手动模式] 资产库检索已关闭，使用手动参考图"
```

---

## 角度关键词映射

### 角色角度

| 角度 | 关键词 |
|------|--------|
| 左侧 | 左、左侧、侧脸左、转头向左、朝左、左转、left |
| 右侧 | 右、右侧、侧脸右、转头向右、回头、朝右、右转、right |
| 背面 | 背、背面、后、远去、离开、转身、back |
| 仰视 | 仰、抬头、仰视、低机位、仰拍、往上看、lookup |
| 俯视 | 俯、低头、俯视、高机位、俯拍、往下看、lookdown |
| 侧面 | 侧、侧面、侧身、侧脸、side |
| 正面 | 正、正面、front（默认） |

### 背景变体

| 变体 | 关键词 |
|------|--------|
| 白天 | 白天、日间、晴天、day |
| 黄昏 | 黄昏、日落、傍晚、夕阳、dusk |
| 夜晚 | 夜晚、夜间、深夜、晚上、night |
| 清晨 | 清晨、黎明、拂晓、日出、dawn |
| 默认 | 默认、default（降级备选） |

---

## 使用示例

### 基础使用（检索模式）

```
提示词：林晚宁在教室看窗外，顾霆轩站在天台

输出：
- character_image1: 林晚宁正面图
- character_image2: 顾霆轩正面图
- background_image1: 教室默认图
```

### 带角度指定

```
提示词：林晚宁回头看向左侧，顾霆轩站在天台背面

输出：
- character_image1: 林晚宁左侧图
- character_image2: 顾霆轩背面图
```

### 带背景变体

```
提示词：林晚宁在教室，黄昏时分

输出：
- character_image1: 林晚宁正面图
- background_image1: 教室黄昏图
```

### 透传模式（手动参考图）

```
1. enabled = False
2. 手动拖入参考图到 manual_char_image1

输出：
- character_image1: 手动输入的图片
- matched_info: "[手动模式] 资产库检索已关闭，使用手动参考图"
```

---

## 降级策略

当找不到精确匹配时，按以下顺序降级：

### 角色角度降级
1. 精确匹配 → 2. 正面图（文件名含"正"或"front"）→ 3. 文件夹第一张图 → 4. 空IMAGE

### 背景变体降级
1. 精确匹配 → 2. 默认变体（文件名含"默认"或"default"）→ 3. 文件夹第一张图 → 4. 空IMAGE

### 道具降级
1. 默认变体 → 2. 文件夹第一张图 → 3. 空IMAGE

---

## 提示词编写技巧

### ✅ 推荐写法
```
林晚宁正面照，顾霆轩回头看向右侧，教室白天
```

### ❌ 不推荐写法
```
角色A（林晚宁）在背景B（教室）的变体C（白天）
```

**原因**：节点通过文件夹名匹配，提示词中需要包含资产名称。

---

## 调试方法

### 1. 查看 Console 输出

节点会在 ComfyUI 控制台输出调试信息：
```
[AssetLibrary] 检索模式：从资产库自动匹配参考图
[AssetLibrary] 使用资产库路径: /path/to/asset_library
[AssetLibrary] 提示词: 林晚宁在教室...
[AssetLibrary] 匹配到角色: 林晚宁
[AssetLibrary] 角色 林晚宁 目标角度: front
[AssetLibrary] 加载角色图: /path/to/正面_front.png
[AssetLibrary] 匹配结果:
✅ 林晚宁(正面_front.png)
⚠️ 背景:教室(变体无匹配)
```

### 2. 快速切换模式对比

使用 `enabled` 开关快速对比：
- **检索模式**：自动匹配 vs 手动参考
- **透传模式**：跳过检索，直接使用手拖图

### 3. 检查 matched_info 输出

将 `matched_info` 连接到节点可以看到匹配详情。

---

## 故障排除

### Q: 节点没有匹配到任何资产？

**检查项**：
1. ✅ 提示词中是否包含资产名称（文件夹名）
2. ✅ `library_path` 是否正确（绝对路径或相对于 ComfyUI 目录）
3. ✅ 文件夹名是否包含中文或英文（支持混合）
4. ✅ 文件是否在正确的文件夹层级
5. ✅ `enabled` 是否为 True（检索模式）

### Q: 透传模式没有输出图片？

**检查项**：
1. ✅ `enabled` 是否为 False（透传模式）
2. ✅ 是否已手动拖入参考图到对应端口
3. ✅ 手动图片是否正确连接

### Q: 角度没有匹配到？

**检查项**：
1. ✅ 提示词中是否包含角度关键词
2. ✅ 文件名是否为 `中文_英文.扩展名` 格式
3. ✅ 查看 `matched_info` 确认匹配详情

---

## 技术实现

- **依赖库**：torch, numpy, PIL, os, re, glob
- **不依赖**：nodeutils, nodes.MAX_RESOLUTION
- **图片格式**：支持 PNG, JPG, JPEG, WEBP, BMP
- **输出格式**：ComfyUI 标准 IMAGE tensor

---

## 版本历史

### v2.0 (当前版本)
- ✅ 支持角色、背景、道具三种资产类型
- ✅ 添加双模式切换（检索/透传）
- ✅ 增加手动图片输入端口
- ✅ 优化角度匹配逻辑
- ✅ 移除不兼容依赖

### v1.0 (初始版本)
- 仅支持角色角度匹配
- 依赖 nodeutils
