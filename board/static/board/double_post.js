Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            thread_id: document.getElementById('thread_id').value,
        }
    },
    methods: {
        loadbookmark() {
            const bookmark_json = REVIEWED.getCookies();
        },
        onPostClick() {
            console.log("onPostClick");
            REVIEWED.setReviewed(this.thread_id);
        }
    },
    mounted() {
        this.loadbookmark();
    }

}).mount('#review_Form_post_button');

Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            thread_id: document.getElementById('thread_id').value,
            not_posted: true,
        }
    },
    methods: {
        loadreviwed() {
            console.log("loadreviwed");
            const reviewed_json = REVIEWED.getCookies();

            if (this.thread_id in reviewed_json) {
                this.not_posted = false;
            }
        },
    },
    mounted() {
        this.loadreviwed();
    }

}).mount('#PostedBoolean');