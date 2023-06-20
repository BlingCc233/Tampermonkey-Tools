// ==UserScript==
// @name         UESTC评教
// @namespace    http://tampermonkey-check-evaIndex-button-uestc-actions
// @version      1.1.2
// @description  用法：导入油猴。进入评教页，点击右上角按钮。
// @match        http://eams.uestc/*
// @grant        none
// @author       BlingCc
// @license      GNU General Public License v3.0 or later

// ==/UserScript==

(function() {
    'use strict';

    const button = document.createElement('button');
    button.innerText = '点此按钮一键评教';
    button.style.position = 'fixed';
    button.style.top = '50px';
    button.style.right = '50px';
    button.addEventListener('click', () => {
        // Check all checkboxes with ID "evaIndex"
        const checkboxes = document.querySelectorAll('input[type="checkbox"][id="evaIndex"]');
        checkboxes.forEach((checkbox) => {
            checkbox.checked = true;
        });

        // Click the fifth li element in all ul elements inside td elements whose ID matches the pattern "starTd_数字"
        const tdElements = document.querySelectorAll('td[id^="starTd_"]');
        tdElements.forEach((td) => {
            const ulElements = td.querySelectorAll('ul');
            ulElements.forEach((ul) => {
                const liElements = ul.querySelectorAll('li');

                const li5 = liElements[4]
                var rect = li5.getBoundingClientRect();
                var x = rect.left + (rect.width / 2);
                var y = rect.top + (rect.height / 2);

                var event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y
                });
                setTimeout(function() {
                    li5.dispatchEvent(event);
                }, 0);

                if (liElements.length >= 5) {
                    liElements[4].click();
                }
            });
        });

        // Fill in the input box with ID "evaText" with a random number
        const inputBox = document.querySelector('textarea[id="evaText"]');
        if (inputBox) {
            const randomNumber = Math.floor(Math.random() * 301);
            inputBox.value = '我认为老师讲的好得很，认真学习就能……' + randomNumber.toString();
        }
    });

    document.body.appendChild(button);
})();
