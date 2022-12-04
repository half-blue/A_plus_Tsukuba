//cf.https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Add_to_home_screen

Vue.createApp({
    delimiters: ['[[', ']]'],
    data () {
        return {
            deferredPrompt: null
        }
    },
    methods: {
        preventDefaultInstallPrompt(e) {
            // デフォルトのインストールプロンプトを無効化する
            e.preventDefault();
            //再利用のためキャプチャする
            this.deferredPrompt = e;
        },
        getAppButtonOnClick() {
            this.deferredPrompt.prompt();
            this.deferredPrompt.userChoice.then(this.userChoiceThen);
        },
        userChoiceThen (choiceResult) {
            if (choiceResult.outcome === "accepted") {
                //インストールされたので不要になる。
                this.deferredPrompt = null;
            }
        }
    },
    created () {
        window.addEventListener("beforeinstallprompt", this.preventDefaultInstallPrompt)
    }
}).mount('#get_app_app')

// copy self_address to clipboard
Vue.createApp({
    delimiters: ['[[', ']]'],
    data () {
        return {
            self_address: location.href
        }
    },
    methods: {
        copySelfAddress() {
            navigator.clipboard.writeText(this.self_address)
            .then(() => {
                console.log("copied!")
                this.ChangeAlert()
            })
            .catch(e => {
                console.error(e)
            })
        },
        ChangeAlert() {
            alert("コピーしました!")
        }
    }
}).mount('#copy_to_clipboard_app')