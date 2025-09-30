# OIerDb Query API 使用文档

这是一个基于 FastAPI 构建的 OI 选手信息查询 API，提供了丰富的查询功能。

## 🚀 快速开始

### 启动服务器

```bash
python run.py
```

服务器将在 `http://localhost:8000` 启动。

### 访问 API 文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📋 API 端点列表

### 1. 批量查询选手信息

**POST** `/query`

根据选手姓名列表批量查询获奖信息。

**请求体:**
```json
{
    "names": ["张三", "李四", "王五"]
}
```

**响应:**
```json
[
    {
        "name": "张三",
        "gender": "男",
        "enroll_middle": 2010,
        "oierdb_score": 1250.5,
        "ccf_score": 890.2,
        "ccf_level": 8,
        "records": [
            {
                "contest_name": "第20届全国青少年信息学奥林匹克联赛",
                "contest_type": "NOIP",
                "year": 2014,
                "score": 350,
                "rank": 15,
                "level": "一等奖",
                "province": "北京",
                "school": "北京四中"
            }
        ]
    }
]
```

### 2. 智能搜索

**POST** `/search`

支持按姓名、学校、比赛、省份等多种方式搜索。

**请求体:**
```json
{
    "query": "北京四中",
    "search_type": "school",
    "limit": 20
}
```

**参数说明:**
- `query`: 搜索关键词
- `search_type`: 搜索类型，可选值：
  - `"name"`: 按姓名搜索（支持模糊匹配）
  - `"school"`: 按学校搜索
  - `"contest"`: 按比赛搜索
  - `"province"`: 按省份搜索
- `limit`: 返回结果数量限制（默认50，最大100）

**响应:**
```json
{
    "total": 15,
    "results": [
        {
            "name": "张三",
            // ... 其他选手信息
        }
    ]
}
```

### 3. 排行榜

**POST** `/ranking`

获取选手排行榜，支持分页。

**请求体:**
```json
{
    "score_type": "oierdb",
    "limit": 50,
    "offset": 0
}
```

**参数说明:**
- `score_type`: 评分类型
  - `"oierdb"`: 按 OIerDb 评分排序
  - `"ccf"`: 按 CCF 评分排序
- `limit`: 每页数量（默认100）
- `offset`: 分页偏移量（默认0）

### 4. 比赛信息

**GET** `/contests`

获取所有比赛信息。

**响应:**
```json
[
    {
        "name": "第20届全国青少年信息学奥林匹克联赛",
        "type": "NOIP",
        "year": 2014,
        "contestants_count": 1500
    }
]
```

### 5. 学校信息

**GET** `/schools`

获取所有学校信息及学生统计。

**响应:**
```json
[
    {
        "name": "北京四中",
        "province": "北京",
        "city": "北京市",
        "student_count": 25
    }
]
```

### 6. 统计信息

**GET** `/stats`

获取系统整体统计信息。

**响应:**
```json
{
    "basic_stats": {
        "total_oiers": 15420,
        "total_contests": 850,
        "total_schools": 3200
    },
    "gender_distribution": {
        "男": 12500,
        "女": 2800,
        "未知": 120
    },
    "province_distribution": {
        "北京": 1250,
        "上海": 980,
        "广东": 1890
    },
    "contest_type_stats": {
        "NOIP": {
            "count": 25,
            "total_contestants": 18500
        },
        "NOI": {
            "count": 15,
            "total_contestants": 2500
        }
    }
}
```

## 🔧 使用示例

### Python 示例

```python
import requests
import json

# 批量查询
def query_students(names):
    url = "http://localhost:8000/query"
    data = {"names": names}
    response = requests.post(url, json=data)
    return response.json()

# 智能搜索
def search_by_school(school_name):
    url = "http://localhost:8000/search"
    data = {
        "query": school_name,
        "search_type": "school",
        "limit": 50
    }
    response = requests.post(url, json=data)
    return response.json()

# 获取排行榜
def get_top_students(limit=10):
    url = "http://localhost:8000/ranking"
    data = {
        "score_type": "oierdb",
        "limit": limit,
        "offset": 0
    }
    response = requests.post(url, json=data)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 查询特定学生
    students = query_students(["张三", "李四"])
    print(json.dumps(students, ensure_ascii=False, indent=2))
    
    # 搜索北京四中的学生
    school_students = search_by_school("北京四中")
    print(f"找到 {school_students['total']} 名学生")
    
    # 获取前10名
    top10 = get_top_students(10)
    for i, student in enumerate(top10, 1):
        print(f"{i}. {student['name']} - OIerDb评分: {student['oierdb_score']}")
```

### JavaScript (前端) 示例

```javascript
// 批量查询
async function queryStudents(names) {
    const response = await fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ names })
    });
    return await response.json();
}

// 智能搜索
async function searchStudents(query, searchType = 'name', limit = 50) {
    const response = await fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query,
            search_type: searchType,
            limit
        })
    });
    return await response.json();
}

// 获取统计信息
async function getStatistics() {
    const response = await fetch('/stats');
    return await response.json();
}

// 使用示例
document.addEventListener('DOMContentLoaded', async () => {
    // 获取系统统计
    const stats = await getStatistics();
    console.log('系统统计:', stats);
    
    // 搜索包含"中学"的学校
    const schoolResults = await searchStudents('中学', 'school', 20);
    console.log(`找到 ${schoolResults.total} 个结果`);
});
```

### cURL 示例

```bash
# 批量查询
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"names": ["张三", "李四"]}'

# 智能搜索
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "北京", "search_type": "province", "limit": 10}'

# 获取排行榜
curl -X POST "http://localhost:8000/ranking" \
     -H "Content-Type: application/json" \
     -d '{"score_type": "oierdb", "limit": 5, "offset": 0}'

# 获取比赛信息
curl -X GET "http://localhost:8000/contests"

# 获取统计信息
curl -X GET "http://localhost:8000/stats"
```

## ⚠️ 注意事项

1. **请求限制**: 单次批量查询最多支持100个姓名
2. **搜索限制**: 搜索结果最多返回100条记录
3. **数据更新**: 系统启动时会自动加载数据，如需更新数据请重启服务
4. **错误处理**: 所有API都包含详细的错误信息，请检查HTTP状态码和响应体

## 🚀 性能优化建议

1. **批量查询**: 尽量使用批量查询API而不是多次单独查询
2. **合理分页**: 使用排行榜API时建议使用分页避免一次性加载过多数据
3. **缓存结果**: 对于不经常变化的数据（如学校信息、比赛信息）建议在客户端缓存
4. **精确搜索**: 在搜索时尽量使用精确的关键词以提高查询效率

## 🤝 支持与反馈

如有任何问题或建议，请通过以下方式联系：

- GitHub Issues: [项目地址]
- 邮箱: [联系邮箱]

---

*最后更新: 2025年9月30日*