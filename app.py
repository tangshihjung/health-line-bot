from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# LINE Bot 設定 - 請填入你的 Channel Secret 和 Access Token
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 用字典儲存每個使用者的對話狀態
user_states = {}

def calculate_bmi(height_m, weight_kg):
    """計算 BMI"""
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def get_bmi_category(bmi):
    """判斷 BMI 分類"""
    if bmi < 18.5:
        return "體重過輕"
    elif 18.5 <= bmi < 24:
        return "健康體位"
    elif 24 <= bmi < 27:
        return "體位過重"
    elif 27 <= bmi < 30:
        return "輕度肥胖"
    elif 30 <= bmi < 35:
        return "重度肥胖"
    else:
        return "重度肥胖"

def calculate_bmr(weight_kg, height_cm, age, gender):
    """計算基礎代謝率 BMR (使用 Harris-Benedict 公式)"""
    if gender == '男':
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:  # 女
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return round(bmr, 1)

def get_diet_advice(bmi, bmr, height_m, weight_kg):
    """根據 BMI 給出飲食建議"""
    category = get_bmi_category(bmi)
    
    advice = f"📊 健康分析結果\n\n"
    advice += f"身高: {height_m} 公尺\n"
    advice += f"體重: {weight_kg} 公斤\n"
    advice += f"BMI: {bmi} ({category})\n"
    advice += f"基礎代謝率: {bmr} 大卡/天\n\n"
    
    advice += "=" * 25 + "\n\n"
    advice += "💡 飲食建議:\n\n"
    
    if bmi < 18.5:
        # 體重過輕
        advice += "🔸 BMI < 18.5（體重過輕）\n\n"
        advice += "【飲食原則】\n"
        advice += "1. 增加高營養密度的食物攝入，如堅果、全脂乳製品和健康油脂，以提升熱量攝取並促進體重增加。\n\n"
        advice += "2. 每天分多次進食，選擇富含蛋白質的食物（如雞蛋、瘦肉和豆類）並搭配複合碳水化合物，幫助穩定增重。\n\n"
        advice += "【建議菜單】\n\n"
        advice += "🍳 早餐：\n"
        advice += "• 全脂希臘優格(200g)搭配一湯匙蜂蜜、30g堅果(如杏仁或核桃)和半杯藍莓\n"
        advice += "• 兩片全麥吐司抹花生醬(2湯匙)，搭配一杯全脂牛奶(250ml)\n\n"
        advice += "🍱 午餐：\n"
        advice += "• 雞胸肉三明治(100g烤雞胸、兩片全麥麵包、牛油果1/4顆、生菜和番茄)\n"
        advice += "• 一份烤地瓜(150g)搭配橄欖油(1湯匙)，以及一杯香蕉奶昔(1根香蕉+250ml全脂牛奶)"
        
    elif 18.5 <= bmi < 24:
        # 健康體位
        advice += "🔸 BMI 18.5-24（正常範圍）\n\n"
        advice += "【飲食原則】\n"
        advice += "1. 維持均衡飲食，確保每天攝取足夠的蔬菜、水果、全穀類和優質蛋白質，以支持整體健康。\n\n"
        advice += "2. 控制加工食品和含糖飲料的攝入，保持適量運動以維持健康的體重和體能。\n\n"
        advice += "【建議菜單】\n\n"
        advice += "🍳 早餐：\n"
        advice += "• 燕麥粥(50g燕麥用250ml低脂牛奶煮製)，加入10g奇亞籽和半杯草莓\n"
        advice += "• 一顆水煮蛋，搭配一杯無糖綠茶\n\n"
        advice += "🍱 午餐：\n"
        advice += "• 烤鮭魚(100g)搭配藜麥(100g)與蒸西蘭花(150g)，淋少許檸檬汁和橄欖油(1茶匙)\n"
        advice += "• 一份新鮮水果沙拉(蘋果、橙子各半個)，搭配100g低脂優格"
        
    elif 24 <= bmi < 27:
        # 體位過重
        advice += "🔸 BMI 24-27（體位過重）\n\n"
        advice += "【飲食原則】\n"
        advice += "1. 優先選擇低熱量、高纖維的食物，如綠葉蔬菜和全穀類，減少高脂肪和高糖食物的攝入以控制熱量。\n\n"
        advice += "2. 採取定時定量的飲食習慣，避免過量進食，並搭配適量水分和規律運動以促進體重管理。\n\n"
        advice += "【建議菜單】\n\n"
        advice += "🍳 早餐：\n"
        advice += "• 全麥吐司(1片)搭配半顆牛油果和一顆水煮蛋，撒少許黑胡椒\n"
        advice += "• 一杯無糖豆漿(250ml)與10g杏仁\n\n"
        advice += "🍱 午餐：\n"
        advice += "• 雞胸肉沙拉(100g烤雞胸、菠菜、生菜、櫻桃番茄、黃瓜，淋1湯匙橄欖油和檸檬汁)\n"
        advice += "• 一份烤南瓜(150g)與半杯糙米"
        
    elif 27 <= bmi < 30:
        # 輕度肥胖
        advice += "🔸 BMI 27-30（輕度肥胖）\n\n"
        advice += "【飲食原則】\n"
        advice += "1. 減少精製碳水化合物和飽和脂肪的攝入，增加高纖維食物（如豆類和蔬菜）以增強飽足感並降低熱量攝取。\n\n"
        advice += "2. 每餐控制份量，選擇低熱量但營養豐富的食物，並每天飲用足量水以支持代謝和減重。\n\n"
        advice += "【建議菜單】\n\n"
        advice += "🍳 早餐：\n"
        advice += "• 無糖燕麥粥(40g燕麥用200ml水煮製)，加入15g亞麻籽和1/4杯藍莓\n"
        advice += "• 一杯無糖黑咖啡或綠茶\n\n"
        advice += "🍱 午餐：\n"
        advice += "• 蒸鱈魚(100g)搭配炒雜菜(西蘭花、胡蘿蔔、甜椒各50g，用1茶匙橄欖油烹調)\n"
        advice += "• 半杯藜麥與一杯清水"
        
    else:
        # 重度肥胖 (BMI >= 30)
        advice += "🔸 BMI 30-35（重度肥胖）\n\n"
        advice += "【飲食原則】\n"
        advice += "1. 採用低熱量飲食計畫，優先選擇高蛋白、低GI（升糖指數）的食物，如瘦肉和全穀類，以控制血糖並促進脂肪燃燒。\n\n"
        advice += "2. 避免高糖和高脂肪的加工食品，結合規律的有氧運動，並考慮制定個人化的減重計畫。\n\n"
        advice += "【建議菜單】\n\n"
        advice += "🍳 早餐：\n"
        advice += "• 蛋白煎蛋捲(2顆蛋+菠菜、蘑菇各30g)，搭配半片全麥吐司\n"
        advice += "• 一杯無糖花草茶\n\n"
        advice += "🍱 午餐：\n"
        advice += "• 烤雞胸(100g)搭配清蒸羽衣甘藍(100g)和烤花椰菜(100g)，淋1茶匙橄欖油\n"
        advice += "• 一份小份糙米(50g)與一杯檸檬水"
    
    advice += "\n\n💬 輸入「重新開始」可以再次分析"
    
    return advice

