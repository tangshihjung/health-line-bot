from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

user_states = {}

def calculate_bmi(height_m, weight_kg):
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "體重過輕"
    elif 18.5 <= bmi < 24:
        return "健康體位"
    elif 24 <= bmi < 27:
        return "體位過重"
    elif 27 <= bmi < 30:
        return "輕度肥胖"
    else:
        return "重度肥胖"

def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender == '男':
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return round(bmr, 1)

def get_exercise_recommendation(bmi, age):
    if age >= 60:
        return {'recommend': 3, 'reason': '專為銀髮族設計，安全低衝擊'}
    elif bmi < 18.5:
        return {'recommend': '1+2', 'reason': '增肌為主，上下肢都要訓練'}
    elif bmi >= 27:
        return {'recommend': 3, 'reason': '低衝擊運動保護關節'}
    elif bmi >= 24:
        return {'recommend': 2, 'reason': '大肌群訓練，減脂效果佳'}
    else:
        return {'recommend': '任選', 'reason': '體態正常，依喜好選擇'}

def get_diet_plan(bmi):
    category = get_bmi_category(bmi)
    plan = f"🍽️ 飲食計畫\n\n📊 BMI: {bmi} ({category})\n\n"
    
    if bmi < 18.5:
        plan += "🎯 目標:健康增重\n\n"
        plan += "【🏪 超商健康組合】($150)\n"
        plan += "✅ 御飯糰 $35\n✅ 茶葉蛋2顆 $26\n"
        plan += "✅ 全脂牛奶 $30\n✅ 堅果 $40\n✅ 香蕉 $15\n"
        plan += "💰 $146 | 🔥 約600卡\n\n"
        plan += "【🍜 外食建議】\n"
        plan += "✅ 雞腿便當+荷包蛋\n✅ 自助餐2肉2菜\n"
        plan += "✅ 牛肉麵+滷蛋\n⚠️ 避免:輕食沙拉\n\n"
        plan += "【📅 一日三餐】\n"
        plan += "🌅 早:全麥吐司2片+花生醬+蛋2顆+全脂奶\n"
        plan += "🌞 午:雞腿便當+牛油果+堅果\n"
        plan += "🌙 晚:鮭魚150g+地瓜+青菜+糙米飯\n"
    elif 18.5 <= bmi < 24:
        plan += "🎯 目標:維持健康\n\n"
        plan += "【🏪 超商健康組合】($120)\n"
        plan += "✅ 茶葉蛋2顆 $26\n✅ 地瓜 $35\n"
        plan += "✅ 無糖豆漿 $25\n✅ 雞胸沙拉 $65\n"
        plan += "💰 $151 | 🔥 約400卡\n\n"
        plan += "【🍜 外食建議】\n"
        plan += "✅ 雞胸便當+燙青菜\n✅ 自助餐1肉2菜\n"
        plan += "✅ 陽春麵+燙青菜\n⚠️ 避免:炸物飲料\n\n"
        plan += "【📅 一日三餐】\n"
        plan += "🌅 早:燕麥粥+蛋+奇亞籽\n"
        plan += "🌞 午:雞胸+糙米飯+青菜2碗\n"
        plan += "🌙 晚:蒸魚+地瓜+大量蔬菜\n"
    elif 24 <= bmi < 27:
        plan += "🎯 目標:溫和減重\n\n"
        plan += "【🏪 超商健康組合】($100)\n"
        plan += "✅ 茶葉蛋2顆 $26\n✅ 雞胸沙拉 $65\n"
        plan += "✅ 無糖綠茶 $25\n"
        plan += "💰 $116 | 🔥 約300卡\n\n"
        plan += "【🍜 外食建議】\n"
        plan += "✅ 雞胸便當少飯油\n✅ 自助餐1肉3菜\n"
        plan += "✅ 滷味:蔬菜+豆製品\n⚠️ 避免:炒飯炒麵\n\n"
        plan += "【📅 一日三餐】\n"
        plan += "🌅 早:全麥吐司+蛋+無糖豆漿\n"
        plan += "🌞 午:雞胸+糙米飯半碗+大量蔬菜\n"
        plan += "🌙 晚:蒸魚+燙青菜2碗(不吃澱粉)\n"
    elif 27 <= bmi < 30:
        plan += "🎯 目標:積極減重\n\n"
        plan += "【🏪 超商健康組合】($90)\n"
        plan += "✅ 茶葉蛋2顆 $26\n✅ 無糖豆漿 $25\n"
        plan += "✅ 生菜沙拉 $45\n"
        plan += "💰 $96 | 🔥 約250卡\n\n"
        plan += "【🍜 外食建議】\n"
        plan += "✅ 自助餐:大量青菜+瘦肉\n✅ 滷味:蔬菜為主\n"
        plan += "✅ 火鍋:菜盤+海鮮\n⚠️ 避免:油炸糖飲\n\n"
        plan += "【📅 一日三餐】\n"
        plan += "🌅 早:燕麥粥40g+蛋+黑咖啡\n"
        plan += "🌞 午:雞胸+糙米飯1/3碗+青菜2碗\n"
        plan += "🌙 晚:蒸魚100g+燙青菜3碗(不吃澱粉)\n"
    else:
        plan += "🎯 目標:醫療級減重\n\n"
        plan += "【🏪 超商健康組合】($80)\n"
        plan += "✅ 水煮蛋2顆 $26\n✅ 無糖豆漿 $25\n"
        plan += "✅ 小番茄 $35\n"
        plan += "💰 $86 | 🔥 約200卡\n\n"
        plan += "【🍜 外食建議】\n"
        plan += "✅ 自助餐:蔬菜+水煮蛋白\n✅ 滷味:全選蔬菜\n"
        plan += "✅ 涮涮鍋:蔬菜+海鮮\n⚠️ 避免:所有加工品\n\n"
        plan += "【📅 一日三餐】\n"
        plan += "🌅 早:水煮蛋2顆+無糖豆漿\n"
        plan += "🌞 午:雞胸100g+大量蔬菜(不吃澱粉)\n"
        plan += "🌙 晚:蒸魚+燙青菜3碗(不吃澱粉)\n"
        plan += "\n⚠️ 請諮詢醫師或營養師\n"
    
    plan += "\n💬 輸入「選單」返回"
    return plan

