axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

const CHATAPP = {};
CHATAPP.reply_to = null;

Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            inputName: "名無し",
            selectEmotion: 1,
            inputText: "",
            selectTwitterBot: 1,
            thread_id: document.getElementById('thread_id').value,
            num_of_reviews: 0,
        }
    },
    methods: {
        async postSubthreads(fields) {
            const endpoint = '/api/post_subthreads';
            const recaptcha_token = await RECAPTCHA.getToken(RECAPTCHA.ACTION_POST_QUESTION);
            const res = await axios.post(
                endpoint,
                {
                    emotion: fields.emotion,
                    thread: this.thread_id,
                    sender_name: fields.sender_name,
                    text: fields.text,
                    allow_tweet: fields.allow_tweet,
                    [RECAPTCHA.TOKEN_FIELD]: recaptcha_token,
                }
            );
            return res;
        },
        async postReplies(post_id, fields) {
            const endpoint = '/api/post_replies';
            const recaptcha_token = await RECAPTCHA.getToken(RECAPTCHA.ACTION_POST_REPLY);
            const res = await axios.post(
                endpoint,
                {
                    emotion: fields.emotion,
                    post_id: post_id,
                    sender_name: fields.sender_name,
                    text: fields.text,
                    [RECAPTCHA.TOKEN_FIELD]: recaptcha_token,
                }
            );
            return res;
        },
        validationCheck() {
            //入力値をバリデーションチェックする
            //通常の操作で起こりうるのは、
            //名前または本文が空の場合である
            //セキュリティに関わる厳密なチェックはサーバーで行うので問題ない
            return this.inputName && this.inputText;
        },
        async onPostButtonClick() {
            //フォームの投稿するボタンが押されたら呼ばれる

            if (!this.validationCheck()) return;

            // reCAPTCHA のトークンを待つあいだに入力が変わっても、押したときの内容を送る
            const fields = {
                emotion: this.selectEmotion,
                sender_name: this.inputName,
                text: this.inputText,
                allow_tweet: this.selectTwitterBot,
            };
            const reply_to = CHATAPP.reply_to;
            this.inputText = "";

            try {
                if (!reply_to) {
                    //reply_to is null
                    await this.postSubthreads(fields);
                } else {
                    await this.postReplies(reply_to, fields);
                }
            } catch (error) {
                // 送れなかったとき (reCAPTCHA で断られたときなど) は、本文を入力欄に戻して知らせる
                if (!this.inputText) {
                    this.inputText = fields.text;
                }
                const detail = error.response && error.response.data && error.response.data.detail;
                alert(detail || "投稿できませんでした。時間をおいて、もう一度お試しください。");
            }
        },
        onSendButtonClick() {
            //質問するボタンを押すと呼ばれる

            CHATAPP.reply_to = null;
            window.document.getElementById("allow_tweet_dropdown").style = "";
        },
    },
    mounted() {
        this.num_of_reviews = REV_COUNT.COUNT;
    }
}).mount('#send_app');

Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            inputComment: "",
        }
    },
}).mount('#review_comment_word_count');