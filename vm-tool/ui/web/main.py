"""FastAPI Web界面"""
from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.dal.database import get_db
from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService

app = FastAPI(
    title="VM-TOOL API",
    description="码表处理工具API",
    version="2.0.0"
)

# 配置模板
 templates = Jinja2Templates(directory="ui/web/templates")

# 配置静态文件
app.mount("/static", StaticFiles(directory="ui/web/static"), name="static")

# 数据模型
class WordBase(BaseModel):
    word: str
    code: Optional[str] = None
    weight: float = 1.0

class WordCreate(WordBase):
    pass

class WordUpdate(BaseModel):
    code: Optional[str] = None
    weight: Optional[float] = None

class WordResponse(WordBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class ImportResponse(BaseModel):
    added: int
    existing: int
    existing_words: List[str]

class StatsResponse(BaseModel):
    total_words: int
    average_word_length: float
    average_code_length: float
    code_conflict_rate: float
    weight_distribution: dict
    length_distribution: dict

# 路由
@app.get("/", response_class=HTMLResponse)
def read_root(request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/words", response_class=HTMLResponse)
def get_words(request, db: Session = Depends(get_db)):
    """词表页面"""
    dict_service = DictService(db)
    words = dict_service.get_all_words()
    return templates.TemplateResponse("words.html", {"request": request, "words": words})

@app.get("/stats", response_class=HTMLResponse)
def get_stats(request, db: Session = Depends(get_db)):
    """统计页面"""
    stats_service = StatsService(db)
    report = stats_service.generate_report()
    return templates.TemplateResponse("stats.html", {"request": request, "report": report})

@app.get("/import", response_class=HTMLResponse)
def import_page(request):
    """导入页面"""
    return templates.TemplateResponse("import.html", {"request": request})

# API路由
@app.get("/api/words", response_model=List[WordResponse])
def api_get_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取词表"""
    dict_service = DictService(db)
    words = dict_service.get_all_words(skip, limit)
    return words

@app.post("/api/words", response_model=WordResponse)
def api_add_word(word: WordCreate, db: Session = Depends(get_db)):
    """添加词条"""
    dict_service = DictService(db)
    try:
        result = dict_service.add_word(word.word, word.code, word.weight)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/words/{word}", response_model=WordResponse)
def api_get_word(word: str, db: Session = Depends(get_db)):
    """获取单个词条"""
    dict_service = DictService(db)
    result = dict_service.get_word(word)
    if not result:
        raise HTTPException(status_code=404, detail="词条不存在")
    return result

@app.put("/api/words/{word}", response_model=WordResponse)
def api_update_word(word: str, word_update: WordUpdate, db: Session = Depends(get_db)):
    """更新词条"""
    dict_service = DictService(db)
    try:
        update_data = {}
        if word_update.code is not None:
            update_data["code"] = word_update.code
        if word_update.weight is not None:
            update_data["weight"] = word_update.weight
        
        result = dict_service.update_word(word, **update_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/words/{word}")
def api_delete_word(word: str, db: Session = Depends(get_db)):
    """删除词条"""
    dict_service = DictService(db)
    try:
        result = dict_service.delete_word(word)
        if not result:
            raise HTTPException(status_code=404, detail="词条不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/search")
def api_search(keyword: str, db: Session = Depends(get_db)):
    """搜索词条"""
    dict_service = DictService(db)
    results = dict_service.search_words(keyword)
    return results

@app.post("/api/import/txt")
def api_import_txt(file_path: str, db: Session = Depends(get_db)):
    """导入TXT文件"""
    filter_service = FilterService(db)
    try:
        result = filter_service.import_from_txt(file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/import/csv")
def api_import_csv(file_path: str, db: Session = Depends(get_db)):
    """导入CSV文件"""
    filter_service = FilterService(db)
    try:
        result = filter_service.import_from_csv(file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/import/json")
def api_import_json(file_path: str, db: Session = Depends(get_db)):
    """导入JSON文件"""
    filter_service = FilterService(db)
    try:
        result = filter_service.import_from_json(file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
def api_get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    stats_service = StatsService(db)
    usage_patterns = stats_service.analyze_usage_patterns()
    return usage_patterns

@app.get("/api/high-frequency")
def api_get_high_frequency(limit: int = 100, db: Session = Depends(get_db)):
    """获取高频词"""
    stats_service = StatsService(db)
    high_frequency = stats_service.get_high_frequency_words(limit)
    return high_frequency

@app.get("/api/code-conflicts")
def api_get_code_conflicts(db: Session = Depends(get_db)):
    """获取编码冲突"""
    stats_service = StatsService(db)
    conflicts = stats_service.detect_code_conflicts()
    return conflicts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
