// ==UserScript==
// @name         Bilibili自动全屏脚本
// @namespace    bilibili-auto-fullscreen-script
// @version      1.2
// @description  在Bilibili网站自动全屏播放视频
// @author       BlingCc
// @match        https://www.bilibili.com/*
// @license      MIT
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    window.onload = function() {
        // 找到包含视频的div元素
        let videoWrap = document.querySelector('.bpx-player-video-area');
        if (videoWrap) {
            // 将鼠标移动到该元素中心
            let rect = videoWrap.getBoundingClientRect();
            let x = rect.left + rect.width / 2;
            let y = rect.top + rect.height / 2;
            simulateMouseEvent(videoWrap, 'mouseenter', x, y);
            simulateMouseEvent(videoWrap, 'mouseover', x, y);


        setTimeout(function() {
            // 找到全屏按钮元素
            let fullscreenButton = document.querySelector('[aria-label="网页全屏"]');
            if (fullscreenButton) {
                // 将鼠标移动到该元素上并模拟点击
                rect = fullscreenButton.getBoundingClientRect();
                x = rect.left + rect.width / 2;
                y = rect.top + rect.height / 2;
                simulateMouseEvent(fullscreenButton, 'mouseenter', x, y);
                simulateMouseEvent(fullscreenButton, 'click', x, y);
                simulateMouseEvent(fullscreenButton, 'mouseleave', x, y);
            }
            }, 1000);
            setTimeout(function() {
                let rect = videoWrap.getBoundingClientRect();
                let x = rect.left + rect.width / 2;
                let y = rect.top + rect.height / 2;
                simulateMouseEvent(videoWrap, 'mouseenter', x, y);
                simulateMouseEvent(videoWrap, 'mouseover', x, y);
            // 找到全屏按钮元素
            let fullscreenButton = document.querySelector('[aria-label="网页全屏"]');
            if (fullscreenButton) {
                // 将鼠标移动到该元素上并模拟点击
                rect = fullscreenButton.getBoundingClientRect();
                x = rect.left + rect.width / 2;
                y = rect.top + rect.height / 2;
                simulateMouseEvent(fullscreenButton, 'mouseenter', x, y);
                simulateMouseEvent(fullscreenButton, 'click', x, y);
                simulateMouseEvent(fullscreenButton, 'mouseleave', x, y);
            }
            }, 1000);
            setTimeout(function() {

                let rect = videoWrap.getBoundingClientRect();
                let x = rect.left + rect.width / 2;
                let y = rect.top + rect.height / 2;
                simulateMouseEvent(videoWrap, 'mouseenter', x, y);
                simulateMouseEvent(videoWrap, 'mouseover', x, y);
            // 找到全屏按钮元素
            let fullscreenButton = document.querySelector('[aria-label="网页全屏"]');
            if (fullscreenButton) {
                // 将鼠标移动到该元素上并模拟点击
                rect = fullscreenButton.getBoundingClientRect();
                x = rect.left + rect.width / 2;
                y = rect.top + rect.height / 2;
                simulateMouseEvent(fullscreenButton, 'mouseenter', x, y);
                simulateMouseEvent(fullscreenButton, 'click', x, y);
                simulateMouseEvent(fullscreenButton, 'mouseleave', x, y);
            }
            }, 4000);

        }
    };

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

})();
