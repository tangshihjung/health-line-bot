from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# 儲存用戶狀態
user_states = {}

# ==================== 健康計算函數 ====================
def calculate_bmi(height, weight):
    """計算 BMI"""
    bmi = weight / (height ** 2)
    return round(bmi, 2)

def get_bmi_category(bmi):
    """BMI 分類"""
    if bmi < 18.5:
        return "體重過輕"
    elif 18.5 <= bmi < 24:
        return "正常範圍"
    elif 24 <= bmi < 27:
        return "體重過重"
    elif 27 <= bmi < 30:
        return "輕度肥胖"
    elif 30 <= bmi < 35:
        return "中度肥胖"
    else:
        return "重度肥胖"

def calculate_bmr_male(weight, height, age):
    """男性基礎代謝率 (Mifflin-St Jeor 公式)"""
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    return round(bmr, 1)

def calculate_bmr_female(weight, height, age):
    """女性基礎代謝率 (Mifflin-St Jeor 公式)"""
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    return round(bmr, 1)

# ==================== AI 運動推薦 ====================
def recommend_exercise(bmi, age):
    """根據 BMI 和年齡推薦運動"""
    if age >= 65:
        return {
            'type': '長者居家運動',
            'reason': '適合銀髮族的低衝擊運動'
        }
    elif bmi < 18.5:
        return {
            'type': '上肢訓練',
            'reason': '增加肌肉量,提升體重'
        }
    elif bmi >= 27:
        return {
            'type': '下肢訓練',
            'reason': '大肌群運動,有效消耗熱量'
        }
    else:
        return {
            'type': '上肢訓練',
            'reason': '均衡訓練,維持健康'
        }

# ==================== 功能選單 ====================
def show_main_menu():
    """主選單"""
    menu = "👋 歡迎使用健康數據管家!\n\n"
    menu += "請選擇功能:\n\n"
    menu += "1️⃣ 健康檢測\n"
    menu += "   分析身體數值+飲食建議\n\n"
    menu += "2️⃣ 運動計畫\n"
    menu += "   個人化運動+影片教學\n\n"
    menu += "3️⃣ 飲食計畫\n"
    menu += "   超商組合+外食建議\n\n"
    menu += "請輸入數字 1-3"
    return menu

def show_exercise_menu(user_data=None):
    """運動選單"""
    menu = "💪 運動計畫\n\n"
    
    if user_data and 'bmi' in user_data and 'age' in user_data:
        rec = recommend_exercise(user_data['bmi'], user_data['age'])
        menu += f"🎯 AI推薦: {rec['type']}\n"
        menu += f"   {rec['reason']}\n\n"
    
    menu += "請選擇運動類型:\n"
    menu += "1️⃣ 上肢訓練\n"
    menu += "2️⃣ 下肢訓練\n"
    menu += "3️⃣ 長者居家運動\n\n"
    menu += "請輸入數字 1-3\n\n"
    menu += "💬 輸入「返回」回到選單"
    return menu

def get_diet_plan(bmi):
    """飲食計畫"""
    plan = "🍽️ 個人化飲食計畫\n\n"
    
    if bmi < 18.5:
        plan += "📊 您的體重偏輕\n"
        plan += "建議:增加熱量攝取\n\n"
        plan += "🌅 早:豆漿+三明治+香蕉\n"
        plan += "🌞 午:便當+雞腿+多吃飯\n"
        plan += "🌙 晚:牛排+義大利麵\n"
    elif 18.5 <= bmi < 24:
        plan += "✅ 您的體重正常\n"
        plan += "建議:維持均衡飲食\n\n"
        plan += "🌅 早:燕麥+水果+堅果\n"
        plan += "🌞 午:糙米飯+雞胸肉+青菜\n"
        plan += "🌙 晚:魚肉+地瓜+沙拉\n"
    elif 24 <= bmi < 27:
        plan += "⚠️ 您的體重偏重\n"
        plan += "建議:控制熱量攝取\n\n"
        plan += "🌅 早:無糖豆漿+茶葉蛋\n"
        plan += "🌞 午:半碗飯+瘦肉+2碗菜\n"
        plan += "🌙 晚:蒸魚+燙青菜(少澱粉)\n"
    else:  # BMI >= 27
        plan += "🔴 建議諮詢營養師\n"
        plan += "建議:積極控制飲食\n\n"
        plan += "🌅 早:無糖豆漿+地瓜\n"
        plan += "🌞 午:少量飯+瘦肉+3碗菜\n"
        plan += "🌙 晚:蒸魚+燙青菜3碗(不吃澱粉)\n"
    
    plan += "\n⚠️ 請諮詢醫師或營養師\n"
    plan += "\n💬 輸入「返回」回到選單"
    return plan

