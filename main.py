from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import datetime
import os
import json

# Konfigurasi langsung (tanpa .env)
BOT_TOKEN = "7643106737:AAHy3pJ_b5Hm6kuRUtSLtNt1jkby8c8zQqg"
API_ID = 23844837  # GANTI
API_HASH = "b6cc42d1a8f7b5b29777dc731343f1d4"
OWNER_ID = 7743291841  # GANTI ID TELEGRAMMU

app = Client("ocrbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

IZIN_FILE = "akses.json"
if not os.path.exists(IZIN_FILE):
    with open(IZIN_FILE, "w") as f:
        json.dump({}, f)

def load_izin():
    with open(IZIN_FILE) as f:
        return json.load(f)

def save_izin(data):
    with open(IZIN_FILE, "w") as f:
        json.dump(data, f)

def check_izin(user_id):
    izin = load_izin()
    user_id = str(user_id)
    if user_id not in izin:
        return False
    batas = datetime.datetime.strptime(izin[user_id], "%Y-%m-%d")
    return datetime.datetime.now() <= batas

@app.on_message(filters.command("adduser") & filters.user(OWNER_ID))
def add_user(_, msg: Message):
    try:
        _, uid, hari = msg.text.split()
        batas = (datetime.datetime.now() + datetime.timedelta(days=int(hari))).strftime("%Y-%m-%d")
        izin = load_izin()
        izin[uid] = batas
        save_izin(izin)
        msg.reply(f"✅ Akses diberikan ke {uid} sampai {batas}")
    except:
        msg.reply("❌ Format salah. Gunakan: /adduser <id> <hari>")

@app.on_message(filters.command("hapusakses") & filters.user(OWNER_ID))
def hapus_akses(_, msg: Message):
    try:
        _, uid = msg.text.split()
        izin = load_izin()
        if uid in izin:
            del izin[uid]
            save_izin(izin)
            msg.reply(f"✅ Akses {uid} berhasil dihapus.")
        else:
            msg.reply("❌ ID tidak ditemukan.")
    except:
        msg.reply("❌ Format salah. Gunakan: /hapusakses <id>")

@app.on_message(filters.command("cekakses"))
def cek_akses(_, msg: Message):
    izin = load_izin()
    uid = str(msg.from_user.id)
    if uid in izin:
        msg.reply(f"✅ Akses aktif sampai: {izin[uid]}")
    else:
        msg.reply("❌ Kamu belum diberi akses.")

@app.on_message(filters.command("help"))
def help_command(_, msg: Message):
    msg.reply(
        "**📖 Panduan Bot OCR Edit Gambar**\n\n"
        "**Owner Commands:**\n"
        "`/adduser <id> <hari>` ➜ Beri akses user\n"
        "`/hapusakses <id>` ➜ Hapus akses user\n\n"
        "**User Commands:**\n"
        "`/cekakses` ➜ Lihat status akses\n"
        "`/editprofilegroup [ID|ENG|MY] jumlah`\n\n"
        "**Cara Pakai:**\n"
        "1. Kirim gambar grup.\n"
        "2. Balas gambar dengan perintah:\n"
        "`/editprofilegroup [ID] 50`"
    )

@app.on_message(filters.command("editprofilegroup") & filters.reply)
def edit_profile(_, msg: Message):
    if not check_izin(msg.from_user.id):
        return msg.reply("❌ Kamu belum diberi akses.")

    if not msg.reply_to_message.photo:
        return msg.reply("❌ Balas ke gambar yang ingin diedit.")

    try:
        _, lang, jumlah = msg.text.split()
        jumlah = int(jumlah)
        lang = lang.upper().replace("[", "").replace("]", "")

        teks_baru = {
            "ID": f"Grup • {jumlah} anggota",
            "ENG": f"Group • {jumlah} members",
            "MY": f"Kumpulan • {jumlah} ahli"
        }.get(lang, f"Group • {jumlah} members")

        # Simpan gambar
        path = f"image_{msg.from_user.id}.jpg"
        msg.reply_to_message.download(file_name=path)

        image = Image.open(path)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("font.ttf", size=32)

        target = None
        for i in range(len(data['text'])):
            if "grup" in data['text'][i].lower() or "group" in data['text'][i].lower():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                target = (x, y, w, h)
                break

        if not target:
            return msg.reply("❌ Tidak menemukan teks seperti 'Grup • xx anggota'.")

        x, y, w, h = target
        draw.rectangle([x - 10, y - 10, x + w + 10, y + h + 10], fill="white")
        draw.text((x, y), teks_baru, font=font, fill="black")

        output_path = f"edited_{msg.from_user.id}.jpg"
        image.save(output_path)
        msg.reply_photo(output_path, caption="✅ Gambar berhasil diedit.")

        os.remove(path)
        os.remove(output_path)
    except Exception as e:
        msg.reply(f"❌ Error: {e}")

@app.on_message(filters.photo)
def auto_instruction(_, msg: Message):
    if check_izin(msg.from_user.id):
        msg.reply("📸 Gambar diterima.\nBalas gambar ini dengan:\n`/editprofilegroup [ID] 50`")
    else:
        msg.reply("🔒 Kirim `/cekakses` untuk memeriksa apakah kamu punya izin.")

@app.on_message(filters.command("start"))
def start(_, msg: Message):
    msg.reply("👋 Kirim gambar dan balas dengan:\n`/editprofilegroup [ID|ENG|MY] jumlah`\nGunakan `/help` untuk bantuan.")

app.run()
