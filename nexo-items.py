import yaml
import json
import os
import re

NEXO_DIR = 'nexo-items'
OUTPUT_FILE = 'items.json'

REQUIRED_CATEGORIES = [
    'equipment', 'relics', 'materials', 'blocks', 'food', 'misc', 'plants'
]

TAG_TO_CATEGORY = {
    'tag_equipment': 'equipment',
    'tag_relic':     'relics',
    'tag_material':  'materials',
    'tag_block':     'blocks',
    'tag_provision': 'food',
    'tag_other':     'misc'
}

COLOR_MAP = {
    'black': '#000000', 'dark_blue': '#0000AA', 'dark_green': '#00AA00', 'dark_aqua': '#00AAAA',
    'dark_red': '#AA0000', 'dark_purple': '#AA00AA', 'gold': '#FFAA00', 'gray': '#AAAAAA',
    'dark_gray': '#555555', 'blue': '#5555FF', 'green': '#55FF55', 'aqua': '#55FFFF',
    'red': '#FF5555', 'light_purple': '#FF55FF', 'yellow': '#FFFF55', 'white': '#FFFFFF',
    'reset': '#FFFFFF'
}

ICON_MAP = {
    'PAPER': 'scroll', 'EMERALD': 'shield-check', 'DIAMOND': 'gem',
    'LEATHER_HORSE_ARMOR': 'package', 'POISONOUS_POTATO': 'cookie',
    'TRIDENT': 'send', 'TOTEM_OF_UNDYING': 'shield-plus',
    'SPAWNER': 'box-select', 'NOTEBLOCK': 'box',
    'POTION': 'flask-conical', 'COMPASS': 'monitor', 'STICK': 'drumstick'
}

def clean_item_name(name):
    if not name:
        return ""
    return re.sub(r'<[^>]+>', '', str(name)).strip()

def extract_custom_texture(item_data):
    if 'Pack' in item_data and isinstance(item_data['Pack'], dict) and 'texture' in item_data['Pack']:
        raw = item_data['Pack']['texture']
        path_part = raw.split(':', 1)[1] if ':' in raw else raw
        
        if not path_part.endswith('.png'):
            path_part += '.png'
        return f"assets/textures/{path_part}"
    return ""

def extract_custom_model(item_data):
    model_raw = None
    
    if 'Pack' in item_data and isinstance(item_data['Pack'], dict) and 'model' in item_data['Pack']:
        model_raw = item_data['Pack']['model']
    
    elif 'Components' in item_data:
        comps = item_data['Components']
        if 'item_model' in comps:
            model_raw = comps['item_model']
        elif 'parent_model' in comps:
            model_raw = comps['parent_model']

    if model_raw:
        clean_path = model_raw.split(':', 1)[1] if ':' in model_raw else model_raw
        
        if '/' in clean_path:
            final_path = f"assets/models/{clean_path}"
        else:
            final_path = f"assets/models/item/{clean_path}"

        if not final_path.endswith('.json'):
            final_path += '.json'
            
        return final_path

    return ""

def get_model_details(model_path):
    texture_res = ""
    parent_res = ""

    if not model_path or not os.path.exists(model_path):
        return "", ""

    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            model_json = json.load(f)
        
        if 'parent' in model_json:
            raw_parent = model_json['parent']
            clean_parent = raw_parent.split(':', 1)[1] if ':' in raw_parent else raw_parent
            
            parent_res = f"assets/models/{clean_parent}"
            if not parent_res.endswith('.json'):
                parent_res += ".json"

        textures = model_json.get('textures', {})
        raw_texture = textures.get('0')
        
        if not raw_texture:
            raw_texture = textures.get('layer0')
            
        if raw_texture and isinstance(raw_texture, str):
            if not raw_texture.startswith('#'):
                clean_tex = raw_texture.split(':', 1)[1] if ':' in raw_texture else raw_texture
                texture_res = f"assets/textures/{clean_tex}"
                if not texture_res.endswith('.png'):
                    texture_res += ".png"

    except Exception as e:
        print(f"Error reading model {model_path}: {e}")

    return texture_res, parent_res

def clean_technical_tags(text):
    text = re.sub(r'<shift:[^>]+>', '', text)
    text = re.sub(r'<glyph:[^>]+>', '', text)
    return text

def extract_glyph_tags_from_list(lore_lines):
    tags = set()
    full_text = str(lore_lines)
    matches = re.findall(r'<glyph:(tag_[a-zA-Z0-9_]+)(?::[^>]+)?>', full_text)
    for m in matches:
        if 'tag_line' in m: continue
        tags.add(m)
    return list(tags)

def parse_lore_line_to_html(line):
    if not line or not isinstance(line, str):
        return None
    
    clean_line = clean_technical_tags(line)
    if len(line) > 0 and not clean_line.strip(): 
         return None

    parts = re.split(r'(</?#[0-9a-fA-F]{6}>|</?[a-zA-Z_]+>)', clean_line)
    
    html_parts = []
    base_color = "gray"
    current_color = None
    is_italic = False
    first_color_found = False

    for part in parts:
        if not part: continue
        
        is_tag = False
        lower_part = part.lower()
        
        hex_match = re.match(r'^</?(#[0-9a-fA-F]{6})>$', lower_part)
        name_match = re.match(r'^</?([a-z_]+)>$', lower_part)

        if hex_match:
            is_tag = True
            if part.startswith('</'):
                current_color = None 
            else:
                color = hex_match.group(1)
                current_color = color
                if not first_color_found:
                    base_color = color
                    first_color_found = True

        elif name_match:
            is_tag = True
            tag_name = name_match.group(1)
            if tag_name == 'italic':
                is_italic = not part.startswith('</')
            elif tag_name in COLOR_MAP:
                if part.startswith('</'):
                    current_color = None
                else:
                    color = COLOR_MAP[tag_name]
                    current_color = color
                    if not first_color_found:
                        base_color = color
                        first_color_found = True
        
        if not is_tag:
            safe_text = part.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            style = []
            if current_color: style.append(f"color: {current_color}")
            if is_italic: style.append("font-style: italic")
            
            if style:
                html_parts.append(f'<span style="{"; ".join(style)}">{safe_text}</span>')
            else:
                html_parts.append(safe_text)

    final_html = "".join(html_parts)
    return { "text": final_html, "color": base_color, "italic": False }

