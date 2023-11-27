from typing import Tuple, List, Union, TypedDict


# ------------------------------------------------------------------
# 型定義
# ------------------------------------------------------------------
class type_chapter_by_page(TypedDict):
    pageno: int
    chapter_titles: str

# items:List[type_chapter] = []
# item: type_chapter = {'pageno': 1, 'chapter_title': 'unknown'}
# items.append(item)

class type_chapter_by_chapter(TypedDict):
    pageno_start: int
    pageno_end: int    
    chapter_title_all: str
    leaf_flg: bool

class type_chapter_per_page(TypedDict):
    pageno_start: int
    pageno_end: int    
    chapter_title: str
    level: Union[int,None]

class type_chapter_per_page2(TypedDict):
    pageno_start: int
    pageno_end: int    
    chapter_title: str
    leaf_flg: bool
    leveltext: str
    level1: int
    level2: int
    level3: int
    level4: int
    level5: int
    level6: int
    
class type_res_document_upload_save(TypedDict):
    status:str
    data:List[type_chapter_by_chapter]
# ----------------------------------------------------------------------
