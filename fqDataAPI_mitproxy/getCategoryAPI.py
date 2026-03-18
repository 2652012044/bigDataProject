"""
番茄小说分类API数据获取脚本
直接请求API获取分类数据，无需UI自动化
"""

import requests
import json
import argparse
import logging
from pathlib import Path


def setup_logger():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def get_category_data(gender=1, save_to_file=True):
    """
    获取分类API数据
    
    Args:
        gender: 1=男生, 2=女生
        save_to_file: 是否保存到文件
    
    Returns:
        dict: API响应数据
    """
    logger = setup_logger()
    
    # API地址（需要根据Charles中看到的实际version替换）
    # 常见版本: v1, v2, v999 等
    base_url = "https://api5-normal-sinfonlineb.fqnovel.com"
    
    # 尝试常见的版本号
    versions = ["999", "1", "2", "100"]
    
    # 从Charles中复制的请求头（根据实际情况修改）
    headers = {
        "User-Agent": "okhttp/3.12.4.200_99_21_33_12",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    for version in versions:
        url = f"{base_url}/reading/bookapi/new_category/front/v{version}/"
        
        # 查询参数（根据Charles中的实际参数调整）
        params = {
            "gender": gender,
            "iid": "",  # 设备ID，从Charles中获取
            "device_id": "",  # 设备ID，从Charles中获取
            "version_code": "",  # App版本，从Charles中获取
        }
        
        try:
            logger.info(f"正在尝试版本: v{version}")
            logger.info(f"请求URL: {url}")
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ 请求成功! 版本 v{version}")
                data = response.json()
                
                if save_to_file:
                    # 保存到文件
                    output_dir = Path("data")
                    output_dir.mkdir(exist_ok=True)
                    
                    filename = output_dir / f"category_gender_{gender}_v{version}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"数据已保存到: {filename}")
                
                # 打印基本信息
                if 'data' in data:
                    tabs = data['data'].get('TabList', [])
                    logger.info(f"共有 {len(tabs)} 个标签页")
                    
                    for tab in tabs:
                        tab_name = tab.get('Name', 'Unknown')
                        groups = tab.get('Groups', [])
                        total_categories = sum(len(g.get('Items', [])) for g in groups)
                        logger.info(f"  - {tab_name}: {len(groups)} 个分组, {total_categories} 个分类")
                
                return data
            else:
                logger.warning(f"✗ 版本 v{version} 失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"✗ 版本 v{version} 出错: {e}")
            continue
    
    logger.error("所有版本号尝试失败")
    return None


def extract_category_mapping(data, gender=1):
    """
    从API数据中提取 category_id 和 name 的映射
    
    Args:
        data: API响应数据
        gender: 性别标识
        
    Returns:
        list: 分类映射列表
    """
    logger = setup_logger()
    mapping = []
    
    if not data or 'data' not in data:
        logger.error("无效的数据格式")
        return mapping
    
    tabs = data['data'].get('TabList', [])
    
    for tab in tabs:
        tab_name = tab.get('Name', '')
        groups = tab.get('Groups', [])
        
        for group in groups:
            group_name = group.get('Name', '')
            items = group.get('Items', [])
            
            for item in items:
                category_id = item.get('category_id', '')
                name = item.get('name', '')
                
                mapping.append({
                    'category_id': category_id,
                    'name': name,
                    'tab': tab_name,
                    'group': group_name,
                    'gender': gender
                })
    
    logger.info(f"共提取 {len(mapping)} 个分类映射")
    
    # 保存映射
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    filename = output_dir / f"category_mapping_gender_{gender}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    logger.info(f"映射已保存到: {filename}")
    
    return mapping


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='获取番茄小说分类API数据')
    parser.add_argument('--gender', type=int, default=1, choices=[1, 2],
                        help='性别: 1=男生, 2=女生 (默认: 1)')
    parser.add_argument('--extract-mapping', action='store_true',
                        help='提取分类ID映射')
    
    args = parser.parse_args()
    
    logger = setup_logger()
    logger.info("=" * 50)
    logger.info("番茄小说分类API数据获取")
    logger.info("=" * 50)
    
    # 获取数据
    data = get_category_data(gender=args.gender)
    
    if data and args.extract_mapping:
        # 提取映射
        extract_category_mapping(data, gender=args.gender)
    
    logger.info("完成!")


if __name__ == "__main__":
    main()