def get_exercise_detail(exercise_type):
    videos = {
        '1': 'https://www.youtube.com/watch?v=IODxDxX7oi4',
        '2': 'https://www.youtube.com/watch?v=aclHkVaku9U',
        '3': 'https://www.youtube.com/watch?v=4BOTvaRaDjI'
    }
    
    if exercise_type == '1':
        detail = "💪 上肢訓練\n\n【訓練肌群】\n"
        detail += "✅ 胸大肌:推的動作\n✅ 三角肌:肩膀穩定\n"
        detail += "✅ 肱二頭肌:手臂彎曲\n✅ 肱三頭肌:手臂伸直\n\n"
        detail += "【發力重點】\n"
        detail += "• 胸部:向內擠壓\n• 肩膀:下壓避免聳肩\n"
        detail += "• 核心:保持收緊\n\n"
        detail += f"【教學影片】\n🎥 {videos['1']}\n\n"
        detail += "【訓練建議】\n"
        detail += "• 頻率:每週2-3次\n• 組數:每動作3組\n"
        detail += "• 次數:每組10-15下\n• 休息:60秒\n\n"
        detail += "⚠️ 保持呼吸,感受發力,不適立即停止"
    elif exercise_type == '2':
        detail = "💪 下肢訓練\n\n【訓練肌群】\n"
        detail += "✅ 股四頭肌:大腿前側\n✅ 腿後肌群:大腿後側\n"
        detail += "✅ 臀大肌:臀部主力\n✅ 小腿肌群:小腿\n\n"
        detail += "【發力重點】\n"
        detail += "• 臀部:往後坐\n• 膝蓋:不超過腳尖\n"
        detail += "• 腰背:保持挺直\n\n"
        detail += f"【教學影片】\n🎥 {videos['2']}\n\n"
        detail += "【訓練建議】\n"
        detail += "• 頻率:每週2-3次\n• 組數:每動作3-4組\n"
        detail += "• 次數:每組12-20下\n• 休息:90秒\n\n"
        detail += "⚠️ 膝蓋與腳尖同向,腰背挺直"
    else:
        detail = "💪 長者居家運動\n\n【訓練重點】\n"
        detail += "✅ 肌力維持\n✅ 平衡訓練\n"
        detail += "✅ 關節活動\n✅ 心肺功能\n\n"
        detail += "【安全原則】\n"
        detail += "• 動作和緩\n• 旁邊有扶手\n"
        detail += "• 穿防滑鞋\n• 有人陪伴\n\n"
        detail += f"【教學影片】\n🎥 {videos['3']}\n\n"
        detail += "【訓練建議】\n"
        detail += "• 頻率:每天練習\n• 時間:15-20分鐘\n"
        detail += "• 強度:輕鬆不費力\n\n"
        detail += "⚠️ 不適立即停止,頭暈胸悶請就醫"
    
    detail += "\n\n💬 輸入「選單」返回"
    return detail

def show_main_menu():
    menu = "👋 歡迎使用健康數據管家!\n\n"
    menu += "請選擇功能:\n\n"
    menu += "1️⃣ 健康檢測\n   分析身體數值+飲食建議\n\n"
    menu += "2️⃣ 運動計畫\n   個人化運動+影片教學\n\n"
    menu += "3️⃣ 飲食計畫\n   超商組合+外食建議\n\n"
    menu += "請輸入數字 1-3"
    return menu

