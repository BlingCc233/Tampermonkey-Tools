// ==UserScript==
// @name         4虎·四虎·4hu TV去广告
// @version      1.2
// @description  Removes the midBox div tag and any element with id starting with 'content_' on 4hu TV after page load
// @match        https://4hu.tv/*
// @author       BlingCc
// @license      MIT
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    window.addEventListener('load', function() {
        // Remove midBox
        var midBox = document.getElementById('midBox');
        if (midBox) {
            midBox.remove();
        }

        // Remove elements with id starting with 'content_'
        var contentElements = document.querySelectorAll('[id^="content_"]');
        contentElements.forEach(function(element) {
            element.remove();
        });
    });
})();
