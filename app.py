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

class SearchRequest(BaseModel):
    query: str  # 搜索关键词
    search_type: str = "name"  # 搜索类型：name, school, contest, province
    limit: int = 50  # 返回结果数量限制

class RankingRequest(BaseModel):
    score_type: str = "oierdb"  # 评分类型：oierdb, ccf
    limit: int = 100  # 返回结果数量
    offset: int = 0  # 分页偏移量

class AwardInfo(BaseModel):
    name: str
    gender: str
    enroll_middle: int
    oierdb_score: float
    ccf_score: float
    ccf_level: int
    records: List[Dict[str, Any]]

class SearchResult(BaseModel):
    total: int
    results: List[AwardInfo]

class ContestInfo(BaseModel):
    name: str
    type: str
    year: int
    contestants_count: int

class SchoolInfo(BaseModel):
    name: str
    province: str
    city: str
    student_count: int

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
    """批量查询选手信息API"""
    # 输入验证
    if not request.names or len(request.names) == 0:
        raise HTTPException(status_code=400, detail="names列表不能为空")
    
    if len(request.names) > 100:
        raise HTTPException(status_code=400, detail="单次查询名单不能超过100个")
    
    # 确保数据已加载
    try:
        load_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据加载失败: {str(e)}")

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

@app.post("/search", response_model=SearchResult)
async def search_oiers(request: SearchRequest):
    """智能搜索API - 支持按姓名、学校、比赛、省份搜索"""
    load_data()
    
    from oier import OIer
    from school import School
    from contest import Contest
    
    results = []
    query = request.query.lower().strip()
    
    if request.search_type == "name":
        # 按姓名搜索（支持模糊匹配）
        for oier in OIer.get_all():
            if query in oier.name.lower():
                results.append(oier)
                if len(results) >= request.limit:
                    break
    
    elif request.search_type == "school":
        # 按学校搜索
        for oier in OIer.get_all():
            for record in oier.records:
                if record.school and query in record.school.name.lower():
                    results.append(oier)
                    break
            if len(results) >= request.limit:
                break
    
    elif request.search_type == "contest":
        # 按比赛搜索
        for oier in OIer.get_all():
            for record in oier.records:
                if (query in record.contest.name.lower() or 
                    query in record.contest.type.lower()):
                    results.append(oier)
                    break
            if len(results) >= request.limit:
                break
    
    elif request.search_type == "province":
        # 按省份搜索
        for oier in OIer.get_all():
            for record in oier.records:
                if record.province and query in record.province.lower():
                    results.append(oier)
                    break
            if len(results) >= request.limit:
                break
    
    # 转换为AwardInfo格式
    award_infos = []
    for oier in results:
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
        
        award_infos.append(
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
    
    return SearchResult(total=len(award_infos), results=award_infos)

@app.post("/ranking", response_model=List[AwardInfo])
async def get_ranking(request: RankingRequest):
    """获取选手排行榜API"""
    load_data()
    
    from oier import OIer
    
    all_oiers = OIer.get_all()
    
    # 根据评分类型排序
    if request.score_type == "oierdb":
        sorted_oiers = sorted(all_oiers, 
                            key=lambda x: getattr(x, 'oierdb_score', 0), 
                            reverse=True)
    elif request.score_type == "ccf":
        sorted_oiers = sorted(all_oiers, 
                            key=lambda x: getattr(x, 'ccf_score', 0), 
                            reverse=True)
    else:
        raise HTTPException(status_code=400, detail="Invalid score_type")
    
    # 分页
    start_idx = request.offset
    end_idx = min(start_idx + request.limit, len(sorted_oiers))
    page_oiers = sorted_oiers[start_idx:end_idx]
    
    # 转换为AwardInfo格式
    results = []
    for oier in page_oiers:
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

@app.get("/contests", response_model=List[ContestInfo])
async def get_contests():
    """获取所有比赛信息API"""
    load_data()
    
    from contest import Contest
    
    contests = Contest.__all_contests_list__
    contest_infos = []
    
    for contest in contests:
        contest_infos.append(
            ContestInfo(
                name=contest.name,
                type=contest.type,
                year=contest.year,
                contestants_count=contest.n_contestants()
            )
        )
    
    return contest_infos

@app.get("/schools", response_model=List[SchoolInfo])
async def get_schools():
    """获取所有学校信息API"""
    load_data()
    
    from school import School
    from oier import OIer
    
    schools = School.get_all()
    school_infos = []
    
    # 统计每个学校的学生数量
    school_student_count = {}
    for oier in OIer.get_all():
        for record in oier.records:
            if record.school:
                school_name = record.school.name
                if school_name not in school_student_count:
                    school_student_count[school_name] = set()
                school_student_count[school_name].add(oier.name)
    
    for school in schools:
        student_count = len(school_student_count.get(school.name, set()))
        school_infos.append(
            SchoolInfo(
                name=school.name,
                province=school.province,
                city=school.city,
                student_count=student_count
            )
        )
    
    return school_infos

@app.get("/stats")
async def get_statistics():
    """获取系统统计信息API"""
    load_data()
    
    from oier import OIer
    from contest import Contest
    from school import School
    
    # 基础统计
    total_oiers = len(OIer.get_all())
    total_contests = len(Contest.__all_contests_list__)
    total_schools = len(School.get_all())
    
    # 按性别统计
    gender_stats = {"男": 0, "女": 0, "未知": 0}
    for oier in OIer.get_all():
        if oier.gender == 1:
            gender_stats["男"] += 1
        elif oier.gender == -1:
            gender_stats["女"] += 1
        else:
            gender_stats["未知"] += 1
    
    # 按省份统计
    province_stats = {}
    for oier in OIer.get_all():
        for record in oier.records:
            if record.province:
                province_stats[record.province] = province_stats.get(record.province, 0) + 1
                break  # 每个选手只统计一次
    
    # 按比赛类型统计
    contest_type_stats = {}
    for contest in Contest.__all_contests_list__:
        contest_type = contest.type
        if contest_type not in contest_type_stats:
            contest_type_stats[contest_type] = {"count": 0, "total_contestants": 0}
        contest_type_stats[contest_type]["count"] += 1
        contest_type_stats[contest_type]["total_contestants"] += contest.n_contestants()
    
    return {
        "basic_stats": {
            "total_oiers": total_oiers,
            "total_contests": total_contests,
            "total_schools": total_schools
        },
        "gender_distribution": gender_stats,
        "province_distribution": dict(sorted(province_stats.items(), key=lambda x: x[1], reverse=True)[:10]),  # 前10个省份
        "contest_type_stats": contest_type_stats
    }