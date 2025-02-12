// ==UserScript==
// @name         Bilibili自动全屏脚本
// @namespace    bilibili-auto-fullscreen-script
// @version      1.3
// @description  在Bilibili网站自动全屏播放视频，支持T键切换
// @author       BlingCc
// @match        https://www.bilibili.com/*
// @license      MIT
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    let fullscreenObserver = null;
    let isAutoFullscreenEnabled = true;

    // 主初始化函数
    function init() {
        setupVideoObserver();
        setupKeyboardListener();
    }

    // 设置视频容器观察器
    function setupVideoObserver() {
        const observer = new MutationObserver((_, obs) => {
            const videoContainer = document.querySelector('.bpx-player-video-area');
            if (videoContainer) {
                obs.disconnect();
                prepareForFullscreen(videoContainer);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // 准备全屏操作
    function prepareForFullscreen(videoContainer) {
        activateVideoControls(videoContainer);
        setupFullscreenButtonObserver(videoContainer);
    }

    // 激活视频控制栏
    function activateVideoControls(element) {
        const { left, top, width, height } = element.getBoundingClientRect();
        dispatchMouseEvent(element, 'mouseenter', left + width/2, top + height/2);
    }

    // 设置全屏按钮观察器
    function setupFullscreenButtonObserver(container) {
        fullscreenObserver = new MutationObserver((_, obs) => {
            const fullscreenBtn = getFullscreenButton();
            if (fullscreenBtn) {
                obs.disconnect();
                if (isAutoFullscreenEnabled) triggerFullscreen(fullscreenBtn);
            }
        });
        fullscreenObserver.observe(container, { childList: true, subtree: true });
    }

    // 触发全屏操作
    function triggerFullscreen(button) {
        // 优先使用直接点击
        if (!attemptDirectClick(button)) {
            simulateRealisticClick(button);
        }
        isAutoFullscreenEnabled = false; // 防止重复触发
    }

    // 尝试直接点击
    function attemptDirectClick(element) {
        const preClickLabel = element.getAttribute('aria-label');
        element.click();
        setTimeout(() => {
            if (element.getAttribute('aria-label') !== preClickLabel) return true;
        }, 100);
        return false;
    }

    // 模拟真实点击
    function simulateRealisticClick(element) {
        const { left, top, width, height } = element.getBoundingClientRect();
        const eventSequence = ['mouseenter', 'mousedown', 'mouseup', 'click'];
        eventSequence.forEach(eventType => {
            dispatchMouseEvent(element, eventType, left + width/2, top + height/2);
        });
    }

    // 设置键盘监听器
    function setupKeyboardListener() {
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 't') handleFullscreenToggle();
        });
    }

    // 处理全屏切换
    function handleFullscreenToggle() {
        const videoContainer = document.querySelector('.bpx-player-video-area');
        if (!videoContainer) return;

        activateVideoControls(videoContainer);
        const fullscreenBtn = getFullscreenButton() || findAlternativeFullscreenButton();
        
        if (fullscreenBtn) {
            triggerFullscreen(fullscreenBtn);
        } else {
            setupTemporaryButtonObserver(videoContainer);
        }
    }

    // 获取当前全屏按钮
    function getFullscreenButton() {
        return document.querySelector('[aria-label="网页全屏"], [aria-label="退出网页全屏"]');
    }

    // 查找备用全屏按钮
    function findAlternativeFullscreenButton() {
        return document.querySelector('.bpx-player-ctrl-web');
    }

    // 设置临时按钮观察器
    function setupTemporaryButtonObserver(container) {
        const tempObserver = new MutationObserver((_, obs) => {
            const btn = getFullscreenButton() || findAlternativeFullscreenButton();
            if (btn) {
                obs.disconnect();
                triggerFullscreen(btn);
            }
        });
        tempObserver.observe(container, { childList: true, subtree: true });
    }

    // 派发鼠标事件
    function dispatchMouseEvent(element, type, x, y) {
        element.dispatchEvent(new MouseEvent(type, {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y
        }));
    }

    // 启动脚本
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
