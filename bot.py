import telebot
from telebot import types
from telebot.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
import json
import traceback
import os
import shutil
import threading
import time

API_TOKEN = '7729478160:AAGBlV8QV8IF7XLV7esZZRSxFBCYLlERhq8'  # استبدل بـ API Token الخاص بك
bot = telebot.TeleBot(API_TOKEN)

DEVELOPER_ID = 5859412391  # استبدل بـ ID المطور

STATS_FILE = 'stats.json'
BACKUP_STATS_FILE = 'backup_stats.json'
BAN_FILE = 'global_ban_list.json'
ADMIN_COUNT_FILE = 'admin_count.json'
ADMIN_DATA_FILE = 'admin_data.json'
IMAGE_FILE = 'welcome_image.jpg'
broadcasting_status = False
current_message = ""
current_message_type = ""  # "individual" أو "group"
broadcast_recipient = ""  # "users" أو "groups"

# تحميل قائمة الكتم من ملف
def load_mute_list():
    if os.path.exists("global_mute_list.json"):
        with open("global_mute_list.json", "r") as file:
            return json.load(file)
    return []

# حفظ قائمة الكتم إلى ملف
def save_mute_list(mute_list):
    with open("global_mute_list.json", "w") as file:
        json.dump(mute_list, file)


# تحميل البيانات
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as file:
            return json.load(file)
    else:
        return {"active_groups": [], "private_users": []}

def load_ban_list():
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, 'r') as file:
            return json.load(file)
    return []

# حفظ البيانات
def save_stats(stats):
    with open(STATS_FILE, 'w') as file:
        json.dump(stats, file)

def save_ban_list(ban_list):
    with open(BAN_FILE, 'w') as file:
        json.dump(ban_list, file)

# تحميل وإدارة الإحصائيات
stats = load_stats()
global_ban_list = load_ban_list()
global_mute_list = load_mute_list()





# تحديث قائمة المجموعات المفعّلة
def update_active_groups():
    updated_groups = []
    for chat_id in stats["active_groups"]:
        try:
            bot.get_chat(chat_id)
            updated_groups.append(chat_id)
        except telebot.apihelper.ApiException:
            bot.send_message(DEVELOPER_ID, f"تم حذف بيانات المجموعة {chat_id} لأنها لم تعد متاحة.")
    
    stats["active_groups"] = updated_groups
    save_stats(stats)




# تفعيل المجموعة من قبل المطورين أو المشرفين فقط
@bot.message_handler(func=lambda message: message.text == "تفعيل")
def activate_group(message):
    if message.chat.type in ["group", "supergroup"]:
        # التحقق مما إذا كان المستخدم مطور السورس أو مشرف
        if message.from_user.id == DEVELOPER_ID:
            # المطور لديه الإذن تلقائيًا
            activate_bot_in_group(message)
        else:
            # التحقق مما إذا كان المستخدم مشرفًا
            chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
            if chat_member.status in ['administrator', 'creator']:
                activate_bot_in_group(message)
            else:
                bot.reply_to(message, "يجب أن تكون مسؤولاً أو مطوراً لتفعيل البوت.")

def activate_bot_in_group(message):
    if message.chat.id not in stats["active_groups"]:
        stats["active_groups"].append(message.chat.id)
        save_stats(stats)
        bot.reply_to(message, "تم تفعيل البوت في هذه المجموعة.")
    else:
        bot.reply_to(message, "البوت مفعل مسبقاً في هذه المجموعة.")

# إلغاء تفعيل المجموعة (فقط للمطور)
@bot.message_handler(func=lambda message: message.text == "إلغاء تفعيل" and message.from_user.id == DEVELOPER_ID)
def deactivate_group(message):
    if message.chat.type in ["group", "supergroup"]:
        if message.chat.id in stats["active_groups"]:
            stats["active_groups"].remove(message.chat.id)
            save_stats(stats)
            bot.reply_to(message, "تم إلغاء تفعيل البوت في هذه المجموعة.")
        else:
            bot.reply_to(message, "البوت غير مفعل في هذه المجموعة.")

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "رجوع")
def send_welcome(message):
    # إنشاء لوحة المفاتيح للمطور
    dev_buttons = [
        ["قسم الصوره"],
        ["قسم العام", "قسم الاحصائيات"],
        ["قسم الاذاعه"]
    ]
    markup_dev = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for row in dev_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_dev.add(*buttons)

    # إنشاء لوحة المفاتيح للمستخدم العادي
    user_buttons = [
        ["معرفي"],
        # يمكنك إضافة المزيد من الأزرار هنا إذا لزم الأمر
    ]
    markup_user = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for row in user_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_user.add(*buttons)

    # إرسال الرسالة حسب توفر الصورة وحسب نوع المستخدم
    if os.path.exists(IMAGE_FILE):
        with open(IMAGE_FILE, 'rb') as image:
            bot.send_photo(
                message.chat.id, image, caption="مرحباً بك في البوت!",
                reply_markup=markup_dev if message.from_user.id == DEVELOPER_ID else markup_user
            )
    else:
        bot.send_message(
            message.chat.id, "مرحباً بك في البوت! لا توجد صورة متاحة.",
            reply_markup=markup_dev if message.from_user.id == DEVELOPER_ID else markup_user
        )

    # تسجيل المستخدم في الإحصائيات
    if message.from_user.id not in stats["private_users"]:
        stats["private_users"].append(message.from_user.id)
        save_stats(stats)


