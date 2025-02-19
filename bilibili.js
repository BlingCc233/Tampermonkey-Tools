// ==UserScript==
// @name         Bilibili自动全屏脚本
// @namespace    bilibili-auto-fullscreen-script
// @version      1.3.3
// @description  在Bilibili网站自动全屏播放视频，按T键切换全屏,包括直播间
// @author       Combined Script
// @match        https://www.bilibili.com/*
// @match        https://live.bilibili.com/*
// @license      MIT
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    let isFullscreen = false;

    // Utility function to wait for elements
    function waitForElement(selector, callback, maxTries = 10, interval = 1000) {
        let tries = 0;

        function check() {
            const element = document.querySelector(selector);
            if (element) {
                callback(element);
                return;
            }

            tries++;
            if (tries < maxTries) {
                setTimeout(check, interval);
            }
        }

        check();
    }

    // Mouse event simulation
    function simulateMouseEvent(element, eventType, x, y) {
        const event = new MouseEvent(eventType, {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y
        });
        element.dispatchEvent(event);
    }

    // Double click simulation
    function triggerDoubleClick(element) {
        const event = new MouseEvent('dblclick', {
            bubbles: true,
            cancelable: true,
            view: window
        });
        element.dispatchEvent(event);
    }

    // Video page fullscreen handler
    function triggerVideoFullscreen() {
        const fullscreenButton = document.querySelector('[aria-label="网页全屏"]');
        if (!fullscreenButton) return;

        try {
            fullscreenButton.click();
        } catch (e) {
            const rect = fullscreenButton.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;

            simulateMouseEvent(fullscreenButton, 'mouseenter', x, y);
            simulateMouseEvent(fullscreenButton, 'click', x, y);
            simulateMouseEvent(fullscreenButton, 'mouseleave', x, y);
        }
    }

    // Live stream fullscreen handler
    function toggleLiveFullscreen() {
        const player = document.getElementById('live-player');
        if (player) {
            triggerDoubleClick(player);
            isFullscreen = !isFullscreen;

            if (isFullscreen) {
                document.body.classList.add('hide-aside-area');
            } else {
                document.body.classList.remove('hide-aside-area');
            }
        }
    }

    // Initialize video page
    function initializeVideo() {
        waitForElement('.bpx-player-video-area', () => {
            waitForElement('[aria-label="网页全屏"]', () => {
                triggerVideoFullscreen();
            });
        });
    }

    // Initialize live stream page
    async function initializeLive() {
        // Wait for player script
        await new Promise((resolve) => {
            const observer = new MutationObserver((mutations, obs) => {
                const scripts = document.getElementsByTagName('script');
                for (let script of scripts) {
                    if (script.src.includes('room-player.prod.min.js')) {
                        setTimeout(() => {
                            obs.disconnect();
                            resolve();
                        }, 1000);
                        return;
                    }
                }
            });

            observer.observe(document, {
                childList: true,
                subtree: true
            });
        });

        // Wait for player element
        const player = await new Promise((resolve) => {
            const checkElement = () => {
                const player = document.getElementById('live-player');
                if (player) {
                    resolve(player);
                } else {
                    requestAnimationFrame(checkElement);
                }
            };
            checkElement();
        });

        // Initial fullscreen
        triggerDoubleClick(player);
        isFullscreen = true;
        document.body.classList.add('hide-aside-area');
    }

    // Main initialization
    function initialize() {
        const isLivePage = window.location.hostname === 'live.bilibili.com';

        if (isLivePage) {
            initializeLive();
        } else {
            initializeVideo();
        }

        // Global T key handler
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 't') {
                if (isLivePage) {
                    toggleLiveFullscreen();
                } else {
                    triggerVideoFullscreen();
                }
            }
        });
    }

    // Start script
    if (document.readyState === 'complete') {
        initialize();
    } else {
        window.addEventListener('load', initialize);
    }
})();
