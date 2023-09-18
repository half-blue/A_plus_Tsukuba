Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            is_not_hide: false,
        }
    },
    methods: {
        load_is_not_hide() {
            this.is_not_hide = PRIME_STUDENT_ALERT.isNotHide();
        },
        push_hide() {
            PRIME_STUDENT_ALERT.setCookieHide();
            this.load_is_not_hide();
        },
    },
    mounted() {
        this.load_is_not_hide();
    }

}).mount('#textbooks_app');