@bot.message_handler(func=lambda message: message.text == "قسم الصوره" and message.from_user.id == DEVELOPER_ID)
def show_dev_keyboard(message):
    # إنشاء لوحة المفاتيح للمطور
    dev_buttons = [
        ["إضافة صورة", "حذف الصورة"],
        ["رجوع"]
    ]
    markup_dev = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for row in dev_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_dev.add(*buttons)

    bot.send_message(message.chat.id, "اهلا بك في قسم تغيير الصوره", reply_markup=markup_dev)

@bot.message_handler(func=lambda message: message.text == "قسم العام" and message.from_user.id == DEVELOPER_ID)
def show_dev_keyboard(message):
    # إنشاء لوحة المفاتيح للمطور
    dev_buttons = [
        ["حظر عام", "كتم عام"],
        ["الغاء الحظر العام", "الغاء الكتم العام"],
        ["معلومات الحظر","معلومات الكتم"],
        ["رجوع"]
    ]
    markup_dev = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for row in dev_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_dev.add(*buttons)

    bot.send_message(message.chat.id, "اهلا بك فى قسم الكتم و الحظر العام", reply_markup=markup_dev)


@bot.message_handler(func=lambda message: message.text == "قسم الاحصائيات" and message.from_user.id == DEVELOPER_ID)
def show_dev_keyboard(message):
    # إنشاء لوحة المفاتيح للمطور
    dev_buttons = [
        ["رفع النسخة الاحتياطية", "جلب النسخة الاحتياطية"],
        ["الإحصائيات"],
        ["رجوع"]
    ]
    markup_dev = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for row in dev_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_dev.add(*buttons)

    bot.send_message(message.chat.id, "اهلا بك في قسم الاحصائيات", reply_markup=markup_dev)

@bot.message_handler(func=lambda message: message.text == "قسم الاذاعه" and message.from_user.id == DEVELOPER_ID)
def show_dev_keyboard(message):
    # إنشاء لوحة المفاتيح للمطور
    dev_buttons = [
        ["اذاعه للاشخاص", "اذاعه للمجموعات"],
        ["اذاعة بالتثبيت للمجموعات"],
        ["إلغاء الأمر"],
        ["رجوع"]
    ]
    markup_dev = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for row in dev_buttons:
        buttons = [types.KeyboardButton(text) for text in row]
        markup_dev.add(*buttons)

    bot.send_message(message.chat.id, "اهلا بك في قسم الاذاعه", reply_markup=markup_dev)



# تعريف الـ ID الخاص بمطور السورس
DEVELOPER_ID = 5859412391

# دالة التأكد من تفعيل البوت في المجموعة
def is_group_active(chat_id):
    stats = load_stats()
    return chat_id in stats.get("active_groups", [])

# دالة لإنشاء زر التفعيل
def create_xero_button():
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("XERO", url="https://t.me/X_YOTOP")
    markup.add(button)
    return markup

