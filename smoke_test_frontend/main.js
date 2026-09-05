import { SimliClient } from 'simli-client';

let simliClient = null;
let isConnected = false;

document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("startBtn");
    const playBtn = document.getElementById("playBtn");
    const btnFallbackOnly = document.getElementById("btnFallbackOnly");
    const btnWebAudioOnly = document.getElementById("btnWebAudioOnly");

    const videoElement = document.getElementById("simliVideo");
    const audioElement = document.getElementById("simliAudio");
    const fallbackAudio = document.getElementById("fallbackAudio");
    const statusText = document.getElementById("status");
    const logEl = document.getElementById("diagnosticLog");

    function log(msg) {
        console.log(msg);
        if(logEl) {
            logEl.innerHTML += `<div>${new Date().toISOString().split('T')[1]} - ${msg}</div>`;
            logEl.scrollTop = logEl.scrollHeight;
        }
    }

    // Audio Ownership State
    let audioOwner = "none"; // "simli" | "fallback" | "none"
    let sendAudioLoop = null;
    let audioContext = null;

    function stopAllAudio() {
        if (sendAudioLoop) {
            clearInterval(sendAudioLoop);
            sendAudioLoop = null;
        }
        fallbackAudio.pause();
        fallbackAudio.currentTime = 0;
        audioOwner = "none";
        log("[AUDIO] stopAllAudio called, owner=none");
    }

    log("DOM READY, BUTTONS FOUND");

    // ==========================================
    // STEP 3 - INDEPENDENT FALLBACK TEST
    // ==========================================
    btnFallbackOnly.addEventListener("click", async () => {
        log("=== TEST: FALLBACK ONLY ===");
        log(`fallbackAudio src: ${fallbackAudio.src}`);
        fallbackAudio.load();
        try {
            log("Calling fallbackAudio.play()...");
            await fallbackAudio.play();
            log("fallbackAudio.play() PROMISE RESOLVED.");
            log(`- paused: ${fallbackAudio.paused}`);
            log(`- muted: ${fallbackAudio.muted}`);
            log(`- volume: ${fallbackAudio.volume}`);
            log(`- readyState: ${fallbackAudio.readyState}`);
            log(`- networkState: ${fallbackAudio.networkState}`);
            log(`- currentTime: ${fallbackAudio.currentTime}`);
            log(`- duration: ${fallbackAudio.duration}`);
        } catch (e) {
            log(`fallbackAudio.play() REJECTED: ${e.name} - ${e.message}`);
        }
    });

    // ==========================================
    // STEP 4 - INDEPENDENT WEBAUDIO TEST
    // ==========================================
    btnWebAudioOnly.addEventListener("click", async () => {
        log("=== TEST: WEBAUDIO ONLY ===");
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            log(`AudioContext created. state=${ctx.state}, sampleRate=${ctx.sampleRate}`);
            
            const url = fallbackAudio.src;
            log(`Fetching MP3 from ${url}...`);
            const response = await fetch(url);
            log(`Fetch response: status=${response.status}, content-type=${response.headers.get('content-type')}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const arrayBuffer = await response.arrayBuffer();
            log(`Fetched ${arrayBuffer.byteLength} bytes.`);
            
            log("Decoding audio data...");
            const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
            log(`Decoded: duration=${audioBuffer.duration}s, channels=${audioBuffer.numberOfChannels}, sampleRate=${audioBuffer.sampleRate}, length=${audioBuffer.length}`);
            
            const source = ctx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(ctx.destination);
            
            if (ctx.state === 'suspended') {
                log("Resuming AudioContext...");
                await ctx.resume();
                log(`AudioContext state is now: ${ctx.state}`);
            }
            
            log("Calling source.start(0)...");
            source.start(0);
            log("WebAudio playback started.");
        } catch (e) {
            log(`WebAudio test FAILED: ${e.message}`);
        }
    });

    // ==========================================
    // STEP 5 & 1 - SIMLI SESSION CREATION
    // ==========================================
    startBtn.addEventListener("click", async () => {
        log("=== TEST: SIMLI SESSION ===");
        try {
            statusText.innerText = "Connecting to backend for session...";
            const res = await fetch("/avatar/session", { method: "POST" });
            if (!res.ok) throw new Error(`Backend session failed: ${res.status}`);
            
            const sessionData = await res.json();
            log("Backend session fetched successfully.");
            
            simliClient = new SimliClient(
                sessionData.session_token,
                videoElement,
                audioElement,
                sessionData.ice_servers,
            );

            // Register all relevant SDK events
            const events = ["connected", "disconnected", "failed"];
            events.forEach(evt => {
                simliClient.on(evt, (...args) => {
                    log(`[SIMLI EVENT] ${evt} ` + (args.length ? JSON.stringify(args) : ""));
                });
            });

            simliClient.on("connected", () => {
                isConnected = true;
                statusText.innerText = "Connected to Simli WebRTC!";
                
                // Inspect MediaStream
                log("Inspecting Simli WebRTC MediaStream...");
                if (simliClient.connection && simliClient.connection.signalingConnection) {
                    const stream = simliClient.connection.signalingConnection.mediaStream;
                    if (stream) {
                        log(`MediaStream ID: ${stream.id}, active: ${stream.active}`);
                        const aTracks = stream.getAudioTracks();
                        const vTracks = stream.getVideoTracks();
                        log(`Audio tracks: ${aTracks.length}, Video tracks: ${vTracks.length}`);
                        
                        aTracks.forEach((t, i) => {
                            log(`Audio Track [${i}]: readyState=${t.readyState}, enabled=${t.enabled}, muted=${t.muted}`);
                        });
                        vTracks.forEach((t, i) => {
                            log(`Video Track [${i}]: readyState=${t.readyState}, enabled=${t.enabled}, muted=${t.muted}`);
                        });

                        // Explicitly attach audio track to audioElement to ensure it's playable
                        if (aTracks.length > 0) {
                            if (audioElement.srcObject !== stream) {
                                log("Attaching MediaStream to simliAudio element explicitly...");
                                audioElement.srcObject = stream;
                            }
                            audioElement.play().then(() => {
                                log("simliAudio.play() RESOLVED for WebRTC audio track.");
                            }).catch(err => {
                                log(`simliAudio.play() REJECTED: ${err.name} - ${err.message}`);
                            });
                        }
                    } else {
                        log("MediaStream is null or undefined on signalingConnection.");
                    }
                } else {
                    log("Cannot access connection/signalingConnection in SDK.");
                }
            });

            simliClient.on("disconnected", () => {
                isConnected = false;
                statusText.innerText = "Disconnected.";
                if (audioOwner === "simli") {
                    log("[AUDIO] owner=FALLBACK_HTML (Simli disconnected mid-speech)");
                    audioOwner = "fallback";
                    if (sendAudioLoop) clearInterval(sendAudioLoop);
                    fallbackAudio.play().catch(e => log(`Fallback play failed: ${e.message}`));
                }
            });

            simliClient.on("failed", () => {
                isConnected = false;
                statusText.innerText = "Connection Failed.";
                if (audioOwner === "simli") {
                    log("[AUDIO] owner=FALLBACK_HTML (Simli failed mid-speech)");
                    audioOwner = "fallback";
                    if (sendAudioLoop) clearInterval(sendAudioLoop);
                    fallbackAudio.play().catch(e => log(`Fallback play failed: ${e.message}`));
                }
            });
            
            statusText.innerText = "Starting WebRTC...";
            log("Calling simliClient.start()...");
            await simliClient.start();
            log("simliClient.start() complete.");
            
        } catch (err) {
            log(`Error starting session: ${err.message}`);
            statusText.innerText = `Error: ${err.message}`;
            isConnected = false;
        }
    });

    // ==========================================
    // STEP 6 - PCM CONVERSION & CHUNKING
    // ==========================================
    async function getPCM16Data(url) {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            log(`[PCM] AudioContext created: sampleRate=${audioContext.sampleRate}, state=${audioContext.state}`);
        }
        
        log(`[PCM] Fetching MP3: ${url}`);
        const response = await fetch(url);
        log(`[PCM] Fetch status: ${response.status}, bytes: ${response.headers.get('content-length')}`);
        if (!response.ok) throw new Error("MP3 fetch failed: " + response.status);
        const arrayBuffer = await response.arrayBuffer();
        
        log(`[PCM] Decoding ${arrayBuffer.byteLength} bytes...`);
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        log(`[PCM] Decoded: duration=${audioBuffer.duration}s, channels=${audioBuffer.numberOfChannels}, SR=${audioBuffer.sampleRate}`);
        
        const targetSampleRate = 16000;
        log(`[PCM] Resampling to ${targetSampleRate}Hz Mono...`);
        const offlineCtx = new OfflineAudioContext(1, Math.ceil(audioBuffer.duration * targetSampleRate), targetSampleRate);
        const source = offlineCtx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(offlineCtx.destination);
        source.start(0);
        
        const renderedBuffer = await offlineCtx.startRendering();
        const float32Data = renderedBuffer.getChannelData(0);
        log(`[PCM] Resampled channels=1, total samples=${float32Data.length}`);
        
        log("[PCM] Converting Float32 to Int16...");
        const pcm16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Data[i]));
            pcm16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        const uint8Data = new Uint8Array(pcm16Data.buffer);
        log(`[PCM] Final Uint8Array length=${uint8Data.length} bytes. Target=PCM16, 16000Hz, Mono, Little-Endian.`);
        return uint8Data;
    }

    playBtn.addEventListener("click", async () => {
        log("=== TEST: SIMLI PCM AUDIO ===");
        stopAllAudio(); // Rule 12: Stop previous session/audio

        if (!isConnected || !simliClient) {
            log("[AUDIO] owner=FALLBACK_HTML (Simli not connected)");
            audioOwner = "fallback";
            statusText.innerText = "Playing audio (Fallback)...";
            fallbackAudio.play().catch(e => log(`Fallback play failed: ${e.name} ${e.message}`));
            return;
        }

        try {
            log("[AUDIO] Fetching and processing audio for Simli...");
            statusText.innerText = "Processing audio...";
            
            const uint8Data = await getPCM16Data(fallbackAudio.src);
            
            if (!isConnected) {
                throw new Error("Disconnected during processing");
            }

            audioOwner = "simli";
            log(`[AUDIO] owner=SIMLI`);
            statusText.innerText = "Playing audio via Avatar...";
            
            const chunkSize = 6000; 
            const intervalMs = 187.5;
            
            let offset = 0;
            
            sendAudioLoop = setInterval(() => {
                if (!isConnected || audioOwner !== "simli") {
                    log(`[AUDIO LOOP] Aborting loop. isConnected=${isConnected}, owner=${audioOwner}`);
                    clearInterval(sendAudioLoop);
                    return;
                }
                
                if (offset >= uint8Data.length) {
                    clearInterval(sendAudioLoop);
                    sendAudioLoop = null;
                    audioOwner = "none";
                    log("[AUDIO LOOP] Simli playback finished naturally.");
                    statusText.innerText = "Playback finished.";
                    return;
                }
                
                const chunk = uint8Data.slice(offset, offset + chunkSize);
                simliClient.sendAudioData(chunk);
                offset += chunkSize;

                if(offset === chunkSize) {
                   log(`[AUDIO LOOP] First chunk sent. Size=${chunk.byteLength} bytes.`);
                }
            }, intervalMs);

            log(`[AUDIO LOOP] Started setInterval (${intervalMs}ms) for ${uint8Data.length} total bytes.`);

        } catch (err) {
            log(`[AUDIO] Error: ${err.message}`);
            log("[AUDIO] owner=FALLBACK_HTML (Error fallback)");
            audioOwner = "fallback";
            statusText.innerText = "Playing audio (Fallback from error)...";
            fallbackAudio.play().catch(e => log(`Fallback play failed: ${e.message}`));
        }
    });
});
