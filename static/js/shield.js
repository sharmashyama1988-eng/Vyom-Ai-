/**
 * VYOM AI - UI SHIELD PROTOCOL
 * Prevents unauthorized inspection and tampering of the frontend interface.
 */

// 1. Disable Right Click Context Menu
document.addEventListener('contextmenu', event => {
    event.preventDefault();
});

// 2. Disable Keyboard Shortcuts (F12, Ctrl+Shift+I, Ctrl+U, etc.)
document.onkeydown = function(e) {
    // F12
    if(e.keyCode == 123) {
        return false;
    }
    // Ctrl+Shift+I (Inspect)
    if(e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0)) {
        return false;
    }
    // Ctrl+Shift+C (Element Inspector)
    if(e.ctrlKey && e.shiftKey && e.keyCode == 'C'.charCodeAt(0)) {
        return false;
    }
    // Ctrl+Shift+J (Console)
    if(e.ctrlKey && e.shiftKey && e.keyCode == 'J'.charCodeAt(0)) {
        return false;
    }
    // Ctrl+U (View Source)
    if(e.ctrlKey && e.keyCode == 'U'.charCodeAt(0)) {
        return false;
    }
    // Ctrl+S (Save Page) - Optional, prevents simple saving
    if(e.ctrlKey && e.keyCode == 'S'.charCodeAt(0)) {
        e.preventDefault();
        return false;
    }
}

// 3. Social Engineering Warning (Console Message)
// If someone manages to open console, scare them off.
setTimeout(function() {
    console.log("%c STOP! ", "color: red; font-size: 60px; font-weight: bold; text-shadow: 2px 2px 0px black;");
    console.log("%c This is a restricted browser feature intended for developers.", "font-size: 20px; color: white; background: #333; padding: 5px;");
    console.log("%c If someone told you to copy-paste something here to 'hack' Vyom AI, they are scamming you.", "font-size: 16px; color: #ff5546;");
}, 1000);