# دالة لحفظ معلومات الأدمنين مع اسم المجموعة في ملف مختلف
def save_admin_v2_info(chat_id, user_id, name, group_title):
    try:
        # تحميل جميع بيانات الأدمنين لكل المجموعات
        with open("all_admin_v2.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        all_data = {}

    if str(chat_id) not in all_data:
        all_data[str(chat_id)] = {"group_title": group_title, "admins": []}
    
    admin_data = all_data[str(chat_id)]["admins"]
    if not any(admin["id"] == user_id for admin in admin_data):
        admin_data.append({"id": user_id, "name": name})

    all_data[str(chat_id)]["admins"] = admin_data

    try:
        with open("all_admin_v2.json", 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print("خطأ أثناء حفظ معلومات الأدمنين:", e)

# دالة لتحميل معلومات الأدمنين
def load_admin_v2_info(chat_id):
    try:
        with open("all_admin_v2.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        group_data = data.get(str(chat_id), {})
        return group_data.get("admins", [])
    except json.JSONDecodeError as e:
        print(f"خطأ في قراءة الملف: {e}")
        return []
    except Exception as e:
        print(f"حدث خطأ غير متوقع أثناء تحميل البيانات: {e}")
        return []




# دالة لحذف المشرف من ملف المشرفين (في حالة تمت ترقيته كأدمن)
def remove_superadmin_info(chat_id, user_id):
    try:
        with open("all_admins.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)
        
        if str(chat_id) in all_data:
            all_data[str(chat_id)]["admins"] = [
                admin for admin in all_data[str(chat_id)]["admins"] if admin["id"] != user_id
            ]
            
            with open("all_admins.json", 'w', encoding='utf-8') as file:
                json.dump(all_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print("خطأ أثناء حذف المشرف من الملف:", e)

# تعديل دالة رفع أدمن
def promote_to_admin_v2(message):
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    group_title = message.chat.title

    bot_member = bot.get_chat_member(chat_id, bot.get_me().id)
    if bot_member.status != 'administrator' or not bot_member.can_promote_members:
        bot.reply_to(message, "ليس لدي صلاحية إضافة أدمنين.", reply_markup=create_xero_button())
        return

    try:
        member_status = bot.get_chat_member(chat_id, user_id).status
        if member_status in ['administrator', 'creator']:
            existing_admins = load_admin_info(chat_id)
            if not any(admin["id"] == user_id for admin in existing_admins):
                bot.reply_to(
                    message, 
                    "المستخدم بالفعل مشرف في المجموعة ولكن ليس عن طريق البوت. يرجى تنزيله أولاً ثم رفعه من خلال البوت.", 
                    reply_markup=create_xero_button()
                )
                return

        # إذا كان المستخدم موجودًا في ملف المشرفين، نحذفه منه
        remove_superadmin_info(chat_id, user_id)

        # نرفع المستخدم كأدمن
        bot.promote_chat_member(
            chat_id, user_id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_video_chats=True
        )
        
        bot.reply_to(message, f"تم رفع {message.reply_to_message.from_user.first_name} كأدمن.", reply_markup=create_xero_button())
        save_admin_v2_info(chat_id, user_id, message.reply_to_message.from_user.first_name, group_title)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء رفع المستخدم: {e}", reply_markup=create_xero_button())

# دالة لتنزيل أدمن
def demote_from_admin_v2(message):
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        # التحقق إذا كان المستخدم أدمن مرفوع عبر البوت
        existing_admins = load_admin_v2_info(chat_id)
        if not any(admin["id"] == user_id for admin in existing_admins):
            # إذا كان أدمن ولكن ليس عبر البوت
            member_status = bot.get_chat_member(chat_id, user_id).status
            if member_status in ['administrator', 'creator']:
                bot.reply_to(message, "نتأسف لحضرتك لا يمكن تنزيله لعدم رفعه ادمن من خلال البوت.", reply_markup=create_xero_button())
                return
            # إذا لم يكن أدمن أساسًا
            bot.reply_to(message, "الشخص ليس أدمنًا حتى أتمكن من تنزيله.", reply_markup=create_xero_button())
            return

        # تنزيل صلاحيات الأدمن
        bot.promote_chat_member(
            chat_id, user_id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_video_chats=False
        )
        bot.reply_to(message, f"تم إزالة صلاحيات {message.reply_to_message.from_user.first_name}.", reply_markup=create_xero_button())
        
        # حذف بيانات الأدمن من الملف
        remove_admin_v2_info(chat_id, user_id)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء إزالة الصلاحيات: {e}", reply_markup=create_xero_button())

# دالة لإزالة معلومات الأدمن من المجموعة
def remove_admin_v2_info(chat_id, user_id):
    try:
        with open("all_admin_v2.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)

        if not isinstance(all_data.get(str(chat_id)), dict):
            all_data[str(chat_id)] = {"group_title": "Unknown", "admins": []}

        all_data[str(chat_id)]["admins"] = [admin for admin in all_data[str(chat_id)]["admins"] if admin["id"] != user_id]

        with open("all_admin_v2.json", 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print("خطأ أثناء إزالة معلومات الأدمن:", e)

# دالة لعرض معلومات الأدمنين المرفوعين عبر البوت
def admin_v2_info(message):
    chat_id = message.chat.id
    admins = load_admin_v2_info(chat_id)
    
    if not admins:
        bot.reply_to(message, "لا يوجد أدمنين مرفوعين عبر البوت في هذه المجموعة.", reply_markup=create_xero_button())
        return
    
    response = "قائمة الأدمنين المرفوعين عبر البوت:\n"
    for admin in admins:
        response += f"- {admin['name']} (ID: {admin['id']})\n"
    
    bot.reply_to(message, response, reply_markup=create_xero_button())

# دالة للتحقق من صلاحيات المستخدمين
def is_authorized_v2(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # تحقق إذا كان المستخدم هو مطور السورس
        if user_id == DEVELOPER_ID:
            return True

        # تحقق إذا كان المستخدم هو مالك المجموعة
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id and admin.status == 'creator':
                return True

        # تحقق إذا كان المستخدم مشرفًا تم رفعه عبر البوت في هذه المجموعة
        existing_admins = load_admin_info(chat_id)
        if any(admin["id"] == user_id for admin in existing_admins):
            return True

        return False
    except Exception as e:
        print(f"خطأ أثناء التحقق من صلاحيات المستخدم: {e}")
        return False





# دالة التأكد من تفعيل البوت في المجموعة
def is_group_active(chat_id):
    stats = load_stats()
    return chat_id in stats.get("active_groups", [])

# دالة لإنشاء زر التفعيل
def create_xero_button():
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("XERO", url="https://t.me/X_YOTOP")
    markup.add(button)
    return markup

# دالة لحفظ معلومات المشرفين مع اسم المجموعة
def save_admin_info(chat_id, user_id, name, group_title):
    print(f"بدء حفظ المشرف: {name} (ID: {user_id}) للمجموعة: {chat_id} ({group_title})")
    try:
        # تحميل جميع بيانات المشرفين لكل المجموعات
        with open("all_admins.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        all_data = {}

    # الحصول على بيانات المجموعة أو إنشاء قائمة جديدة إذا لم تكن موجودة
    if str(chat_id) not in all_data:
        all_data[str(chat_id)] = {"group_title": group_title, "admins": []}
    
    # التحقق من عدم وجود المشرف مسبقًا لتجنب التكرار
    admin_data = all_data[str(chat_id)]["admins"]
    if not any(admin["id"] == user_id for admin in admin_data):
        admin_data.append({"id": user_id, "name": name})

    # تحديث بيانات المجموعة في الملف
    all_data[str(chat_id)]["admins"] = admin_data

    # حفظ التحديثات إلى الملف
    try:
        with open("all_admins.json", 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
            print(f"تم حفظ المشرف: {name} بنجاح")
    except Exception as e:
        print("خطأ أثناء حفظ معلومات المشرفين:", e)

# دالة لتحميل معلومات المشرفين
def load_admin_info(chat_id):
    print(f"تحميل معلومات المشرفين للمجموعة: {chat_id}")
    try:
        # التأكد من وجود الملف أولاً
        try:
            with open("all_admins.json", 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            print("الملف 'all_admins.json' غير موجود. سيتم إنشاؤه.")
            data = {}  # إذا كان الملف غير موجود، نعيد تعيين البيانات كقائمة فارغة

        # التأكد من وجود بيانات المجموعة
        group_data = data.get(str(chat_id), {})
        if group_data:
            admins = group_data.get("admins", [])
            if admins:
                print(f"تم تحميل البيانات بنجاح: {group_data}")
                return admins
            else:
                print(f"لا يوجد مشرفين في المجموعة: {chat_id}")
                return []  # إذا كانت القائمة فارغة، نرجع قائمة فارغة
        else:
            print(f"لا توجد بيانات للمجموعة: {chat_id}")
            return []  # إذا لم تكن هناك بيانات للمجموعة، نرجع قائمة فارغة

    except json.JSONDecodeError as e:
        print(f"خطأ في قراءة الملف: {e}")
        return []

    except Exception as e:
        print(f"حدث خطأ غير متوقع أثناء تحميل البيانات: {e}")
        return []



# دالة لحذف المستخدم من قائمة الأدمنين (في حالة تمت ترقيته كمشرف)
def remove_admin_infoxx(chat_id, user_id):
    try:
        with open("all_admin_v2.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)
        
        if str(chat_id) in all_data:
            all_data[str(chat_id)]["admins"] = [
                admin for admin in all_data[str(chat_id)]["admins"] if admin["id"] != user_id
            ]
            
            with open("all_admin_v2.json", 'w', encoding='utf-8') as file:
                json.dump(all_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print("خطأ أثناء حذف الأدمن من الملف:", e)

# تعديل دالة رفع مشرف
def promote_to_admin(message):
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    group_title = message.chat.title  # الحصول على اسم المجموعة

    bot_member = bot.get_chat_member(chat_id, bot.get_me().id)
    if bot_member.status != 'administrator' or not bot_member.can_promote_members:
        bot.reply_to(message, "ليس لدي صلاحية إضافة مشرفين.", reply_markup=create_xero_button())
        return

    try:
        # تحقق إذا كان الشخص أدمن بالفعل في المجموعة
        member_status = bot.get_chat_member(chat_id, user_id).status
        if member_status == 'administrator':
            # إذا كان المستخدم أدمن، نحذفه من قائمة الأدمنين
            remove_admin_infoxx(chat_id, user_id)

        # رفع المستخدم كمشرف
        bot.promote_chat_member(
            chat_id, user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_manage_video_chats=True,
            can_manage_topics=True
        )
        bot.reply_to(message, f"تم رفع {message.reply_to_message.from_user.first_name} كمسؤول.", reply_markup=create_xero_button())
        save_admin_info(chat_id, user_id, message.reply_to_message.from_user.first_name, group_title)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء رفع المستخدم: {e}", reply_markup=create_xero_button())

# دالة لتنزيل مشرف
def demote_from_admin(message):
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        # التحقق إذا كان المستخدم مشرفًا مرفوعًا عبر البوت
        existing_admins = load_admin_info(chat_id)
        if not any(admin["id"] == user_id for admin in existing_admins):
            # إذا كان مشرفًا ولكن ليس عبر البوت
            member_status = bot.get_chat_member(chat_id, user_id).status
            if member_status in ['administrator', 'creator']:
                bot.reply_to(message, "نتأسف لحضرتك لا يمكن تنزيله لعدم رفعه مشرف من خلال البوت.", reply_markup=create_xero_button())
                return
            # إذا لم يكن مشرفًا أساسًا
            bot.reply_to(message, "الشخص ليس مشرفًا حتى أتمكن من تنزيله.", reply_markup=create_xero_button())
            return

        # تنزيل صلاحيات المشرف
        bot.promote_chat_member(
            chat_id, user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_manage_video_chats=False,
            can_manage_topics=False
        )
        bot.reply_to(message, f"تم إزالة صلاحيات {message.reply_to_message.from_user.first_name}.", reply_markup=create_xero_button())
        
        # حذف بيانات المشرف من الملف
        remove_admin_info(chat_id, user_id)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء إزالة الصلاحيات: {e}", reply_markup=create_xero_button())



# دالة لإزالة معلومات المشرف من مجموعة محددة
def remove_admin_info(chat_id, user_id):
    print(f"بدء إزالة المشرف (ID: {user_id}) من المجموعة: {chat_id}")
    try:
        # تحميل جميع بيانات المشرفين لكل المجموعات
        with open("all_admins.json", 'r', encoding='utf-8') as file:
            all_data = json.load(file)

        # تأكد أن بيانات المجموعة هي كائن وليست قائمة
        if not isinstance(all_data.get(str(chat_id)), dict):
            print(f"بيانات المجموعة {chat_id} غير متوافقة، سيتم إعادة تعيينها كقائمة فارغة.")
            all_data[str(chat_id)] = {"group_title": "Unknown", "admins": []}

        # تصفية بيانات المشرفين للمجموعة المطلوبة
        all_data[str(chat_id)]["admins"] = [admin for admin in all_data[str(chat_id)]["admins"] if admin["id"] != user_id]

        # حفظ التحديثات إلى الملف
        with open("all_admins.json", 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
            print("تم إزالة المشرف بنجاح من المجموعة دون التأثير على المجموعات الأخرى")
    except Exception as e:
        print("خطأ أثناء إزالة معلومات المشرفين:", e)
        print("تفاصيل الخطأ:", traceback.format_exc())


def admin_info(message):
    chat_id = message.chat.id
    print("بدء جلب معلومات المشرفين")
    try:
        # تحميل معلومات المشرفين للمجموعة
        admins = load_admin_info(chat_id)

        if not admins:
            bot.reply_to(message, "لا يوجد مشرفين في هذه المجموعة.", reply_markup=create_xero_button())
            return

        # إذا تم العثور على مشرفين
        group_title = message.chat.title
        response = f"مشرفو المجموعة {group_title}:\n"
        for admin in admins:
            response += f"- ID: {admin['id']}\n    Name: {admin['name']}\n\n"  # إضافة مسافة أكبر بين الـ ID والـ Name
        
        # إضافة الرد مع زر XERO
        bot.reply_to(message, response, reply_markup=create_xero_button())

    except Exception as e:
        print("حدث خطأ أثناء جلب معلومات المشرفين:", e)
        bot.reply_to(message, "حدث خطأ أثناء جلب معلومات المشرفين.", reply_markup=create_xero_button())

DEVELOPER_ID = 5859412391

def is_authorized(message):
    try:
        # جلب قائمة المشرفين
        admins = bot.get_chat_administrators(message.chat.id)

        # التحقق إذا كان المستخدم هو المطور بناءً على الـ ID فقط
        if message.from_user.id == DEVELOPER_ID:
            return True  # السماح للمطور بالتحكم في الأوامر

        # التحقق إذا كان المستخدم هو مالك المجموعة (creator) فقط
        for admin in admins:
            if admin.user.id == message.from_user.id:
                if admin.status == 'creator':  # السماح لمالك المجموعة فقط
                    return True

        return False
    except Exception as e:
        print(f"خطأ أثناء التحقق من صلاحيات المستخدم: {e}")
        return False

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_admin_commands(message):
    if not is_group_active(message.chat.id):
        bot.reply_to(message, "رجاء تفعيل البوت في المجموعة أولاً.")
        return

    if message.text == "رفع مشرف":
        if not is_authorized(message):
            bot.reply_to(message, "أنت غير مخول لرفع مشرفين.", reply_markup=create_xero_button())
            return
        promote_to_admin(message)

    elif message.text == "تنزيل مشرف":
        if not is_authorized(message):
            bot.reply_to(message, "أنت غير مخول لتنزيل المشرفين.", reply_markup=create_xero_button())
            return
        demote_from_admin(message)

    elif message.text == "معلومات المشرفين":
        if not is_authorized(message):
            bot.reply_to(message, "أنت غير مخول لعرض معلومات المشرفين.", reply_markup=create_xero_button())
            return
        admin_info(message)
        
    elif message.text == "رفع ادمن":
        if not is_authorized_v2(message):
            bot.reply_to(message, "أنت غير مخول لرفع أدمنين.", reply_markup=create_xero_button())
            return
        promote_to_admin_v2(message)

    elif message.text == "تنزيل ادمن":
        if not is_authorized_v2(message):
            bot.reply_to(message, "أنت غير مخول لتنزيل الأدمنين.", reply_markup=create_xero_button())
            return
        demote_from_admin_v2(message)

    elif message.text == "معلومات الادمنين":
        if not is_authorized_v2(message):
            bot.reply_to(message, "أنت غير مخول لعرض معلومات الأدمنين.", reply_markup=create_xero_button())
            return
        admin_v2_info(message)







# إضافة وحذف الصورة
@bot.message_handler(func=lambda message: message.text == "إضافة صورة" and message.from_user.id == DEVELOPER_ID)
def add_image(message):
    bot.send_message(message.chat.id, "يرجى إرسال الصورة التي تريد وضعها كصورة ترحيب.")
    bot.register_next_step_handler(message, process_add_image)

def process_add_image(message):
    if message.content_type == 'photo':
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(IMAGE_FILE, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, "تم إضافة الصورة بنجاح!")
    else:
        bot.send_message(message.chat.id, "يرجى إرسال صورة فقط.")

@bot.message_handler(func=lambda message: message.text == "حذف الصورة" and message.from_user.id == DEVELOPER_ID)
def delete_image(message):
    if os.path.exists(IMAGE_FILE):
        os.remove(IMAGE_FILE)
        bot.send_message(message.chat.id, "تم حذف الصورة بنجاح.")
    else:
        bot.send_message(message.chat.id, "لا توجد صورة لإزالتها.")

# الإحصائيات للمطور
@bot.message_handler(func=lambda message: message.text == "الإحصائيات" and message.chat.type == "private" and message.from_user.id == DEVELOPER_ID)
def stats_message(message):
    active_groups_count = len(stats["active_groups"])
    private_users_count = len(stats["private_users"])
    bot.send_message(message.chat.id, f"عدد المجموعات المفعلة: {active_groups_count}\nعدد المستخدمين في الخاص: {private_users_count}")

# النسخة الاحتياطية وجلب النسخة
@bot.message_handler(func=lambda message: message.text == "جلب النسخة الاحتياطية" and message.from_user.id == DEVELOPER_ID)
def download_backup_command(message):
    try:
        shutil.copy(STATS_FILE, BACKUP_STATS_FILE)
        bot.send_document(message.chat.id, open(BACKUP_STATS_FILE, 'rb'))
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء تحميل النسخة الاحتياطية: {e}")

@bot.message_handler(func=lambda message: message.text == "رفع النسخة الاحتياطية" and message.from_user.id == DEVELOPER_ID)
def request_backup_upload(message):
    bot.send_message(message.chat.id, "الرجاء إرسال النسخة الاحتياطية بامتداد .json.")
    bot.register_next_step_handler(message, process_backup)

def process_backup(message):
    if message.content_type == 'document' and message.document.file_name.endswith('.json'):
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(STATS_FILE, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            # تحميل النسخة الاحتياطية بعد تحديث الملف
            global stats
            stats = load_stats()
            bot.send_message(message.chat.id, "تم رفع النسخة الاحتياطية بنجاح وتحديث الإحصائيات.")
        except telebot.apihelper.ApiException as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء تحميل الملف: {e}")
    else:
        bot.send_message(message.chat.id, "تم إلغاء الأمر لعدم إرسال ملف بامتداد .json.")


@bot.message_handler(func=lambda message: message.text == "اذاعه للاشخاص" and message.from_user.id == DEVELOPER_ID)
def initiate_broadcast(message):
    bot.send_message(message.chat.id, "يرجى إرسال رسالتك للإذاعة.")

    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.text == "إلغاء الأمر":
        bot.send_message(message.chat.id, "تم إلغاء الأمر.")
        return

    # هنا يمكنك إضافة منطق إرسال الرسالة إلى الأعضاء
    sent_count = send_broadcast_to_users(message.text)
    bot.send_message(message.chat.id, f"تم إرسال الرسالة إلى {sent_count} شخص.")

def send_broadcast_to_users(text):
    # الكود الخاص بإرسال الرسالة لجميع الأعضاء
    count = 0
    # مثال على إرسال الرسالة، يجب تعديل هذا الكود ليعكس آلية الإرسال لديك
    for user_id in stats["private_users"]:
        try:
            bot.send_message(user_id, text)
            count += 1
        except Exception:
            continue
    return count

@bot.message_handler(func=lambda message: message.text == "اذاعه للمجموعات" and message.from_user.id == DEVELOPER_ID)
def initiate_group_broadcast(message):
    bot.send_message(message.chat.id, "يرجى إرسال رسالتك للإذاعة للمجموعات.")
    bot.register_next_step_handler(message, process_group_broadcast)

def process_group_broadcast(message):
    if message.text == "إلغاء الأمر":
        bot.send_message(message.chat.id, "تم إلغاء الأمر.")
        return

    # إرسال الرسالة إلى المجموعات
    sent_count_groups = send_broadcast_to_groups(message.text)
    bot.send_message(message.chat.id, f"تم إرسال الرسالة إلى {sent_count_groups} مجموعة.")

def send_broadcast_to_groups(text):
    count = 0
    for group_id in stats["active_groups"]:  # تأكد من أن القائمة هنا تتضمن معرفات المجموعات الفعلية
        try:
            bot.send_message(group_id, text)
            count += 1
        except Exception as e:
            continue  # تجاهل الأخطاء وواصل إلى المجموعة التالية
    return count

@bot.message_handler(func=lambda message: message.text == "اذاعة بالتثبيت للمجموعات" and message.from_user.id == DEVELOPER_ID)
def initiate_group_pinned_broadcast(message):
    bot.send_message(message.chat.id, "يرجى إرسال رسالتك للإذاعة بالتثبيت للمجموعات.")
    bot.register_next_step_handler(message, process_group_pinned_broadcast)

def process_group_pinned_broadcast(message):
    if message.text == "إلغاء الأمر":
        bot.send_message(message.chat.id, "تم إلغاء الأمر.")
        return

    # إرسال الرسالة إلى المجموعات مع تثبيتها
    sent_count_groups = send_pinned_broadcast_to_groups(message.text)
    bot.send_message(message.chat.id, f"تم إرسال الرسالة إلى {sent_count_groups} مجموعة وتثبيتها.")

def send_pinned_broadcast_to_groups(text):
    count = 0
    for group_id in stats["active_groups"]:  # تأكد من أن القائمة هنا تتضمن معرفات المجموعات الفعلية
        try:
            # إرسال الرسالة إلى المجموعة
            message = bot.send_message(group_id, text)
            # تثبيت الرسالة
            bot.pin_chat_message(group_id, message.message_id)
            count += 1
        except Exception as e:
            continue  # تجاهل الأخطاء وواصل إلى المجموعة التالية
    return count





# كود معلومات الحظر العام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "معلومات الحظر" and message.from_user.id == DEVELOPER_ID and message.chat.type == "private")
def get_ban_info(message):
    if global_ban_list:
        info = "قائمة الأشخاص المحظورين:\n"
        for user_id in global_ban_list:
            try:
                user = bot.get_chat(user_id)
                info += f"الاسم: {user.first_name} {user.last_name or ''} | المعرف: @{user.username or 'لا يوجد'} | الآي دي: {user_id}\n"
            except Exception:
                info += f"الآي دي: {user_id} (غير متاح)\n"
        bot.send_message(message.chat.id, info)
    else:
        bot.send_message(message.chat.id, "لا يوجد أي شخص محظور حالياً.")



# حظر عام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "حظر عام" and message.from_user.id == DEVELOPER_ID)
def global_ban(message):
    if message.reply_to_message:  # حظر من المجموعات
        user_id = message.reply_to_message.from_user.id
        if user_id not in global_ban_list:
            global_ban_list.append(user_id)
            save_ban_list(global_ban_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.reply_to(message, f"تم حظر المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.reply_to(message, "المستخدم محظور بالفعل.")
    else:  # حظر من الخاص
        bot.send_message(message.chat.id, "الرجاء إرسال معرف المستخدم لحظره.")
        bot.register_next_step_handler(message, process_global_ban)

def process_global_ban(message):
    try:
        user_id = int(message.text)
        if user_id not in global_ban_list:
            global_ban_list.append(user_id)
            save_ban_list(global_ban_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.send_message(message.chat.id, f"تم حظر المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.send_message(message.chat.id, "المستخدم محظور بالفعل.")
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إرسال معرف صالح.")

# إلغاء الحظر العام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "الغاء الحظر العام" and message.from_user.id == DEVELOPER_ID)
def global_unban(message):
    if message.reply_to_message:  # إلغاء الحظر من المجموعات
        user_id = message.reply_to_message.from_user.id
        if user_id in global_ban_list:
            global_ban_list.remove(user_id)
            save_ban_list(global_ban_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.reply_to(message, f"تم إلغاء حظر المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.reply_to(message, "المستخدم غير محظور.")
    else:  # إلغاء الحظر من الخاص
        bot.send_message(message.chat.id, "الرجاء إرسال معرف المستخدم لإلغاء الحظر.")
        bot.register_next_step_handler(message, process_global_unban)

def process_global_unban(message):
    try:
        user_id = int(message.text)
        if user_id in global_ban_list:
            global_ban_list.remove(user_id)
            save_ban_list(global_ban_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.send_message(message.chat.id, f"تم إلغاء حظر المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.send_message(message.chat.id, "المستخدم غير محظور.")
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إرسال معرف صالح.")




# كود معلومات الكتم العام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "معلومات الكتم" and message.from_user.id == DEVELOPER_ID and message.chat.type == "private")
def get_mute_info(message):
    if global_mute_list:
        info = "قائمة الأشخاص المكتومين:\n"
        for user_id in global_mute_list:
            try:
                user = bot.get_chat(user_id)
                info += f"الاسم: {user.first_name} {user.last_name or ''} | المعرف: @{user.username or 'لا يوجد'} | الآي دي: {user_id}\n"
            except Exception:
                info += f"الآي دي: {user_id} (غير متاح)\n"
        bot.send_message(message.chat.id, info)
    else:
        bot.send_message(message.chat.id, "لا يوجد أي شخص مكتوم حالياً.")


# كتم عام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "كتم عام" and message.from_user.id == DEVELOPER_ID)
def global_mute(message):
    if message.reply_to_message:  # كتم من المجموعات
        user_id = message.reply_to_message.from_user.id
        if user_id not in global_mute_list:
            global_mute_list.append(user_id)
            save_mute_list(global_mute_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.reply_to(message, f"تم كتم المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.reply_to(message, "المستخدم كتم بالفعل.")
    else:  # كتم من الخاص
        bot.send_message(message.chat.id, "الرجاء إرسال معرف المستخدم لكتمه.")
        bot.register_next_step_handler(message, process_global_mute)

def process_global_mute(message):
    try:
        user_id = int(message.text)
        if user_id not in global_mute_list:
            global_mute_list.append(user_id)
            save_mute_list(global_mute_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.send_message(message.chat.id, f"تم كتم المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.send_message(message.chat.id, "المستخدم كتم بالفعل.")
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إرسال معرف صالح.")

# إلغاء الكتم العام (خاص فقط)
@bot.message_handler(func=lambda message: message.text == "الغاء الكتم العام" and message.from_user.id == DEVELOPER_ID)
def global_unmute(message):
    if message.reply_to_message:  # إلغاء الكتم من المجموعات
        user_id = message.reply_to_message.from_user.id
        if user_id in global_mute_list:
            global_mute_list.remove(user_id)
            save_mute_list(global_mute_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.reply_to(message, f"تم إلغاء كتم المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.reply_to(message, "المستخدم غير كتم.")
    else:  # إلغاء الكتم من الخاص
        bot.send_message(message.chat.id, "الرجاء إرسال معرف المستخدم لإلغاء كتمه.")
        bot.register_next_step_handler(message, process_global_unmute)

def process_global_unmute(message):
    try:
        user_id = int(message.text)
        if user_id in global_mute_list:
            global_mute_list.remove(user_id)
            save_mute_list(global_mute_list)
            group_count = len(bot.get_chat_administrators(message.chat.id))  # عدد المجموعات التي فيها البوت مشرف
            bot.send_message(message.chat.id, f"تم إلغاء كتم المستخدم {user_id} من جميع المجموعات ({group_count} مجموعة).")
        else:
            bot.send_message(message.chat.id, "المستخدم غير كتم.")
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إرسال معرف صالح.")

# مراقبة الرسائل في المجموعات
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.from_user.id in global_mute_list:
        bot.delete_message(message.chat.id, message.message_id)



# تحقق دوري من الحظر العام وتطبيقه على جميع المجموعات
def enforce_global_ban():
    while True:
        for chat_id in stats["active_groups"]:
            for user_id in global_ban_list:
                try:
                    member = bot.get_chat_member(chat_id, user_id)
                    if member.status not in ['administrator', 'creator']:
                        bot.kick_chat_member(chat_id, user_id)
                except telebot.apihelper.ApiException as e:
                    bot.send_message(DEVELOPER_ID, f"خطأ عند محاولة طرد المستخدم {user_id} من المجموعة {chat_id}: {e}")
        time.sleep(5)

# تحديث مستمر للإحصائيات
def update_stats():
    while True:
        update_active_groups()
        save_stats(stats)
        time.sleep(5)

# تشغيل التحديث التلقائي للحظر العام
threading.Thread(target=enforce_global_ban, daemon=True).start()
threading.Thread(target=update_stats, daemon=True).start()

# تشغيل البوت
bot.infinity_polling()
