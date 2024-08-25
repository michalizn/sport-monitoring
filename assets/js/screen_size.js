// assets/detect_screen_size.js
document.addEventListener('DOMContentLoaded', function() {
    const screenWidth = window.innerWidth;
    const screenSize = screenWidth < 769 ? 'mobile' : 'desktop';
    window.dash_clientside.callback_context.triggered[0].prop_id = 'screen-size.data';
    window.dash_clientside.trigger_store_update('screen-size', screenSize);
});
