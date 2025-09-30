#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
OIerDb API 测试脚本
用于测试各个API端点的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoint(name, method, endpoint, data=None):
    """测试API端点"""
    print(f"\n🧪 测试 {name}")
    print(f"📍 {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应的Content-Type来判断如何处理
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                # JSON响应
                result = response.json()
                if isinstance(result, list):
                    print(f"✅ 成功 - 返回 {len(result)} 条记录")
                    if len(result) > 0:
                        print(f"📝 第一条记录预览: {json.dumps(result[0] if isinstance(result[0], dict) else str(result[0]), ensure_ascii=False)[:200]}...")
                elif isinstance(result, dict):
                    if 'total' in result:
                        print(f"✅ 成功 - 总计 {result['total']} 条记录")
                    else:
                        print(f"✅ 成功 - 返回数据: {json.dumps(result, ensure_ascii=False)[:200]}...")
                else:
                    print(f"✅ 成功 - 返回: {str(result)[:200]}...")
            elif 'text/html' in content_type or endpoint == '/':
                # HTML响应（如主页）
                print(f"✅ 成功 - 返回HTML页面 (大小: {len(response.text)} 字符)")
            else:
                # 其他类型的响应
                try:
                    result = response.json()
                    if isinstance(result, list):
                        print(f"✅ 成功 - 返回 {len(result)} 条记录")
                        if len(result) > 0:
                            print(f"📝 第一条记录预览: {json.dumps(result[0] if isinstance(result[0], dict) else str(result[0]), ensure_ascii=False)[:200]}...")
                    elif isinstance(result, dict):
                        if 'total' in result:
                            print(f"✅ 成功 - 总计 {result['total']} 条记录")
                        else:
                            print(f"✅ 成功 - 返回数据: {json.dumps(result, ensure_ascii=False)[:200]}...")
                    else:
                        print(f"✅ 成功 - 返回: {str(result)[:200]}...")
                except json.JSONDecodeError:
                    print(f"✅ 成功 - 返回非JSON数据 (大小: {len(response.text)} 字符)")
        else:
            print(f"❌ 失败 - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务器已启动 (python run.py)")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始测试 OIerDb API")
    print("=" * 50)
    
    # 测试基础端点
    test_api_endpoint("主页", "GET", "/")
    
    # 测试统计信息
    test_api_endpoint("统计信息", "GET", "/stats")
    
    # 测试比赛信息
    test_api_endpoint("比赛信息", "GET", "/contests")
    
    # 测试学校信息  
    test_api_endpoint("学校信息", "GET", "/schools")
    
    # 测试批量查询 (使用常见姓名)
    test_api_endpoint("批量查询选手", "POST", "/query", {
        "names": ["张三", "李四", "王五", "赵六"]
    })
    
    # 测试智能搜索 - 按姓名
    test_api_endpoint("按姓名搜索", "POST", "/search", {
        "query": "张",
        "search_type": "name",
        "limit": 5
    })
    
    # 测试智能搜索 - 按学校
    test_api_endpoint("按学校搜索", "POST", "/search", {
        "query": "中学",
        "search_type": "school", 
        "limit": 10
    })
    
    # 测试智能搜索 - 按省份
    test_api_endpoint("按省份搜索", "POST", "/search", {
        "query": "北京",
        "search_type": "province",
        "limit": 8
    })
    
    # 测试智能搜索 - 按比赛
    test_api_endpoint("按比赛搜索", "POST", "/search", {
        "query": "NOIP",
        "search_type": "contest",
        "limit": 10
    })
    
    # 测试排行榜 - OIerDb评分
    test_api_endpoint("OIerDb评分排行榜", "POST", "/ranking", {
        "score_type": "oierdb",
        "limit": 10,
        "offset": 0
    })
    
    # 测试排行榜 - CCF评分
    test_api_endpoint("CCF评分排行榜", "POST", "/ranking", {
        "score_type": "ccf", 
        "limit": 5,
        "offset": 0
    })
    
    print("\n" + "=" * 50)
    print("✨ 测试完成！")

def test_error_handling():
    """测试错误处理"""
    print("\n🔧 测试错误处理")
    print("=" * 30)
    
    # 测试空的批量查询
    test_api_endpoint("空查询列表", "POST", "/query", {
        "names": []
    })
    
    # 测试过多的批量查询
    test_api_endpoint("超量查询", "POST", "/query", {
        "names": [f"测试用户{i}" for i in range(101)]
    })
    
    # 测试无效的评分类型
    test_api_endpoint("无效评分类型", "POST", "/ranking", {
        "score_type": "invalid",
        "limit": 10,
        "offset": 0
    })

def interactive_test():
    """交互式测试"""
    print("\n🎮 交互式测试模式")
    print("输入 'quit' 退出")
    
    while True:
        print("\n可用的测试:")
        print("1. 按姓名查询")
        print("2. 按学校搜索") 
        print("3. 获取排行榜")
        print("4. 获取统计信息")
        
        choice = input("\n请选择测试类型 (1-4) 或输入 'quit': ").strip()
        
        if choice.lower() == 'quit':
            break
            
        if choice == "1":
            names = input("请输入姓名 (用逗号分隔): ").strip()
            if names:
                name_list = [name.strip() for name in names.split(",")]
                test_api_endpoint("用户查询", "POST", "/query", {"names": name_list})
                
        elif choice == "2":
            school = input("请输入学校关键词: ").strip() 
            if school:
                test_api_endpoint("学校搜索", "POST", "/search", {
                    "query": school,
                    "search_type": "school",
                    "limit": 20
                })
                
        elif choice == "3":
            limit = input("请输入排行榜数量 (默认10): ").strip()
            limit = int(limit) if limit and limit.isdigit() else 10
            test_api_endpoint("排行榜", "POST", "/ranking", {
                "score_type": "oierdb",
                "limit": limit,
                "offset": 0
            })
            
        elif choice == "4":
            test_api_endpoint("统计信息", "GET", "/stats")
            
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "error":
            test_error_handling()
        elif sys.argv[1] == "interactive":
            interactive_test()
        else:
            print("用法:")
            print("  python test_api.py           # 运行所有测试")
            print("  python test_api.py error     # 测试错误处理")
            print("  python test_api.py interactive # 交互式测试")
    else:
        run_all_tests()
        
        # 询问是否进行交互式测试
        if input("\n是否进行交互式测试? (y/N): ").lower().startswith('y'):
            interactive_test()