from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os

app = FastAPI(title="OIerDb Query API", description="批量查询选手获奖信息API")

# 添加CORS中间件以允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    names: List[str]  # 选手姓名列表

class AwardInfo(BaseModel):
    name: str
    gender: str
    enroll_middle: int
    oierdb_score: float
    ccf_score: float
    ccf_level: int
    records: List[Dict[str, Any]]

# 全局变量存储数据
data_loaded = False

def load_contests():
    """加载比赛数据"""
    from contest import Contest
    with open("static/contests.json", "r", encoding="utf-8") as f:
        contests_data = json.load(f)
    for contest_data in contests_data:
        Contest.create(contest_data)

def load_schools():
    """加载学校数据"""
    from school import School
    with open("data/school.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            province, city, name = parts[0], parts[1], parts[2]
            aliases = parts[3:] if len(parts) > 3 else []
            School.create(name, province, city, aliases)

def parse_compressed_record(record_str, oier):
    """解析压缩格式的记录"""
    from contest import Contest
    from school import School
    from record import Record
    import util
    
    parts = record_str.split(":")
    if len(parts) < 6:
        return None

    # 压缩格式含义：contest_id:school_id:score:rank:province_idx:award_level_idx
    contest_id = int(parts[0])
    school_id = int(parts[1])
    score = None if parts[2] == "" else float(parts[2])
    rank = int(parts[3]) if parts[3] != "" else 0
    province_field = parts[4]
    level_field = parts[5]

    # 恢复 contest 对象
    contest = next((c for c in Contest.__all_contests_list__ if c.id == contest_id), None)

    # 恢复 school 对象
    school = next((s for s in School.__all_school_list__ if s.id == school_id), None)

    # province_field 可能是索引或原始名称，尝试转换
    try:
        province = util.provinces[int(province_field)] if province_field.isnumeric() else province_field
    except Exception:
        province = province_field

    # level_field 可能是索引或名称
    try:
        level = util.award_levels[int(level_field)] if level_field.isnumeric() else level_field
    except Exception:
        level = level_field

    if contest:
        record = Record(oier, contest, score, rank, level, "", school, province, oier.gender)
        oier.add_record(record)

def load_oiers():
    """加载选手数据"""
    from oier import OIer
    with open("dist/result.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 9:
                continue
            
            uid = int(parts[0])
            initials = parts[1]
            name = parts[2]
            gender = "男" if parts[3] == "1" else "女"
            enroll_middle = int(parts[4])
            oierdb_score = float(parts[5])
            ccf_score = float(parts[6])
            ccf_level = int(parts[7])
            records_str = parts[8]
            
            oier = OIer.of(name, f"{name}({initials})", gender, enroll_middle, uid)
            oier.oierdb_score = oierdb_score
            oier.ccf_score = ccf_score
            oier.ccf_level = ccf_level
            
            # 解析记录
            if records_str:
                for record_str in records_str.split("/"):
                    parse_compressed_record(record_str, oier)

def load_data():
    global data_loaded
    if not data_loaded:
        load_contests()
        load_schools()
        load_oiers()
        from oier import OIer
        OIer.sort_by_score()
        data_loaded = True

@app.on_event("startup")
async def startup_event():
    # 启动时加载数据，确保查询可用
    load_data()

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/query", response_model=List[AwardInfo])
async def query_awards(request: QueryRequest):
    # 确保数据已加载
    load_data()

    from oier import OIer

    results = []
    # 对每个请求中的姓名，进行精确匹配（考虑多个同名情况）
    for name in request.names:
        for oier in OIer.get_all():
            if oier.name == name:
                records_out = []
                for rec in oier.records:
                    records_out.append({
                        "contest_name": rec.contest.name,
                        "contest_type": rec.contest.type,
                        "year": rec.contest.year,
                        "score": rec.score,
                        "rank": rec.rank,
                        "level": rec.level,
                        "province": rec.province,
                        "school": rec.school.name if rec.school else None,
                    })
                results.append(
                    AwardInfo(
                        name=oier.name,
                        gender="男" if oier.gender == 1 else ("女" if oier.gender == -1 else ""),
                        enroll_middle=oier.enroll_middle if oier.enroll_middle else 0,
                        oierdb_score=float(oier.oierdb_score) if hasattr(oier, "oierdb_score") else 0.0,
                        ccf_score=float(oier.ccf_score) if hasattr(oier, "ccf_score") else 0.0,
                        ccf_level=int(oier.ccf_level) if hasattr(oier, "ccf_level") else 0,
                        records=records_out,
                    )
                )

    return results