// ==UserScript==
// @name               skip youtube ad
// @name:zh-CN         youtube跳过广告
// @namespace          vince.youtube
// @version            1.0.0
// @description        hide youtube's ad,auto click "skip ad"
// @description:zh-CN  自动点击"skip ad"
// @author             vince ding
// @match        https://*.youtube.com/*
// @grant        none
// @author       BlingCc
// @license      GNU General Public License v3.0 or later
// ==/UserScript==

(function() {
    'use strict';
    
    var skipInt;
    var log=function(msg){};
    var skipAd=function(){
        var skipbtn=document.querySelector(".ytp-ad-skip-button-modern.ytp-button")||document.querySelector(".videoAdUiSkipButton ");
        if(skipbtn){
           skipbtn=document.querySelector(".ytp-ad-skip-button-modern.ytp-button")||document.querySelector(".videoAdUiSkipButton ");
           log("skip");
           skipbtn.click();
           if(skipInt) {clearTimeout(skipInt);}
           skipInt=setTimeout(skipAd,500);
         }else{
              log("checking...");
              if(skipInt) {clearTimeout(skipInt);}
              skipInt=setTimeout(skipAd,500);
         }
    };

    skipAd();

})();