def show_exercise_menu(user_data=None):
    menu = "💪 運動計畫\n\n"
    if user_data and 'bmi' in user_data:
        rec = get_exercise_recommendation(user_data['bmi'], user_data.get('age', 30))
        menu += f"📊 根據你的數據:\n"
        menu += f"BMI: {user_data['bmi']} ({get_bmi_category(user_data['bmi'])})\n\n"
        menu += f"🎯 AI推薦: {rec['reason']}\n\n"
    menu += "請選擇運動類型:\n"
    menu += "1️⃣ 上肢訓練\n2️⃣ 下肢訓練\n3️⃣ 長者居家運動\n\n"
    menu += "請輸入數字 1-3"
    return menu

@app.route("/webhook", methods=['POST'])
def callback():
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
    
    if user_id not in user_states:
        user_states[user_id] = {'mode': 'menu'}
    
    state = user_states[user_id]
    
    # 選單指令
    if user_message in ['選單', '功能', 'menu', '開始', 'start']:
        user_states[user_id] = {'mode': 'menu'}
        reply = show_main_menu()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 主選單
    if state['mode'] == 'menu':
        if user_message == '1':
            user_states[user_id] = {'mode': 'health', 'step': 1}
            reply = "📊 健康檢測\n\n請輸入你的身高(公尺)\n例如: 1.70"
        elif user_message == '2':
            reply = show_exercise_menu(state.get('health_data'))
            user_states[user_id]['mode'] = 'exercise'
        elif user_message == '3':
            if 'health_data' in state and 'bmi' in state['health_data']:
                reply = get_diet_plan(state['health_data']['bmi'])
            else:
                reply = "💡 建議先完成「健康檢測」\n可獲得個人化飲食建議\n\n或輸入你的 BMI 值查看通用建議"
        else:
            reply = show_main_menu()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 健康檢測流程
    if state['mode'] == 'health':
        if state.get('step') == 1:
            try:
                height = float(user_message)
                if 1.0 <= height <= 2.5:
                    state['height'] = height
                    state['step'] = 2
                    reply = f"✅ 身高: {height}m\n\n請輸入體重(公斤)\n例如: 70"
                else:
                    reply = "⚠️ 請輸入1.0-2.5之間的數字"
            except:
                reply = "⚠️ 請輸入有效數字"
        elif state.get('step') == 2:
            try:
                weight = float(user_message)
                if 30 <= weight <= 300:
                    state['weight'] = weight
                    state['step'] = 3
                    reply = f"✅ 體重: {weight}kg\n\n請輸入年齡(歲)\n例如: 30"
                else:
                    reply = "⚠️ 請輸入30-300之間的數字"
            except:
                reply = "⚠️ 請輸入有效數字"
        elif state.get('step') == 3:
            try:
                age = int(user_message)
                if 10 <= age <= 120:
                    state['age'] = age
                    state['step'] = 4
                    reply = f"✅ 年齡: {age}歲\n\n請輸入性別\n請輸入: 男 或 女"
                else:
                    reply = "⚠️ 請輸入10-120之間的數字"
            except:
                reply = "⚠️ 請輸入有效數字"
        elif state.get('step') == 4:
            if user_message in ['男', '女']:
                bmi = calculate_bmi(state['height'], state['weight'])
                bmr = calculate_bmr(state['weight'], state['height']*100, state['age'], user_message)
                
                state['health_data'] = {
                    'bmi': bmi,
                    'bmr': bmr,
                    'age': state['age']
                }
                
                category = get_bmi_category(bmi)
                reply = f"📊 健康分析結果\n\n"
                reply += f"身高: {state['height']}m\n"
                reply += f"體重: {state['weight']}kg\n"
                reply += f"BMI: {bmi} ({category})\n"
                reply += f"基礎代謝率: {bmr}大卡/天\n\n"
                reply += "✅ 分析完成!\n\n"
                reply += "💬 輸入「選單」查看:\n"
                reply += "• 運動計畫(AI推薦)\n"
                reply += "• 飲食計畫(個人化)"
                
                user_states[user_id]['mode'] = 'menu'
            else:
                reply = "⚠️ 請輸入: 男 或 女"
        else:
            reply = show_main_menu()
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 運動計畫
    if state['mode'] == 'exercise':
        if user_message in ['1', '2', '3']:
            reply = get_exercise_detail(user_message)
            user_states[user_id]['mode'] = 'menu'
        else:
            reply = show_exercise_menu(state.get('health_data'))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 預設
    reply = show_main_menu()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/")
def home():
    return "健康數據管家 LINE Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