@app.route("/webhook", methods=['POST'])
def callback():
    """處理 LINE webhook"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理使用者訊息"""
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    
    # 初始化使用者狀態
    if user_id not in user_states:
        user_states[user_id] = {'step': 0}
    
    state = user_states[user_id]
    
    # 重新開始
    if user_message in ['重新開始', '開始', 'start', '重來']:
        user_states[user_id] = {'step': 0}
        reply = "👋 歡迎使用健康數據管家!\n\n我會引導你輸入身體數值，並提供個人化的飲食建議。\n\n📝 請輸入你的身高(公尺)\n例如: 1.70"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 使用說明
    if user_message in ['說明', '幫助', 'help', '?']:
        reply = "📖 使用說明\n\n我會依序詢問你:\n1️⃣ 身高(公尺)\n2️⃣ 體重(公斤)\n3️⃣ 年齡(歲)\n4️⃣ 性別(男/女)\n\n然後為你分析 BMI 並提供飲食建議!\n\n💬 輸入「開始」可以開始分析"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    
    # 對話流程控制
    if state['step'] == 0:
        # 詢問身高
        reply = "👋 歡迎使用健康數據管家!\n\n我會引導你輸入身體數值，並提供個人化的飲食建議。\n\n📝 請輸入你的身高(公尺)\n例如: 1.70"
        user_states[user_id]['step'] = 1
        
    elif state['step'] == 1:
        # 接收身高(公尺)
        try:
            height = float(user_message)
            if 1.0 <= height <= 2.5:
                user_states[user_id]['height'] = height
                user_states[user_id]['step'] = 2
                reply = f"✅ 身高: {height} 公尺\n\n📝 請輸入你的體重(公斤)\n例如: 70"
            else:
                reply = "⚠️ 身高數值似乎不合理\n請輸入 1.0-2.5 之間的數字\n例如: 1.70"
        except ValueError:
            reply = "⚠️ 請輸入有效的數字\n例如: 1.70"
    
    elif state['step'] == 2:
        # 接收體重
        try:
            weight = float(user_message)
            if 30 <= weight <= 300:
                user_states[user_id]['weight'] = weight
                user_states[user_id]['step'] = 3
                reply = f"✅ 體重: {weight} 公斤\n\n📝 請輸入你的年齡(歲)\n例如: 30"
            else:
                reply = "⚠️ 體重數值似乎不合理\n請輸入 30-300 之間的數字"
        except ValueError:
            reply = "⚠️ 請輸入有效的數字\n例如: 70"
    
    elif state['step'] == 3:
        # 接收年齡
        try:
            age = int(user_message)
            if 10 <= age <= 120:
                user_states[user_id]['age'] = age
                user_states[user_id]['step'] = 4
                reply = f"✅ 年齡: {age} 歲\n\n📝 請輸入你的性別\n請輸入: 男 或 女"
            else:
                reply = "⚠️ 年齡數值似乎不合理\n請輸入 10-120 之間的數字"
        except ValueError:
            reply = "⚠️ 請輸入有效的數字\n例如: 30"
    
    elif state['step'] == 4:
        # 接收性別並計算結果
        if user_message in ['男', '女', 'male', 'female', 'M', 'F', 'm', 'f']:
            # 標準化性別輸入
            if user_message.lower() in ['男', 'male', 'm']:
                gender = '男'
            else:
                gender = '女'
            
            user_states[user_id]['gender'] = gender
            
            # 取得儲存的數據
            height_m = user_states[user_id]['height']
            weight = user_states[user_id]['weight']
            age = user_states[user_id]['age']
            
            # 計算身高公分(用於BMR計算)
            height_cm = height_m * 100
            
            # 計算 BMI 和 BMR
            bmi = calculate_bmi(height_m, weight)
            bmr = calculate_bmr(weight, height_cm, age, gender)
            
            # 生成建議
            reply = get_diet_advice(bmi, bmr, height_m, weight)
            
            # 重置狀態
            user_states[user_id] = {'step': 0}
        else:
            reply = "⚠️ 請輸入有效的性別\n請輸入: 男 或 女"
    
    else:
        reply = "💬 輸入「開始」開始健康分析\n💬 輸入「說明」查看使用說明"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/")
def home():
    return "健康數據管家 LINE Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)