from fastmcp import FastMCP, Client
from typing import List, Optional, Dict, Union
import time
import os
import mcp
import requests
from fastapi import Request

BASE_URL = "https://miniprogram.shandaonmc.com/dev-api"

# token
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJzeXNfdXNlcjoxMTQiLCJyblN0ciI6InBWMmxpUzlJUEZIRk1leDZqYzlDaXN2bHp2WFM0SjI3IiwiY2xpZW50aWQiOiJlNWNkN2U0ODkxYmY5NWQxZDE5MjA2Y2UyNGE3YjMyZSIsInRlbmFudElkIjoiMDAwMDAwIiwidXNlcklkIjoxMTQsInZpcEV4cGlyZURhdGUiOjE3NDc4MTkzNjgsInVzZXJOYW1lIjoibWNwQXBpIiwiZGVwdE5hbWUiOiIiLCJkZXB0Q2F0ZWdvcnkiOiIifQ.lJOfCiYljW4BO2iX7iIjdB51vFxzDsi3bDuN7mQRUXI"


mcp = FastMCP("mcp-nutrimaster")


# 详细参数说明：
# age: 年龄
# sex: 性别（0男1女）
# height: 身高（米）
# weight: 体重（kg）
# nutrientSceneName: 营养模型名称（可选）
#当用户输入他的年龄性别身高体重的时候，会根据他的体征去推荐当餐菜品 如果是男生性别为0 如果是女生性别为1 身高如果是厘米需要除100
#只会返回当餐的推荐菜品，菜品的重量，菜品重量是由dishesCopiesDefaultQuantitativeUnit和dishesMeasureToolNameDefaultQuantitativeUnit组合而成，菜品对应的食材重量，推荐分数，以及当餐是否会有扣分
@mcp.tool()
def create_recommended_dishes(
    age: float,
    sex: str,
    height: float,
    weight: float,
    nutrientSceneName: Optional[Union[str, List[str]]] = None
) -> dict:
    """根据用户年龄 性别 身高 体重 可选营养模型名称，进行推荐菜品
    
    Args:
        age: 年龄
        sex: 性别（0男1女）
        height: 身高（米）
        weight: 体重（kg）
        nutrientSceneName: 营养模型名称（可选），可以是单个字符串或字符串列表
    """
    # 获取营养模型id
    if nutrientSceneName:
        # 将单个字符串转换为列表
        if isinstance(nutrientSceneName, str):
            nutrientSceneName = [nutrientSceneName]
            
        # 获取所有营养模型
        url = "https://miniprogram.shandaonmc.com/dev-api/hy-basics/CommonBasics/SelectNutrientSceneForIdentification?isShow=0"
        headers = {
            "Authorization": f"Bearer {token}",
            "clientId": "e5cd7e4891bf95d1d19206ce24a7b32e"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            models = response.json().get("data", [])
            
            # 收集所有匹配的营养模型ID
            nutrientSceneIds = []
            for scene_name in nutrientSceneName:
                matched = [m for m in models if scene_name.lower() in m.get("nutrientSceneName", "").lower()]
                if matched:
                    nutrientSceneIds.extend([m["id"] for m in matched])
            
            # 如果没有匹配到任何模型，使用默认ID
            if not nutrientSceneIds:
                nutrientSceneIds = [1]
        except Exception:
            nutrientSceneIds = [1]
    else:
        nutrientSceneIds = [1]

    url = "https://miniprogram.shandaonmc.com/dev-api/hy/patient/CreateRecommendedDishes"
    headers = {
        "Authorization": f"Bearer {token}",
        "clientId": "e5cd7e4891bf95d1d19206ce24a7b32e"
    }
    
    data = {
        "conversationId": "67ff4ee7b2771c5ada72aa14",
        "canteenId": None,
        "age": age,
        "sex": sex,
        "height": height,
        "weight": weight,
        "nutrientSceneIds":  nutrientSceneIds,
        "userExclusion":  [],#用户排除食材 现默认为空
        "customerSpecifiedIngredients":  [],#用户指定食材 现默认为空
        "customerSpecifiedDishes": [],#用户指定菜品 现默认为空
        "isIngredientDishes": 0,#是否为食材菜品 现默认为0
        "likesLabels": [],#用户喜好标签 现默认为空
        "isConstraintOSS": "0",#是否限制OSS 现默认为0
        "isSceneMask": "1",#是否场景遮罩 现默认为1
        "mealId": "2",#餐次 现默认为2为午餐
        "recommendedDate": "2025-05-06",#推荐日期 现默认为当天
        "recipeRecommendationPatterns": "1",#推荐模式 现默认为1为营养均衡
        "trUserInformationDiseaseList": [],#用户疾病列表 现默认为空
        "trUserInformationPostoperationList":[],#用户术后列表 现默认为空
        "trUserInformationSceneRecombList" :[]#用户场景列表 现默认为空  
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        # print(response_json)
        # 提取关键信息
        result = []
        data = response_json.get("data", {})
       
        best_results = data.get("recommendedDishesBestResults", {})
        for score, dishes_list in best_results.items():
            for item in dishes_list:
                dishes_bos = item.get("recommendedDishesBos", [])
                for dish in dishes_bos:
                    if dish.get("isHaveEaten") == "0":
                        name = dish.get("dishesName", "")
                        weight = dish.get("dishesWeight", "")
                        measure_tool = dish.get("dishesMeasureToolNameDefaultQuantitativeUnit", "")
                        copies = dish.get("dishesCopiesDefaultQuantitativeUnit", "")
                        # 提取每个食材的名称和重量
                        ingredients = dish.get("ingredientIdWeightsDefaultQuantitativeUnit", [])
                        ingredient_list = []
                        for ing in ingredients:
                            ing_name = ing.get("ingredientName", "")
                            ing_weight = ing.get("weight", "")
                            ingredient_list.append({
                                "ingredientName": ing_name,
                                "weight": f"{ing_weight}克"
                            })
                        result.append({
                            "name": name,
                            "weight": f"{weight}克（{copies}{measure_tool}）",
                            "ingredients": ingredient_list
                        })
        return result
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def show_dishes_and_weights(response_json):
    if not response_json or not isinstance(response_json, dict):
        print("接口返回数据为空或格式不正确！")
        return
    if "error" in response_json:
        print("接口请求出错：", response_json["error"])
        return
    data = response_json.get("data", {})
    best_results = data.get("recommendedDishesBestResults", {})
    for score, dishes_list in best_results.items():
        print(f"推荐分数：{score}")
        for item in dishes_list:
            dishes_bos = item.get("recommendedDishesBos", [])
            for dish in dishes_bos:
                if dish.get("isHaveEaten") == "0":
                    name = dish.get("dishesName", "未知菜品")
                    weight = dish.get("dishesWeight", "未知重量")
                    measure_tool = dish.get("dishesMeasureToolNameDefaultQuantitativeUnit", "未知计量工具")
                    copies = dish.get("dishesCopiesDefaultQuantitativeUnit", "未知份数")
                    print(f"菜品：{name}，重量：{weight}克（{copies}{measure_tool}）")
                    # 显示每个食材的重量
                    ingredients = dish.get("ingredientIdWeightsDefaultQuantitativeUnit", [])
                    for ing in ingredients:
                        ing_name = ing.get("ingredientName", "未知食材")
                        ing_weight = ing.get("weight", "未知重量")
                        print(f"    食材：{ing_name}，重量：{ing_weight}克")


# 获取所有营养模型
@mcp.tool()
def get_all_nutrition_models():
    """获取所有营养模型，只返回id和clientNutrientSceneName字段"""
    
    url = "https://miniprogram.shandaonmc.com/dev-api/hy-basics/CommonBasics/SelectNutrientSceneForIdentification?isShow=0"
    headers = {
        "Authorization": f"Bearer {token}",
        "clientId": "e5cd7e4891bf95d1d19206ce24a7b32e"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        
        # 只提取需要的字段
        if "data" in response_json:
            simplified_data = [
                {
                    "id": item.get("id"),
                    "clientNutrientSceneName": item.get("clientNutrientSceneName")
                }
                for item in response_json["data"]
            ]
            return {"data": simplified_data}
        return response_json
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=9000)