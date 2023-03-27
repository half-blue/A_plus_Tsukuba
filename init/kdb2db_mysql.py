import json
import uuid
import MySQLdb

# Dockerコンテナのためのデフォルト値を設定しています，
# 必要に応じて変更してください
HOST = "my_sql"
PORT = 3306
DB = "vhoi5_aplus_tsukuba"
USER = "root"
PASSWORD = "rootpass"

conn = MySQLdb.connect(host=HOST, port=PORT, db=DB, user=USER, password=PASSWORD, 
                       use_unicode=True, charset="utf8")
cur = conn.cursor()

with open("init/kdb.json","r", encoding="utf-8") as f:
    kdb = json.load(f)

print("講義データベース・スレッド生成プログラム MySQL Version")
print(f"kdb.json Updated at {kdb['updated']}")

print("スレッド生成を開始します。")
print("科目名と教員が同じ講義は同じスレッドになります。")

subdic = dict()
pk = 1

for sub in kdb["subject"]:
    thread_id = pk
    key = f"{sub[1]}({sub[8]})" # 講義名と教員名が同じ科目は同じとみなす。
    if not key in subdic.keys():
        cur.execute("insert into board_thread(id, title) values (%s, %s);", (pk, key))
        subdic[key] = pk
        pk += 1
    else:
        cur.execute("select thread_id_id from board_subject where name=%s and teachers = %s;", (sub[1], sub[8]))
        thread_id = cur.fetchall()[0][0]

    col = [sub[0], sub[1], sub[8], sub[13], sub[14], sub[15], thread_id]
    cur.execute("insert into board_subject("
    + "code,name,teachers,subtype,schools,colleges,thread_id_id"
    + ") values (%s,%s,%s,%s,%s,%s,%s);", col)

print("スレッド生成が完了しました。") 
print("システムメッセージを生成します。")

for pk in subdic.values():
    cur.execute("select name,teachers from board_subject where thread_id_id = %s;", (pk,))
    name, teachers = cur.fetchone()
    cur.execute("select code from board_subject where thread_id_id = %s;",(pk,))
    codes = ""
    for c in cur.fetchall():
        codes += c[0] + ","
    codes = codes[:-1]
    msg = f"ここは「{name}」について相談するスレッドです。\n" 
    msg += f"この講義の担当教員は「{teachers}」です。\n" 
    msg += f"科目番号は「{codes}」に対応します。\n\n"
    msg += f"気軽に話し合いましょう！！"
    sender_name = "system"
    emotion = 3
    post_id = str(uuid.uuid4()).replace("-","")
    col = (post_id, sender_name, emotion, msg, pk)
    cur.execute("insert into board_post(post_id,sender_name, emotion, text, thread_id, created_at) values(%s,%s,%s,%s,%s,NOW());", col)

print("システムメッセージ生成が完了しました。")

conn.commit()
conn.close()

