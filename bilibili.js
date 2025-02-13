// ==UserScript==
// @name         Bilibili自动全屏脚本
// @namespace    bilibili-auto-fullscreen-script
// @version      1.3.2
// @description  在Bilibili网站自动全屏播放视频，按T键切换全屏
// @author       BlingCc
// @match        https://www.bilibili.com/*
// @license      MIT
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // 等待页面完全加载后执行全屏操作
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

    // 触发全屏
    function triggerFullscreen() {
        const fullscreenButton = document.querySelector('[aria-label="网页全屏"]');
        if (!fullscreenButton) return;

        // 首先尝试直接触发点击事件
        try {
            fullscreenButton.click();
        } catch (e) {
            // 如果直接点击失败，则使用模拟鼠标事件
            const rect = fullscreenButton.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            
            simulateMouseEvent(fullscreenButton, 'mouseenter', x, y);
            simulateMouseEvent(fullscreenButton, 'click', x, y);
            simulateMouseEvent(fullscreenButton, 'mouseleave', x, y);
        }
    }

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

    // 初始化
    function initialize() {
        // 等待视频播放器加载完成
        waitForElement('.bpx-player-video-area', (videoWrap) => {
            // 确保播放器控件已加载
            waitForElement('[aria-label="网页全屏"]', () => {
                triggerFullscreen();
            });
        });

        // 添加按T切换全屏的事件监听
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 't') {
                triggerFullscreen();
            }
        });
    }

    // 当页面加载完成时初始化
    if (document.readyState === 'complete') {
        initialize();
    } else {
        window.addEventListener('load', initialize);
    }
})();