def get_exercise_detail(exercise_type):
    """運動詳細說明"""
    details = {
        '1': {
            'title': '上肢訓練',
            'content': (
                "💪 上肢訓練計畫\n\n"
                "🎯 目標:強化手臂、肩膀、胸部\n\n"
                "📋 訓練動作:\n"
                "• 伏地挺身 10次 x 3組\n"
                "• 啞鈴彎舉 12次 x 3組\n"
                "• 肩推 10次 x 3組\n\n"
                "⏱️ 組間休息:60秒\n"
                "📅 建議頻率:每週3次\n"
                "• 強度:適中,可感受肌肉收縮\n\n"
                "⚠️ 不適立即停止,疼痛請就醫"
            )
        },
        '2': {
            'title': '下肢訓練',
            'content': (
                "🦵 下肢訓練計畫\n\n"
                "🎯 目標:強化大腿、臀部、小腿\n\n"
                "📋 訓練動作:\n"
                "• 深蹲 15次 x 3組\n"
                "• 弓箭步 12次 x 3組(每腿)\n"
                "• 橋式 15次 x 3組\n\n"
                "⏱️ 組間休息:60秒\n"
                "📅 建議頻率:每週3次\n"
                "• 強度:適中,膝蓋不超過腳尖\n\n"
                "⚠️ 不適立即停止,膝痛請就醫"
            )
        },
        '3': {
            'title': '長者居家運動',
            'content': (
                "🧓 長者居家運動\n\n"
                "🎯 目標:維持活動力、預防跌倒\n\n"
                "📋 訓練動作:\n"
                "• 坐姿抬腿 10次 x 2組\n"
                "• 手臂畫圈 10次 x 2組\n"
                "• 站姿側抬腿 8次 x 2組(扶椅)\n\n"
                "⏱️ 組間休息:90秒\n"
                "📅 建議頻率:每天輕鬆做\n"
                "• 強度:輕鬆不費力\n\n"
                "⚠️ 不適立即停止,頭暈胸悶請就醫"
            )
        }
    }
    
    detail = details.get(exercise_type, {}).get('content', "找不到該運動計畫")
    detail += "\n\n💬 輸入「返回」回到選單"
    return detail

