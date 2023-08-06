Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        const thread_id = document.getElementById('thread_id').value;
        return {
            subthreads: [],         //サブスレッドのjson配列
            replies: {},            //リプライの辞書 replies[post_id]=replyのjson
            thread_id: thread_id,   //スレッドID
            FETCH_INTERVAL : 3000,  //自動更新頻度(ms)
        };
    },
    methods: {
        async fetchSubthreads(thread_id) {
            //指定したスレッドのサブスレッド一覧をフェッチする
            const res = await axios.get(
                `/api/get_subthreads?thread_id=${thread_id}`
            );
            this.subthreads = res.data || [];
        },
        async fetchReplies(post_id) {
            //指定したサブスレッドのリプライ一覧をフェッチする
            const res = await axios.get(
                `/api/get_replies?post_id=${post_id}`
            );
            this.replies[post_id] = res.data || [];
        },
        getReplyCount(post_id) {
            //指定したサブスレッドの現在のリプライ数を取得する
            if(this.replies[post_id]) {
                return this.replies[post_id].length;
            }else{
                return 0;
            }
        },
        formatTimeString(time) {
            //ISO 8601形式のtimeを表示用のテキストに変換する。
            const ts = Date.parse(time);
            const date = new Date(ts);

            const month = date.getMonth() + 1;
            const year = date.getFullYear();
            const day = date.getDate();
            const hour = date.getHours().toString().padStart(2, '0');
            const min = date.getMinutes().toString().padStart(2, '0');

            return `${year}/${month}/${day} ${hour}:${min}`;
        },
        getEmotionBadgeClass(emotion_code) {
            //emotion_codeからバッチスタイルを得る
            const emotion_class_dict = {
                0: 'badge rounded-pill bg-danger',
                1: 'badge rounded-pill bg-olive',
                2: 'badge rounded-pill bg-pink',
                3: 'badge rounded-pill bg-primary',
                4: 'badge rounded-pill bg-gray',
                5: 'badge rounded-pill bg-orange',

                10: 'badge rounded-pill bg-gray',
                11: 'badge rounded-pill bg-primary',
                20: 'badge rounded-pill bg-pink',
                21: 'badge rounded-pill bg-primary',
                30: 'badge rounded-pill bg-gray',
                31: 'badge rounded-pill bg-danger',
                32: 'badge rounded-pill bg-tsukuba-gold text-light',
                40: 'badge rounded-pill bg-danger',
                41: 'badge rounded-pill bg-pink',
                42: 'badge rounded-pill bg-success',
                50: 'badge rounded-pill bg-tsukuba-itf text-light',
                51: 'badge rounded-pill bg-tsukuba-purple text-light',
                52: 'badge rounded-pill bg-dark',
            };
            return emotion_class_dict[emotion_code];
        },
        getEmotionText(emotion_code) {
            //emotion_codeから感情テキストを得る
            const emotion_text_dict = {
                0: '非常事態(´•_•; )',
                1: '考え中(-ω-;)ｳｰﾝ',
                2: '助かった(*´▽`人)',
                3: '提案(^^)/~~~',
                4: `ウンウン(´ー｀*)`,
                5: '大丈夫？( *´艸｀)',

                10: "ｆｍ ˘ω ˘ *))ｆｍ",
                11: "ぴえん🥺",
                20: "ありがとう🙏",
                21: "そんな……😭",
                30: "もう無理😖",
                31: "異議ありっ！！",
                32: "🎖️GOLD🎖️",
                40: "完全に理解した！",
                41: "どしたん話聞こか？",
                42: "🎓MASTER🎓",
                50: "IMAGINE THE FUTURE.",
                51: "DESIGN THE FUTURE.",
                52: "👑GRAND MASTER👑",
            };
            return emotion_text_dict[emotion_code];
        },
        escapeHTML(text) {
            //textをサニタイズする
            text = text.replace(/&/g, '&amp;');
            text = text.replace(/>/g, '&gt;');
            text = text.replace(/</g, '&lt;');
            text = text.replace(/"/g, '&quot;');
            text = text.replace(/'/g, '&#x27;');
            text = text.replace(/`/g, '&#x60;');
            return text;
        },
        autoLinkFilter(text) {
            //textに含まれるURLをリンク化して返す
            const safe_text = this.escapeHTML(text);
            return safe_text.replace(
                /(https?:\/\/[^\s]*)/g,
                "<a href='$1'>$1</a>"
            );
        },
        start () {
            //マウント時に実行される
            //定期実行をセットアップする
            const self = this;
            if (self.interval) {
              clearInterval(self.interval);
            }
            self.interval = setInterval(() => {
                this.loop();
            }, this.FETCH_INTERVAL);
        },
        async loop () {
            //定期実行される関数
            if (document.visibilityState === 'visible') {
                //タブが画面に写っているときのみ
                await this.fetchSubthreads(this.thread_id);
                for (const key in this.subthreads) {
                    const post_id = this.subthreads[key].post_id;
                    await this.fetchReplies(post_id);
                }
            }
        },
        onCommentButtonClick (post_id) {
            //コメントするボタンが押されるとき
            //グローバル空間のCHATAPPに返信先を書き込む
            CHATAPP.reply_to = post_id;
            window.document.getElementById("allow_tweet_dropdown").style = "display:none;";
        }
    },
    mounted() {
        this.loop();
        this.start();
    },
}).mount('#post_app')