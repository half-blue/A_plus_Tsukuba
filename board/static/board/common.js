const BOOK_MARK = {}
const REVIEWED = {}
const REV_COUNT = {}
BOOK_MARK.EXPIRES = 365 * 6; // Bachelor and Master period
REVIEWED.EXPIRES = 365 * 6; // Bachelor and Master period
REV_COUNT.EXPIRES = 365 * 6; // Bachelor and Master period
REV_COUNT.COUNT = 0;


BOOK_MARK.getCookies = function () { // return (JSON)object not (JSON)string
    const load_json_string = Cookies.get('bookmark');

    if (load_json_string) {
        return JSON.parse(load_json_string);
    } else {
        return {};
    }
}

BOOK_MARK.setCookie = function (name, json_object) { // receive (JSON)object not (JSON)string
    Cookies.set(name, JSON.stringify(json_object), { expires: BOOK_MARK.EXPIRES });
};

BOOK_MARK.setBookmark = function (thread_id, thread_title) {
    let bookmark_json = BOOK_MARK.getCookies();

    bookmark_json[thread_id] = thread_title;
    BOOK_MARK.setCookie("bookmark", bookmark_json);
}

BOOK_MARK.deleteBookmark = function (thread_id) {
    let bookmark_json = BOOK_MARK.getCookies();

    delete bookmark_json[thread_id]
    BOOK_MARK.setCookie("bookmark", bookmark_json);
}

Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            bookmark_data: [],
        }
    },
    methods: {
        loadbookmark() {
            const bookmark_json = BOOK_MARK.getCookies();
            this.bookmark_data = Object.entries(bookmark_json);  
        }
    }
}).mount('#bookmark_dropdown');

REVIEWED.getCookies = function () { // return (JSON)object not (JSON)string
    const load_json_string = Cookies.get('reviewed');

    if (load_json_string) {
        return JSON.parse(load_json_string);
    } else {
        return {};
    }
}

REVIEWED.setCookie = function (name, json_object) { // receive (JSON)object not (JSON)string
    Cookies.set(name, JSON.stringify(json_object), { expires: REVIEWED.EXPIRES });
};

REVIEWED.setReviewed = function (thread_id) {
    let bookmark_json = REVIEWED.getCookies();

    bookmark_json[thread_id] = true;
    BOOK_MARK.setCookie("reviewed", bookmark_json);
}

const CHATAPP = {};
CHATAPP.reply_to = null;
let bookmark_json = REVIEWED.getCookies();
REV_COUNT.COUNT = Object.keys(bookmark_json).length;