/* Initialize Firebase (compat) after firebase-app-compat.js is loaded. */
(function () {
    var cfg = window.__FIREBASE_CONFIG__ || {};
    if (!cfg.apiKey) {
        window.firebaseReady = false;
        return;
    }
    firebase.initializeApp(cfg);
    window.firebaseReady = true;
})();