def get_description(lore_parsed):
    desc_lines = []
    for line in lore_parsed:
        raw_text = re.sub(r'<[^>]+>', '', line['text'])
        if (raw_text.strip() 
            and not raw_text.startswith('◆') 
            and not raw_text.startswith('Уровень:') 
            and not raw_text.startswith('Владелец:') 
            and not raw_text.startswith('Информация')
            and not raw_text.startswith('Заметка')):
            
            desc_lines.append(raw_text.strip())
            if len(desc_lines) >= 3: break
    return " ".join(desc_lines) if desc_lines else ""

def get_mechanics(item_data):
    mechs = {}
    if 'Components' in item_data:
        comps = item_data['Components']
        if 'food' in comps:
            food = comps['food']
            if 'nutrition' in food: mechs['Питательность'] = f"{food['nutrition']} ед."
            if 'saturation' in food: mechs['Насыщение'] = f"{food['saturation']} ед."
        
        if 'consumable' in comps:
            cons = comps['consumable']
            effects_list = []
            raw_eff = cons.get('effects', {})
            apply_eff = raw_eff.get('APPLY_EFFECTS', {}) if isinstance(raw_eff, dict) else {}
            if not apply_eff and isinstance(raw_eff, dict) and raw_eff and 'duration' not in raw_eff:
                 apply_eff = raw_eff

            if isinstance(apply_eff, dict):
                for eff_name, eff_data in apply_eff.items():
                    if eff_name == 'APPLY_EFFECTS': continue
                    dur = eff_data.get('duration', 0)
                    amp = eff_data.get('amplifier', 0) + 1
                    effects_list.append(f"{eff_name.capitalize()} {amp} ({dur}s)")
            
            if effects_list:
                mechs['Эффект'] = ", ".join(effects_list)

    if 'Mechanics' in item_data and 'backpack' in item_data['Mechanics']:
        rows = item_data['Mechanics']['backpack'].get('rows', 1)
        mechs['Рюкзак'] = f"{rows} ряд(а) ({rows*9} слотов)"
        mechs['Совместимость'] = "Нельзя положить шалкеры и мешки"

    return mechs

def process_files(global_storage):
    if not os.path.exists(NEXO_DIR):
        print(f"Dir {NEXO_DIR} not found")
        return

    files = [f for f in os.listdir(NEXO_DIR) if f.endswith('.yml') or f.endswith('.yaml')]
    
    for filename in files:
        filepath = os.path.join(NEXO_DIR, filename)
        print(f"Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error reading {filename}: {e}")
                continue

        if not data: continue

        for item_id, item_data in data.items():
            if not isinstance(item_data, dict) or 'itemname' not in item_data: continue

            raw_lore = item_data.get('lore', [])
            glyph_tags = extract_glyph_tags_from_list(raw_lore)
            
            categories = []
            for tag in glyph_tags:
                if tag in TAG_TO_CATEGORY:
                    categories.append(TAG_TO_CATEGORY[tag])
            
            if not categories:
                if 'block' in filename: categories = ['blocks']
                elif 'food' in filename: categories = ['food']
                else: categories = ['misc']

            parsed_lore = []
            for line in raw_lore:
                parsed_line = parse_lore_line_to_html(line)
                if parsed_line:
                    parsed_lore.append(parsed_line)

            custom_texture = extract_custom_texture(item_data)
            custom_model = extract_custom_model(item_data)
            
            model_texture = ""
            parent_model = ""
            if custom_model:
                model_texture, parent_model = get_model_details(custom_model)

            raw_name = item_data.get('itemname', item_id)
            clean_name = clean_item_name(raw_name)

            item_obj = {
                "id": item_id,
                "name": clean_name,
                "type": item_data.get('material', 'UNKNOWN'),
                "description": get_description(parsed_lore),
                "rarity": item_data.get('Components', {}).get('rarity', 'COMMON'),
                "icon": ICON_MAP.get(item_data.get('material'), 'box'),
                "customIcon": custom_texture,
                "customModel": custom_model,
                "customModelTexture": model_texture,
                "parentmodel": parent_model,
                "lore": parsed_lore,
                "mechanics": get_mechanics(item_data),
                "glyph_tags": glyph_tags,
                "image": "",
                "Pack": item_data.get('Pack', {}),
                "Components": item_data.get('Components', {})
            }

            for cat in categories:
                if cat in global_storage:
                    global_storage[cat].append(item_obj)
                elif 'misc' in global_storage:
                    global_storage['misc'].append(item_obj)

def main():
    final_json = {cat: [] for cat in REQUIRED_CATEGORIES}
    process_files(final_json)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    print(f"Generated {OUTPUT_FILE} ({len(final_json)} categories)")

if __name__ == "__main__":
    main()