"""
ComfyUI AssetLibrary 节点核心逻辑
支持角色、背景、道具三种资产类型的智能加载
- enabled=True: 检索模式，自动从资产库匹配注入参考图
- enabled=False: 透传模式，直接使用手动输入的参考图
"""

import os
import re
import glob
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# ============================================================
# 关键词映射配置
# ============================================================

# 角色角度关键词映射
ANGLE_KEYWORDS = {
    'front': ['正', '正面', '面朝', '朝前', '正脸', 'front'],
    'left': ['左', '左侧', '侧脸左', '转头向左', '朝左', '左转', 'left'],
    'right': ['右', '右侧', '侧脸右', '转头向右', '朝右', '右转', 'right'],
    'back': ['背面', '背影', '远去', '离开', 'back'],
    'lookback': ['回眸', '回头', '回头看', '转头看', '回望', '转身', '转头', 'lookback'],
    'lookup': ['仰', '抬头', '仰视', '低机位', '仰拍', '往上看', 'lookup'],
    'lookdown': ['俯', '低头', '俯视', '高机位', '俯拍', '往下看', 'lookdown'],
    'side': ['侧', '侧面', '侧身', '侧脸', 'side'],
    'closeup': ['特写', '近景', '脸部特写', '面部特写', 'closeup'],
    'halfbody': ['半身', '上半身', '腰部以上', 'halfbody'],
    'fullbody': ['全身', '全景', '站姿', 'fullbody'],
    'wide': ['远景', '大全景', '远处', 'wide'],
}

# 背景变体关键词映射
BACKGROUND_VARIANT_KEYWORDS = {
    'day': ['白天', '日间', '晴天', 'day'],
    'dusk': ['黄昏', '日落', '傍晚', '夕阳', 'dusk'],
    'night': ['夜晚', '夜间', '深夜', '晚上', 'night'],
    'dawn': ['清晨', '黎明', '拂晓', '日出', 'dawn'],
}

# 正面/默认关键词
FRONT_KEYWORDS = ['正', '正面', 'front', '前面', '正脸']
DEFAULT_KEYWORDS = ['默认', 'default', 'standard', '标准']


# ============================================================
# 辅助函数
# ============================================================

def pil2tensor(image: Image.Image) -> torch.Tensor:
    """将PIL图像转换为ComfyUI的tensor格式 [H, W, C]"""
    array = np.array(image).astype(np.float32) / 255.0
    return torch.from_numpy(array)[None,]


def create_black_tensor() -> torch.Tensor:
    """创建1x1黑色tensor作为空输出"""
    return torch.zeros(1, 1, 1, 3, dtype=torch.float32)


def get_char_name_from_folder(folder_name: str) -> str:
    """从文件夹名提取角色名（去掉后缀）"""
    if '_' in folder_name:
        # 处理 "林晚宁_LinWanNing" 格式
        return folder_name.split('_')[0]
    return folder_name


def parse_filename(filename: str) -> Tuple[str, str]:
    """
    解析文件名，提取中文和英文标签
    例如："正面_front.png" -> ("正面", "front")
    例如："白天_day.png" -> ("白天", "day")
    例如："默认_default.png" -> ("默认", "default")
    """
    name_without_ext = os.path.splitext(filename)[0]
    
    if '_' in name_without_ext:
        parts = name_without_ext.split('_', 1)
        return parts[0], parts[1] if len(parts) > 1 else ""
    
    return name_without_ext, ""


def keyword_match(text: str, keywords: List[str]) -> bool:
    """检查文本中是否包含任意关键词"""
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False


def match_angle_from_prompt(prompt: str, asset_type: str = 'character') -> str:
    """
    从提示词中匹配角度或变体
    asset_type: 'character' 或 'background' 或 'prop'
    返回匹配到的角度标签，如 'left', 'right', 'front', 'day', 'dusk' 等
    """
    if asset_type == 'character':
        # 角色角度匹配
        for angle, keywords in ANGLE_KEYWORDS.items():
            if keyword_match(prompt, keywords):
                return angle
        return 'front'  # 默认正面
    
    elif asset_type == 'background':
        # 背景变体匹配
        for variant, keywords in BACKGROUND_VARIANT_KEYWORDS.items():
            if keyword_match(prompt, keywords):
                return variant
        return 'default'  # 默认变体
    
    return 'default'


