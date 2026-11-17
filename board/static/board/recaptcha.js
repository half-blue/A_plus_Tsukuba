// 質問・返信・レビューの投稿の直前に reCAPTCHA のトークンを取る (確かめるのはサーバー。board/recaptcha.py)。
// 鍵はテンプレートが json_script (id="recaptcha-site-key") で埋め込む。鍵がない (reCAPTCHA を使わない) ときは空文字列を返す。
// トークンを取れなかったとき (reCAPTCHA の読み込みが広告ブロッカーなどで止められたときなど) も空文字列で送り、
// 通すかどうかはサーバーが決める。
const RECAPTCHA = {};

// アクション名 (board/recaptcha.py の ACTION_* と揃える)
RECAPTCHA.ACTION_POST_QUESTION = 'post_question';
RECAPTCHA.ACTION_POST_REPLY = 'post_reply';
RECAPTCHA.ACTION_POST_REVIEW = 'post_review';

// 投稿の中でトークンを入れるフィールドの名前 (board/recaptcha.py の TOKEN_FIELD と揃える)
RECAPTCHA.TOKEN_FIELD = 'recaptcha_token';

// トークンを待つ上限 (ミリ秒)。超えたら空文字列で送る
RECAPTCHA.TIMEOUT_MS = 10000;

RECAPTCHA.siteKey = function () {
    const element = document.getElementById('recaptcha-site-key');
    return element ? JSON.parse(element.textContent) : '';
};

RECAPTCHA.getToken = async function (action) {
    const siteKey = RECAPTCHA.siteKey();
    if (!siteKey) {
        return '';
    }
    if (typeof grecaptcha === 'undefined' || !grecaptcha.enterprise) {
        console.warn('reCAPTCHA を読み込めませんでした');
        return '';
    }
    const token = new Promise((resolve, reject) => {
        grecaptcha.enterprise.ready(() => {
            grecaptcha.enterprise.execute(siteKey, { action: action }).then(resolve, reject);
        });
    });
    const timeout = new Promise((resolve) => setTimeout(() => resolve(''), RECAPTCHA.TIMEOUT_MS));
    try {
        return await Promise.race([token, timeout]);
    } catch (error) {
        console.warn('reCAPTCHA のトークンを取れませんでした', error);
        return '';
    }
};

// フォームの送信の直前にトークンを取り、隠しフィールド (name が TOKEN_FIELD) に入れてから送る
RECAPTCHA.protectForm = function (form, action) {
    let submitting = false;
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (submitting) {
            return;
        }
        submitting = true;
        form.elements[RECAPTCHA.TOKEN_FIELD].value = await RECAPTCHA.getToken(action);
        // HTMLFormElement.submit() は submit イベントを出さないので、このリスナーには戻ってこない
        form.submit();
    });
};

(function () {
    const reviewForm = document.getElementById('review_post_form');
    if (reviewForm && RECAPTCHA.siteKey() && reviewForm.elements[RECAPTCHA.TOKEN_FIELD]) {
        RECAPTCHA.protectForm(reviewForm, RECAPTCHA.ACTION_POST_REVIEW);
    }
})();
