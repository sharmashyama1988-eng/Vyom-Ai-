/**
 * VOICE MODULE - The Ears of Vyom AI
 * Handles Wake Word, Speech Recognition, and Auto-Commands.
 */

class VyomAIVoiceEngine {
    constructor(callbacks) {
        this.recognition = null;
        this.isSystemActive = false; // Master switch
        this.isProcessing = false;   // To stop listening while Vyom AI speaks
        this.silenceTimer = null;
        
        // Configuration
        this.wakeWords = ["hey vyom", "hello vyom", "vyom", "ok vyom"];
        this.silenceDelay = 1500; // 1.5 seconds silence = Send Command
        
        // Callbacks from UI (chat.html)
        this.onSpeech = callbacks.onSpeech || function(){};     // Updating text box
        this.onWake = callbacks.onWake || function(){};         // "Listening..." UI update
        this.onCommand = callbacks.onCommand || function(){};   // Sending message
        this.onStandby = callbacks.onStandby || function(){};   // Back to "Hey Vyom" mode
        
        this.init();
    }

    init() {
        if (!('webkitSpeechRecognition' in window)) {
            console.error("Browser does not support Speech API.");
            return;
        }

        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = true;      // Hamesha sunte raho
        this.recognition.interimResults = true;  // Real-time typing
        this.recognition.lang = 'en-IN';         // Best for Hinglish

        this.recognition.onstart = () => console.log("👂 Vyom AI Ears Active");
        
        this.recognition.onend = () => {
            // Agar system active hai aur humne manually band nahi kiya, to restart karo
            if (this.isSystemActive) {
                console.log("🔄 Restarting Listener...");
                try { this.recognition.start(); } catch(e){}
            }
        };

        this.recognition.onresult = (event) => this.handleAudio(event);
        this.recognition.onerror = (e) => console.log("Mic Error:", e.error);
    }

    start() {
        this.isSystemActive = true;
        try { this.recognition.start(); } catch(e){}
    }

    stop() {
        this.isSystemActive = false;
        try { this.recognition.stop(); } catch(e){}
    }

    handleAudio(event) {
        if (this.isProcessing) return; // Jab Vyom AI bol raha ho, tab mat suno

        let transcript = '';
        let isFinal = false;

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
            if (event.results[i].isFinal) isFinal = true;
        }
        
        transcript = transcript.toLowerCase().trim();
        if (!transcript) return;

        // --- 1. WAKE WORD CHECK (Standby Mode) ---
        if (!this.isActiveMode) {
            // Check agar user ne wake word bola
            const detected = this.wakeWords.some(word => transcript.includes(word));
            if (detected) {
                this.activateCommandMode();
            }
        } 
        // --- 2. COMMAND MODE (Active Listening) ---
        else {
            this.onSpeech(transcript); // UI update karo (Text box mein likho)
            
            // Silence Detection Logic (Auto Send)
            clearTimeout(this.silenceTimer);
            
            // Agar user 1.5 second chup raha, ya sentence khatam ho gaya
            if (transcript.length > 0) {
                this.silenceTimer = setTimeout(() => {
                    this.triggerCommand(transcript);
                }, this.silenceDelay);
            }
        }
    }

    activateCommandMode() {
        this.isActiveMode = true;
        this.playBeep();
        this.onWake(); // UI ko bolo "Listening..." dikhaye
        
        // Restart recognition to clear buffer (purani baatein saaf karo)
        this.recognition.stop();
        setTimeout(() => {
            if(this.isSystemActive) this.recognition.start();
        }, 200);
    }

    triggerCommand(text) {
        if (!this.isActiveMode || !text) return;
        
        this.isActiveMode = false; // Wapas standby mode mein jao
        this.onCommand(text);      // Message bhejo
        this.onStandby();          // UI reset karo
    }

    playBeep() {
        const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
        audio.volume = 0.5;
        audio.play().catch(e => console.log("Audio play failed"));
    }
}