def find_matching_images(
    folder_path: str,
    angle_or_variant: str,
    asset_type: str = 'character'
) -> List[str]:
    """
    在文件夹中查找匹配角度/变体的图片
    优先级：精确匹配 > 正面图/默认图 > 文件夹第一张图
    """
    all_images = []
    
    # 获取所有支持格式的图片
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp']:
        all_images.extend(glob.glob(os.path.join(folder_path, ext)))
        all_images.extend(glob.glob(os.path.join(folder_path, ext.upper())))
    
    if not all_images:
        return []
    
    # 解析所有图片，分类
    matched_images = []   # 精确匹配
    front_images = []     # 正面图（降级用）
    default_images = []   # 默认变体（背景降级用）
    
    for img_path in all_images:
        filename = os.path.basename(img_path)
        cn_label, en_label = parse_filename(filename)
        
        # 检查是否匹配目标角度/变体
        is_match = False
        
        if asset_type == 'character':
            # 正面图特殊处理
            if cn_label in ['正', '正面'] or en_label.lower() == 'front':
                front_images.append(img_path)
                if angle_or_variant == 'front':
                    is_match = True
            else:
                for angle, keywords in ANGLE_KEYWORDS.items():
                    if angle == angle_or_variant:
                        if cn_label in keywords or en_label.lower() in keywords:
                            is_match = True
                            break
        
        elif asset_type == 'background':
            if cn_label in DEFAULT_KEYWORDS or en_label.lower() == 'default':
                default_images.append(img_path)
                if angle_or_variant == 'default':
                    is_match = True
            else:
                for variant, keywords in BACKGROUND_VARIANT_KEYWORDS.items():
                    if variant == angle_or_variant:
                        if cn_label in keywords or en_label.lower() in keywords:
                            is_match = True
                            break
        else:
            # 道具：默认变体
            if cn_label in DEFAULT_KEYWORDS or en_label.lower() == 'default':
                default_images.append(img_path)
                if angle_or_variant == 'default':
                    is_match = True
        
        if is_match:
            matched_images.append(img_path)
    
    # 返回优先级：精确匹配 > 正面图/默认图 > 第一张图
    if matched_images:
        return matched_images
    if front_images:
        return front_images
    if default_images:
        return default_images
    # 最后兜底：第一张图
    return [all_images[0]] if all_images else []


