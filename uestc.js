// ==UserScript==
// @name         UESTC评教
// @namespace    http://tampermonkey-check-evaIndex-button-uestc-actions
// @version      1.2.1
// @description  用法：导入油猴。进入评教页，点击右上角按钮。
// @match        https://eams.uestc.edu.cn/*
// @grant        none
// @author       BlingCc
// @license      GNU General Public License v3.0 or later

// @downloadURL https://update.greasyfork.org/scripts/468441/UESTC%E8%AF%84%E6%95%99.user.js
// @updateURL https://update.greasyfork.org/scripts/468441/UESTC%E8%AF%84%E6%95%99.meta.js
// ==/UserScript==

(function() {
    'use strict';

    const button = document.createElement('button');
    button.innerText = '点此按钮一键评教';
    button.style.position = 'fixed';
    button.style.top = '50px';
    button.style.right = '50px';
    button.addEventListener('click', () => {
        var idRegex = /^option_(\d+)_0$/;
        var inputs = document.getElementsByTagName('input');

        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            
            if (input.id && idRegex.test(input.id)) {
                
                var num = idRegex.exec(input.id)[1];
                
                if (num >= 0 && num <= 100) {  // 这里可以根据你的具体条件进行修改
                    input.checked = true;
                }
            }
        }
        
        const checkboxes = document.querySelectorAll('input[type="checkbox"][id="evaIndex"]');
        checkboxes.forEach((checkbox) => {
            checkbox.checked = true;
        });



        const inputBox = document.querySelector('textarea[id="evaText"]');
        var fourthTdContent = document.querySelector('body > div#BodyBg > div#MainBody.bg1 > div#main.ajax_container > form > table.infoTitle2 > tbody > tr:nth-child(2) > td:nth-child(4)').textContent;
        if (inputBox) {
            const randomNumber = Math.floor(Math.random() * 301);
            inputBox.value = '我认为'+fourthTdContent.toString()+'老师讲的好得很，认真学习就能……' + randomNumber.toString();
        }

        var submitButton = document.getElementById('sub');
        if (submitButton) {
            submitButton.click();
        }
    });

    document.body.appendChild(button);
})();

/*
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
    */

/*
button.addEventListener('click', () => {
  function simulateMouseEvent(element, eventType, x, y) {
    var event = new MouseEvent(eventType, {
      bubbles: true,
      cancelable: true,
      clientX: x,
      clientY: y
    });
    element.dispatchEvent(event);
  }

  function clickFifthLi(num) {
    var tdId = "starTd_" + num;
    var tdElement = document.getElementById(tdId);
    if (tdElement) {
      var ulElement = tdElement.querySelector("ul");
      var liElements = ulElement.querySelectorAll("li");
      if (liElements.length >= 5) {
        var fifthLiElement = liElements[4];
        var rect = fifthLiElement.getBoundingClientRect();
        var x = rect.left + rect.width / 2;
        var y = rect.top + rect.height / 2;
        simulateMouseEvent(fifthLiElement, 'mouseenter', x, y);
        simulateMouseEvent(fifthLiElement, 'click', x, y);
        simulateMouseEvent(fifthLiElement, 'mouseleave', x, y);
      }
    }
  }

  // 循环调用 clickFifthLi 函数，num 从 0 到 10
  for (var num = 0; num <= 10; num++) {
    clickFifthLi(num);
  }
});

*/
