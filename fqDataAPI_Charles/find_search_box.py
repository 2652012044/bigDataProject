"""
查找搜索框的详细信息
"""
import xml.etree.ElementTree as ET

xml_file = "hierarchy_debug.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

print("=" * 60)
print("分析顶部搜索框相关组件:")
print("=" * 60)

target_text = "病娇+卑微+占有欲超强"

for node in root.iter('node'):
    text = node.get('text', '')
    if target_text in text:
        # 找到了，现在获取其父级信息
        print(f"\n✓ 找到目标组件!")
        print(f"  Text: {text}")
        print(f"  Resource ID: {node.get('resource-id', 'N/A')}")
        print(f"  Class: {node.get('class', 'N/A')}")
        print(f"  Bounds: {node.get('bounds', 'N/A')}")
        print(f"  Clickable: {node.get('clickable', 'N/A')}")
        print(f"  Content Desc: {node.get('content-desc', 'N/A')}")

print("\n" + "=" * 60)
print("查找所有顶部 (y < 100) 可点击的组件:")
print("=" * 60)

for node in root.iter('node'):
    bounds = node.get('bounds', '')
    clickable = node.get('clickable', '')
    
    if bounds:
        try:
            parts = bounds.replace('[', '').replace(']', '').split(',')
            if len(parts) >= 4:
                y1 = int(parts[1])
                if y1 < 100 and clickable == 'true':
                    text = node.get('text', '')
                    resource_id = node.get('resource-id', '')
                    cls = node.get('class', '')
                    
                    print(f"\n✓ 可点击组件:")
                    print(f"  Text: '{text}'")
                    print(f"  Resource ID: {resource_id}")
                    print(f"  Class: {cls}")
                    print(f"  Bounds: {bounds}")
        except:
            pass

print("\n" + "=" * 60)
print("所有包含 'text' 的顶部组件（无论是否可点击）:")
print("=" * 60)

for node in root.iter('node'):
    bounds = node.get('bounds', '')
    text = node.get('text', '')
    
    if bounds and text:
        try:
            parts = bounds.replace('[', '').replace(']', '').split(',')
            if len(parts) >= 4:
                y1 = int(parts[1])
                if y1 < 150:  # 顶部 150 像素
                    resource_id = node.get('resource-id', '')
                    cls = node.get('class', '')
                    clickable = node.get('clickable', '')
                    
                    print(f"\nText: '{text}'")
                    print(f"  Resource ID: {resource_id}")
                    print(f"  Class: {cls}")
                    print(f"  Clickable: {clickable}")
                    print(f"  Bounds: {bounds}")
        except:
            pass