def find_asset_in_prompt(
    prompt: str,
    library_path: str,
    asset_folder: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    从提示词中匹配资产并返回(文件夹路径, 匹配名称)
    """
    # 构建资产文件夹的完整路径
    asset_path = os.path.join(library_path, asset_folder)
    
    if not os.path.isdir(asset_path):
        return None, None
    
    # 获取所有子文件夹
    subfolders = [f for f in os.listdir(asset_path) 
                  if os.path.isdir(os.path.join(asset_path, f))]
    
    if not subfolders:
        return None, None
    
    # 最长匹配优先策略
    # 对提示词进行分词处理
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', prompt.lower())
    
    best_match_folder = None
    best_match_name = None
    max_len = 0
    
    for folder in subfolders:
        folder_lower = folder.lower()
        
        # 检查文件夹名是否在提示词中
        if folder_lower in prompt.lower():
            match_len = len(folder)
            if match_len > max_len:
                max_len = match_len
                best_match_folder = folder
                best_match_name = get_char_name_from_folder(folder)
        
        # 检查分词后的关键词
        folder_parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', folder_lower)
        for part in folder_parts:
            if len(part) >= 2 and part in words:
                if len(part) > max_len:
                    max_len = len(part)
                    best_match_folder = folder
                    best_match_name = get_char_name_from_folder(folder)
    
    if best_match_folder:
        return os.path.join(asset_path, best_match_folder), best_match_name
    
    return None, None


def get_character_context(prompt: str, char_name: str, radius: int = 30) -> str:
    """
    提取角色名附近的上下文文本，用于独立匹配角度
    radius: 角色名前后各取多少字符
    """
    try:
        pos = prompt.lower().index(char_name.lower())
        start = max(0, pos - radius)
        end = min(len(prompt), pos + len(char_name) + radius)
        return prompt[start:end]
    except ValueError:
        return prompt


def load_image_safe(image_path: str) -> Optional[torch.Tensor]:
    """安全加载图片，返回tensor或None"""
    try:
        img = Image.open(image_path).convert('RGB')
        return pil2tensor(img)
    except Exception as e:
        print(f"[AssetLibrary] 加载图片失败 {image_path}: {e}")
        return None


# ============================================================
# 主节点类
# ============================================================

class AssetLibraryLoader:
    """资产库智能加载器 - 支持角色、背景、道具三种资产类型"""

    CATEGORY = "K9B多锚点"
    FUNCTION = "process"
    RETURN_TYPES = (
        "IMAGE", "IMAGE", "IMAGE",
        "STRING", "STRING", "STRING",
        "IMAGE",
        "STRING",
        "IMAGE",
        "STRING",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "character_image1", "character_image2", "character_image3",
        "character_name1", "character_name2", "character_name3",
        "background_image1",
        "background_name1",
        "prop_image1",
        "prop_name1",
        "matched_info",
        "cleaned_prompt",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "library_path": ("STRING", {"default": "asset_library"}),
                "enabled": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                # 接线用提示词输入，优先级高于文本框（解决STRING类型不匹配问题）
                "linked_prompt": ("STRING", {"forceInput": True}),
                "max_characters": ("INT", {"default": 3, "min": 1, "max": 5}),
                "max_backgrounds": ("INT", {"default": 1, "min": 0, "max": 3}),
                "max_props": ("INT", {"default": 1, "min": 0, "max": 3}),
                # 手动图片输入（透传模式使用）
                "manual_char_image1": ("IMAGE",),
                "manual_char_image2": ("IMAGE",),
                "manual_char_image3": ("IMAGE",),
                "manual_bg_image1": ("IMAGE",),
                "manual_prop_image1": ("IMAGE",),
            }
        }

    def __init__(self):
        self.device = "cpu"

    def process(
        self,
        prompt: str,
        library_path: str,
        enabled: bool,
        max_characters: int = 3,
        max_backgrounds: int = 1,
        max_props: int = 1,
        # 接线用提示词（优先级高于文本框）
        linked_prompt: str = None,
        # 手动图片输入（optional，可能为None）
        manual_char_image1: torch.Tensor = None,
        manual_char_image2: torch.Tensor = None,
        manual_char_image3: torch.Tensor = None,
        manual_bg_image1: torch.Tensor = None,
        manual_prop_image1: torch.Tensor = None,
    ):
        """主处理函数"""
        
        # 优先使用接线传入的提示词
        if linked_prompt is not None and linked_prompt != "":
            prompt = linked_prompt
            print(f"[AssetLibrary] 使用接线提示词")
        
        # ============================================================
        # 模式一：透传模式 (enabled=False)
        # 直接透传手动输入的参考图，不做任何检索
        # ============================================================
        if not enabled:
            print("[AssetLibrary] 透传模式：直接使用手动参考图，跳过资产库检索")
            
            # 透传手动图片，有就用，没有就返回空IMAGE
            char1 = manual_char_image1 if manual_char_image1 is not None else create_black_tensor()
            char2 = manual_char_image2 if manual_char_image2 is not None else create_black_tensor()
            char3 = manual_char_image3 if manual_char_image3 is not None else create_black_tensor()
            bg1 = manual_bg_image1 if manual_bg_image1 is not None else create_black_tensor()
            prop1 = manual_prop_image1 if manual_prop_image1 is not None else create_black_tensor()
            
            return (
                char1,  # character_image1
                char2,  # character_image2
                char3,  # character_image3
                "",     # character_name1 (透传模式不输出名称)
                "",     # character_name2
                "",     # character_name3
                bg1,    # background_image1
                "",     # background_name1
                prop1,  # prop_image1
                "",     # prop_name1
                "[手动模式] 资产库检索已关闭，使用手动参考图",
            )

        # ============================================================
        # 模式二：检索模式 (enabled=True)
        # 自动从资产库匹配并注入参考图
        # ============================================================
        print("[AssetLibrary] 检索模式：从资产库自动匹配参考图")
        
        # 初始化输出
        char_images = [create_black_tensor() for _ in range(3)]
        char_names = ["", "", ""]
        bg_image = create_black_tensor()
        bg_name = ""
        prop_image = create_black_tensor()
        prop_name = ""
        
        all_match_info = []
        
        # 确保library_path是绝对路径
        if not os.path.isabs(library_path):
            # 尝试相对于当前工作目录
            abs_library_path = os.path.join(os.getcwd(), library_path)
            if not os.path.isdir(abs_library_path):
                # 尝试相对于脚本目录
                script_dir = os.path.dirname(os.path.abspath(__file__))
                abs_library_path = os.path.join(script_dir, library_path)
            library_path = abs_library_path

        print(f"[AssetLibrary] 使用资产库路径: {library_path}")
        print(f"[AssetLibrary] 提示词: {prompt[:100]}...")

        # ============================================================
        # 检索角色
        # ============================================================
        # 括号引用格式：（角色名）或（角色名:角度）
        # 角度支持中文：正面/左侧/右侧/背面/回眸/仰/俯/侧面/特写/半身/全身/远景
        # 括号外的是给千问看的描述，不触发角度匹配
        # 示例：（奥玲:左侧）站在左边与（林晚宁:右侧）闲聊（小雨:正面）喝咖啡
        bracket_pattern = re.compile(r'[（(]([^）)]+)[）)]')
        bracket_matches = bracket_pattern.findall(prompt)
        
        # 中文角度→英文标签映射
        ANGLE_CN_TO_EN = {
            '正面': 'front', '正': 'front', '正脸': 'front',
            '左侧': 'left', '左': 'left',
            '右侧': 'right', '右': 'right',
            '背面': 'back', '背影': 'back',
            '回眸': 'lookback', '回头': 'lookback',
            '仰': 'lookup', '仰视': 'lookup', '抬头': 'lookup',
            '俯': 'lookdown', '俯视': 'lookdown', '低头': 'lookdown',
            '侧面': 'side', '侧': 'side',
            '特写': 'closeup', '近景': 'closeup',
            '半身': 'halfbody',
            '全身': 'fullbody',
            '远景': 'wide',
        }
        
        # 解析括号引用：(角色名, 角度英文标签) 列表
        bracket_refs = []
        for ref in bracket_matches:
            ref = ref.strip()
            if ':' in ref or '：' in ref:
                # 兼容中英文冒号
                parts = re.split(r'[:：]', ref, 1)
                name = parts[0].strip()
                angle_cn = parts[1].strip()
                angle_en = ANGLE_CN_TO_EN.get(angle_cn, angle_cn.lower())  # 中文转英文，英文直接用
                bracket_refs.append((name, angle_en))
            else:
                bracket_refs.append((ref, None))  # 无角度指定，默认front
        
        print(f"[AssetLibrary] 括号引用: {bracket_refs}")
        
        char_folder = "角色"
        if os.path.isdir(os.path.join(library_path, char_folder)):
            char_path = os.path.join(library_path, char_folder)
            
            # 获取所有角色文件夹
            char_folders = [f for f in os.listdir(char_path) 
                          if os.path.isdir(os.path.join(char_path, f))]
            
            # 从提示词中匹配角色（按出现顺序）
            matched_chars = []  # (folder, char_name, explicit_angle)
            used_folders = set()
            
            # 第一步：括号引用精确匹配（优先）
            for ref_name, ref_angle in bracket_refs:
                ref_lower = ref_name.lower()
                for folder in char_folders:
                    if folder in used_folders:
                        continue
                    char_name = get_char_name_from_folder(folder)
                    if char_name.lower() == ref_lower or folder.lower() == ref_lower:
                        matched_chars.append((folder, char_name, ref_angle))
                        used_folders.add(folder)
                        angle_hint = f" → 指定角度: {ref_angle}" if ref_angle else " → 默认角度: front"
                        print(f"[AssetLibrary] 括号精确匹配角色: {char_name}{angle_hint}")
                        break
            
            # 第二步：模糊匹配（兜底，无括号引用时使用）
            for folder in char_folders:
                if folder in used_folders:
                    continue
                folder_lower = folder.lower()
                char_name = get_char_name_from_folder(folder)
                
                # 简单匹配：角色名出现在提示词中
                if char_name.lower() in prompt.lower():
                    if folder not in used_folders:
                        matched_chars.append((folder, char_name, None))
                        used_folders.add(folder)
                        print(f"[AssetLibrary] 匹配到角色: {char_name}")
                else:
                    # 尝试部分匹配
                    name_parts = re.findall(r'[\u4e00-\u9fff]+', char_name)
                    for part in name_parts:
                        if len(part) >= 2 and part in prompt:
                            if folder not in used_folders:
                                matched_chars.append((folder, char_name, None))
                                used_folders.add(folder)
                                print(f"[AssetLibrary] 匹配到角色: {char_name} (部分匹配)")
                                break
            
            # 限制数量
            matched_chars = matched_chars[:max_characters]
            
            # 加载角色图片
            for i, (folder, char_name, explicit_angle) in enumerate(matched_chars):
                if i >= 3:
                    break
                
                folder_full_path = os.path.join(char_path, folder)
                
                # 角度确定逻辑：
                # 1. 括号指定了角度 → 用指定的
                # 2. 无括号/未指定 → 从角色附近上下文匹配（旧逻辑兜底）
                if explicit_angle:
                    target_angle = explicit_angle
                else:
                    char_context = get_character_context(prompt, char_name)
                    target_angle = match_angle_from_prompt(char_context, 'character')
                
                print(f"[AssetLibrary] 角色 {char_name} → 目标角度: {target_angle}")
                
                # 查找匹配的图片
                matching_images = find_matching_images(
                    folder_full_path, 
                    target_angle, 
                    'character'
                )
                
                if matching_images:
                    tensor = load_image_safe(matching_images[0])
                    if tensor is not None:
                        char_images[i] = tensor
                        char_names[i] = char_name
                        img_name = os.path.basename(matching_images[0])
                        all_match_info.append(f"✅ {char_name}({img_name})")
                        print(f"[AssetLibrary] 加载角色图: {matching_images[0]}")
                else:
                    all_match_info.append(f"⚠️ {char_name}(角度无匹配)")
                    print(f"[AssetLibrary] 角色 {char_name} 未找到匹配角度图")
        
        # ============================================================
        # 检索背景
        # ============================================================
        bg_folder = "背景"
        if max_backgrounds > 0 and os.path.isdir(os.path.join(library_path, bg_folder)):
            bg_path = os.path.join(library_path, bg_folder)
            
            # 从提示词中匹配背景
            bg_folder_path, bg_matched_name = find_asset_in_prompt(
                prompt, library_path, bg_folder
            )
            
            if bg_folder_path and bg_matched_name:
                print(f"[AssetLibrary] 匹配到背景: {bg_matched_name}")
                
                # 匹配变体
                target_variant = match_angle_from_prompt(prompt, 'background')
                print(f"[AssetLibrary] 背景 {bg_matched_name} 目标变体: {target_variant}")
                
                # 查找匹配的图片
                matching_images = find_matching_images(
                    bg_folder_path, 
                    target_variant, 
                    'background'
                )
                
                if matching_images:
                    tensor = load_image_safe(matching_images[0])
                    if tensor is not None:
                        bg_image = tensor
                        bg_name = bg_matched_name
                        img_name = os.path.basename(matching_images[0])
                        all_match_info.append(f"✅ 背景:{bg_matched_name}({img_name})")
                        print(f"[AssetLibrary] 加载背景图: {matching_images[0]}")
                else:
                    all_match_info.append(f"⚠️ 背景:{bg_matched_name}(变体无匹配)")
                    print(f"[AssetLibrary] 背景 {bg_matched_name} 未找到匹配变体图")
        
        # ============================================================
        # 检索道具
        # ============================================================
        prop_folder = "道具"
        if max_props > 0 and os.path.isdir(os.path.join(library_path, prop_folder)):
            prop_path = os.path.join(library_path, prop_folder)
            
            # 从提示词中匹配道具
            prop_folder_path, prop_matched_name = find_asset_in_prompt(
                prompt, library_path, prop_folder
            )
            
            if prop_folder_path and prop_matched_name:
                print(f"[AssetLibrary] 匹配到道具: {prop_matched_name}")
                
                # 道具默认用默认变体
                matching_images = find_matching_images(
                    prop_folder_path, 
                    'default', 
                    'prop'
                )
                
                if matching_images:
                    tensor = load_image_safe(matching_images[0])
                    if tensor is not None:
                        prop_image = tensor
                        prop_name = prop_matched_name
                        img_name = os.path.basename(matching_images[0])
                        all_match_info.append(f"✅ 道具:{prop_matched_name}({img_name})")
                        print(f"[AssetLibrary] 加载道具图: {matching_images[0]}")
                else:
                    all_match_info.append(f"⚠️ 道具:{prop_matched_name}(无图片)")
                    print(f"[AssetLibrary] 道具 {prop_matched_name} 未找到图片")

        # ============================================================
        # 构建匹配信息
        # ============================================================
        if all_match_info:
            matched_info = "\n".join(all_match_info)
        else:
            matched_info = "[未匹配] 提示词中未识别到资产库中的角色/背景/道具"

        print(f"[AssetLibrary] 匹配结果:\n{matched_info}")

        return (
            char_images[0],  # character_image1
            char_images[1],  # character_image2
            char_images[2],  # character_image3
            char_names[0],   # character_name1
            char_names[1],   # character_name2
            char_names[2],   # character_name3
            bg_image,        # background_image1
            bg_name,         # background_name1
            prop_image,      # prop_image1
            prop_name,       # prop_name1
            matched_info,   # matched_info
            prompt,          # cleaned_prompt（原样输出，直接接千问文本输入）
        )


# ============================================================
# 节点注册
# ============================================================

NODE_CLASS_MAPPINGS = {
    "AssetLibraryLoader": AssetLibraryLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AssetLibraryLoader": "📚 资产库智能加载器（华军）",
}
