Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            bool_of_flutter: true, //ユーザーがFlutterを使っているかどうか
        };
    },
    methods: {
        load_judge_flutter() {
            if (navigator.userAgent.indexOf('A+Tsukuba-flutter-App') == -1) {
                this.bool_of_flutter = false;
            }

        }
    },
    mounted() {
        this.load_judge_flutter();
    }
}).mount('#advertise')
