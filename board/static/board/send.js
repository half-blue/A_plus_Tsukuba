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
        async postSubthreads(thread_id) {
            const endpoint = '/api/post_subthreads';
            const res = await axios.post(
                endpoint,
                {
                    emotion: this.selectEmotion,
                    thread: this.thread_id,
                    sender_name: this.inputName,
                    text: this.inputText,
                    allow_tweet: this.selectTwitterBot,
                }
            );
            return res;
        },
        async postReplies(post_id) {
            const endpoint = '/api/post_replies';
            const res = await axios.post(
                endpoint,
                {
                    emotion: this.selectEmotion,
                    post_id: post_id,
                    sender_name: this.inputName,
                    text: this.inputText,
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
        onPostButtonClick() {
            //フォームの投稿するボタンが押されたら呼ばれる

            if (!this.validationCheck()) return;

            if (!CHATAPP.reply_to) {
                //reply_to is null
                this.postSubthreads(this.thread_id);
            } else {
                this.postReplies(CHATAPP.reply_to);
            }
            this.inputText = "";
        },
        onSendButtonClick() {
            //質問するボタンを押すと呼ばれる

            this.num_of_reviews = REV_COUNT.COUNT;

            CHATAPP.reply_to = null;
            window.document.getElementById("allow_tweet_dropdown").style = "";
        },
    },
}).mount('#send_app');

Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            inputComment: "",
        }
    },
}).mount('#review_comment_word_count');