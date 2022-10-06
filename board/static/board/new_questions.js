Vue.createApp({
    delimiters: ['[[', ']]'],
    methods: {
        fromNowFilter(created_at_RFC5322) {
            const date = moment(created_at_RFC5322);
            return date.fromNow(); 
        }
    },
}).mount('#new_questions_app');