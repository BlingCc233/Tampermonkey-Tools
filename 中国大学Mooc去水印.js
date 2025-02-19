// ==UserScript==
// @name         Remove Water Content (Interval)
// @namespace    http://www.icourse163.org
// @version      1.0
// @description  Remove the water content from www.icourse163.org every 10 seconds
// @author       Cc
// @match        https://www.icourse163.org/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function removeWaterContent() {
        var waterContent = document.getElementById("waterContent");
        if (waterContent) {
            waterContent.remove();
        }
    }

    // 每隔10秒钟执行一次删除操作
    setInterval(removeWaterContent, 10000);
})();
