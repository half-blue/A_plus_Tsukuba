
const ITF_CHECK = {}

ITF_CHECK.PROMPT_MSG = "このサービスは筑波大生専用のサービスです。\n" +
    "筑波大生は以下のクイズに解答して先に進んでくさい。\n" +
    "\n" +
    "筑波大学でアルファベット3文字といえば何でしょう？\n" +
    "（半角英字大文字で入力してください。）";
ITF_CHECK.CONFIRM_MSG = "答えが間違っています。もう一度挑戦しますか？";
ITF_CHECK.MOVE_MSG = "筑波大のWebサイトに遷移します。";
ITF_CHECK.MOVE_TO = "https://www.tsukuba.ac.jp/";
ITF_CHECK.ANSWER = "ITF";
ITF_CHECK.EXPIRES = 365; //DAYS

ITF_CHECK.move = function () {
    alert(ITF_CHECK.MOVE_MSG);
    location.href = ITF_CHECK.MOVE_TO;
}

ITF_CHECK.quiz = function () {
    //クイズを行い、成否を返す。
    const input = window.prompt(ITF_CHECK.PROMPT_MSG);
    if (!input) return false; // in case of "cancel" or "no input"
    if (input == ITF_CHECK.ANSWER) {
        return true;
    } else {
        if (confirm(ITF_CHECK.CONFIRM_MSG)) {
            return ITF_CHECK.quiz();
        } else {
            return false;
        }
    }
}

ITF_CHECK.check = function () {
    //すべてのページにおいて、ページ読み込み時にこの関数が実行されます。
    if (ITF_CHECK.isGoogleBot()) return; //Googlebotは通過させる

    const ITFCookie = Cookies.get("ITF"); // return "true" or undifined
    if (!ITFCookie) {
        if (ITF_CHECK.quiz()) {
            Cookies.set("ITF", "true", { expires: ITF_CHECK.EXPIRES });
        } else {
            ITF_CHECK.move();
        }
    }
}

ITF_CHECK.isGoogleBot = function () {
    const ua = navigator.userAgent;
    return (ua.indexOf("Googlebot") !== -1);
}