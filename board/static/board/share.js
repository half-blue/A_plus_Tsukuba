Vue.createApp({
    delimiters: ['[[', ']]'],
    setup() {
        return {
            NavigatorShareAPI: navigator.share,
            now_url : location.href,
        }
    },
    methods: {
        async NavigatorShareApiShare() {
            try {
                await navigator.share({ title: document.title, url: '' });
            } catch {} //シェアをキャンセルした場合エラーになる 
        },
        TweetShare() {
            const url = 'http://twitter.com/share?hashtags=Aplusつくば&url=' + this.now_url;
            window.open(url, '_blank')
        },
        LineShare() {
            const url = 'https://social-plugins.line.me/lineit/share?url=' + this.now_url;
            window.open(url, '_blank')
        },
    },
}).mount('#share_app')