# ==================== Webhook 處理 ====================
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    
    # 初始化用戶狀態
    if user_id not in user_states:
        user_states[user_id] = {'mode': 'menu'}
    
    state = user_states[user_id]
    
    # ✅ 選單指令(修正版:保留 health_data)
    if user_message in ['選單', '功能', 'menu', '開始', 'start', '返回', 'back', '重新選擇']:
        # 保留舊的 health_data
        old_data = user_states.get(user_id, {}).get('health_data')
        user_states[user_id] = {'mode': 'menu'}
        if old_data:  # 如果之前有健康數據,保留它
            user_states[user_id]['health_data'] = old_data
        reply = show_main_menu()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 主選單處理
    if state['mode'] == 'menu':
        if user_message == '1':
            # ✅ 保留舊的 health_data (如果存在),但開始新的檢測
            old_data = user_states.get(user_id, {}).get('health_data')
            user_states[user_id] = {'mode': 'health', 'step': 1}
            if old_data:
                user_states[user_id]['health_data'] = old_data
            reply = "📊 健康檢測\n\n請輸入你的身高(公分)\n例如: 170\n\n💬 輸入「返回」可重新選擇"
        elif user_message == '2':
            reply = show_exercise_menu(state.get('health_data'))
            user_states[user_id]['mode'] = 'exercise'
        elif user_message == '3':
            if 'health_data' in state and 'bmi' in state['health_data']:
                reply = get_diet_plan(state['health_data']['bmi'])
            else:
                reply = "💡 建議先完成「健康檢測」\n可獲得個人化飲食建議\n\n輸入「1」開始檢測\n或輸入「返回」重新選擇"
        else:
            reply = show_main_menu()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 健康檢測流程
    if state['mode'] == 'health':
        if state.get('step') == 1:
            try:
                height_cm = float(user_message)
                if 100 <= height_cm <= 250:
                    state['height'] = height_cm / 100  # 轉換成公尺儲存
                    state['height_cm'] = height_cm  # 也保存公分值用於顯示
                    state['step'] = 2
                    reply = f"✅ 身高: {height_cm:.0f}cm\n\n請輸入體重(公斤)\n例如: 70\n\n💬 輸入「返回」可重新選擇"
                else:
                    reply = "⚠️ 請輸入100-250之間的數字\n\n💬 輸入「返回」可重新選擇"
            except:
                reply = "⚠️ 請輸入有效數字\n\n💬 輸入「返回」可重新選擇"
        elif state.get('step') == 2:
            try:
                weight = float(user_message)
                if 30 <= weight <= 300:
                    state['weight'] = weight
                    state['step'] = 3
                    reply = f"✅ 體重: {weight}kg\n\n請輸入年齡(歲)\n例如: 30\n\n💬 輸入「返回」可重新選擇"
                else:
                    reply = "⚠️ 請輸入30-300之間的數字\n\n💬 輸入「返回」可重新選擇"
            except:
                reply = "⚠️ 請輸入有效數字\n\n💬 輸入「返回」可重新選擇"
        elif state.get('step') == 3:
            try:
                age = int(user_message)
                if 10 <= age <= 120:
                    state['age'] = age
                    state['step'] = 4
                    reply = f"✅ 年齡: {age}歲\n\n請輸入性別\n請輸入: 男 或 女\n\n💬 輸入「返回」可重新選擇"
                else:
                    reply = "⚠️ 請輸入10-120之間的數字\n\n💬 輸入「返回」可重新選擇"
            except:
                reply = "⚠️ 請輸入有效數字\n\n💬 輸入「返回」可重新選擇"
        elif state.get('step') == 4:
            if user_message in ['男', '女']:
                # ✅ 檢查所有必要數據是否存在
                if 'height' not in state or 'weight' not in state or 'age' not in state or 'height_cm' not in state:
                    reply = "❌ 資料不完整,請重新開始\n\n💬 輸入「返回」回到選單"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
                    return
                
                # ✅ 先保存性別到 state
                state['gender'] = user_message
                
                bmi = calculate_bmi(state['height'], state['weight'])
                
                if user_message == '男':
                    bmr = calculate_bmr_male(state['weight'], state['height']*100, state['age'])
                else:
                    bmr = calculate_bmr_female(state['weight'], state['height']*100, state['age'])

                category = get_bmi_category(bmi)
                reply = f"📊 健康分析結果\n\n"
                reply += f"身高: {state['height_cm']:.0f}cm\n"
                reply += f"體重: {state['weight']}kg\n"
                reply += f"BMI: {bmi} ({category})\n"
                reply += f"基礎代謝率: {bmr}大卡/天\n\n"
                reply += f"✅ 分析完成!\n\n"
                reply += f"💬 輸入「選單」查看:\n"
                reply += "• 運動計畫(AI推薦)\n"
                reply += "• 飲食計畫(個人化)\n"

                # ✅ 完整保存所有健康數據
                user_states[user_id] = {
                    'mode': 'menu',
                    'health_data': {
                        'bmi': bmi,
                        'bmr': bmr,
                        'age': state['age'],
                        'gender': state['gender'],
                        'height': state['height'],
                        'height_cm': state['height_cm'],
                        'weight': state['weight']
                    }
                }
            else:
                reply = "⚠️ 請輸入: 男 或 女\n\n💬 輸入「返回」可重新選擇"
        else:
            reply = show_main_menu()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 運動選單處理
    if state['mode'] == 'exercise':
        if user_message in ['1', '2', '3']:
            reply = get_exercise_detail(user_message)
        else:
            reply = show_exercise_menu(state.get('health_data'))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 預設回應
    reply = "❓ 無法識別指令\n\n請輸入「選單」查看功能"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ==================== 啟動服務 ====================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
