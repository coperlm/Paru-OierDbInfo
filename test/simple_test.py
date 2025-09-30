#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
简单的API测试脚本
"""

import requests
import json

def test_query_api():
    """测试批量查询API"""
    print("测试批量查询API...")
    
    url = "http://localhost:8000/query"
    data = {"names": ["张宇", "李明"]}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 成功查询到 {len(results)} 个选手")
            for result in results:
                print(f"  - {result['name']}: OIerDb评分 {result['oierdb_score']}, 记录数 {len(result['records'])}")
        else:
            print(f"❌ 查询失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_search_api():
    """测试搜索API"""
    print("\n测试搜索API...")
    
    url = "http://localhost:8000/search"
    data = {
        "query": "张",
        "search_type": "name",
        "limit": 5
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 搜索成功，找到 {results['total']} 个结果")
            for result in results['results'][:3]:  # 只显示前3个
                print(f"  - {result['name']}: OIerDb评分 {result['oierdb_score']}")
        else:
            print(f"❌ 搜索失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_stats_api():
    """测试统计API"""
    print("\n测试统计API...")
    
    url = "http://localhost:8000/stats"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            stats = response.json()
            print("✅ 统计信息获取成功:")
            print(f"  - 总选手数: {stats['basic_stats']['total_oiers']}")
            print(f"  - 总比赛数: {stats['basic_stats']['total_contests']}")
            print(f"  - 总学校数: {stats['basic_stats']['total_schools']}")
        else:
            print(f"❌ 统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    print("🚀 开始测试OIerDb API核心功能\n")
    
    test_query_api()
    test_search_api() 
    test_stats_api()
    
    print("\n✨ 测试完成！")