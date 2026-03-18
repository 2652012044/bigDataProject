"""
提取 XML 中所有有用的信息
"""
import xml.etree.ElementTree as ET

xml_file = "hierarchy_debug.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

print("=" * 60)
print("所有有 text 属性的组件:")
print("=" * 60)

count = 0
for node in root.iter('node'):
    text = node.get('text', '')
    resource_id = node.get('resource-id', '')
    cls = node.get('class', '')
    clickable = node.get('clickable', '')
    bounds = node.get('bounds', '')
    
    if text and text.strip():
        print(f"\n{count}. Text: '{text}'")
        print(f"   Resource ID: {resource_id}")
        print(f"   Class: {cls}")
        print(f"   Clickable: {clickable}")
        print(f"   Bounds: {bounds}")
        count += 1

print("\n" + "=" * 60)
print("所有 resource-id 包含 'search' 的组件:")
print("=" * 60)

for node in root.iter('node'):
    resource_id = node.get('resource-id', '')
    if 'search' in resource_id.lower():
        print(f"\n✓ Found: {resource_id}")
        print(f"   Text: {node.get('text', '')}")
        print(f"   Class: {node.get('class', '')}")
        print(f"   Bounds: {node.get('bounds', '')}")

print("\n" + "=" * 60)
print("顶部区域 (y < 202) 的所有元素:")
print("=" * 60)

for node in root.iter('node'):
    bounds = node.get('bounds', '')
    if bounds:
        # 解析 bounds [x1,y1][x2,y2]
        try:
            parts = bounds.replace('[', '').replace(']', '').split(',')
            if len(parts) >= 2:
                y1 = int(parts[1])
                y2 = int(parts[3])
                
                if y1 < 202:  # 顶部
                    text = node.get('text', '')
                    resource_id = node.get('resource-id', '')
                    cls = node.get('class', '')
                    
                    print(f"\nBounds: {bounds}")
                    print(f"  Text: '{text}'")
                    print(f"  Resource ID: {resource_id}")
                    print(f"  Class: {cls}")
        except:
            pass
