// ==UserScript==
// @name        YouTube Live minimum latency
// @name:zh-CN  YouTube 直播最低延迟
// @description YouTube Live の遅延を自動的に最小化します
// @description:zh-CN 自动最小化 YouTube 直播的延迟。
// @namespace   BlingCc
// @version     0.2.3
// @author      Sigsign
// @license     MIT or Apache-2.0
// @match       https://www.youtube.com/*
// @run-at      document-start
// @noframes
// @grant       none
// @downloadURL https://update.greasyfork.org/scripts/427483/YouTube%20Live%20minimum%20latency.user.js
// @updateURL https://update.greasyfork.org/scripts/427483/YouTube%20Live%20minimum%20latency.meta.js
// ==/UserScript==
(function () {
'use strict'; // 启用严格模式，让代码更规范

/**
 * 注册一个在页面加载或切换完成后执行的函数
 * @param {function} fn - 页面加载完成后要执行的回调函数
 */
function loadPage(fn) {
    /**
    * 因为 YouTube 是一个单页应用 (SPA)，仅使用 'load' 事件无法捕捉到页面内部的跳转。
    * 需要使用 'yt-navigate-finish' 这个 YouTube 自定义的事件来确保每次页面切换后脚本都能正确执行。
    *
    * 参考: https://stackoverflow.com/questions/24297929/
    */
    document.addEventListener('yt-navigate-finish', fn, false);
}

/**
 * 获取 YouTube 播放器对象
 * @returns {Element | null} 播放器元素
 */
function getPlayer() {
    return document.querySelector('#movie_player');
}

/**
 * 获取当前直播的延迟时间（秒）
 * @param {object} player - 播放器对象
 * @returns {number} 延迟秒数
 */
function getLiveLatency(player) {
    const current = Date.now() / 1000; // 获取当前时间的 Unix 时间戳（秒）
    const time = player.getMediaReferenceTime(); // 获取播放器媒体的参考时间（直播流的当前时间点）
    return time ? current - time : 0; // 两者之差即为延迟
}

/**
 * 获取视频缓冲区的健康度（已缓冲的秒数）
 * @param {object} player - 播放器对象
 * @returns {number} 缓冲区秒数
 */
function getBufferHealth(player) {
    const stats = player.getVideoStats(); // 获取视频的详细统计信息
    if (!stats) {
        return 0;
    }
    const bufferRange = stats.vbu; // vbu 包含了缓冲区的起止时间
    if (!bufferRange) {
        return 0;
    }
    const buffer = bufferRange.split('-'); // 分割字符串以获取结束时间
    if (buffer.length < 2) {
        return 0;
    }
    const bufferTime = Number(buffer.slice(-1)[0]); // 获取缓冲区的结束时间点
    const currentTime = Number(stats.vct); // vct 是视频的当前播放时间点
    if (isNaN(bufferTime) || isNaN(currentTime)) {
        return 0;
    }
    return bufferTime - currentTime; // 缓冲结束时间减去当前播放时间，即为剩余的缓冲区时长
}

// 定义不同直播模式下的延迟和缓冲区阈值
const thresholds = {
    NORMAL: {     // 普通延迟模式
        latency: 10.0, // 延迟超过 10 秒
        buffer: 2.0,   // 且缓冲区大于 2 秒时，开始加速
    },
    LOW: {        // 低延迟模式
        latency: 5.0,  // 延迟超过 5 秒
        buffer: 1.5,   // 且缓冲区大于 1.5 秒时，开始加速
    },
    ULTRALOW: {   // 超低延迟模式
        latency: 2.0,  // 延迟超过 2 秒
        buffer: 1.0,   // 且缓冲区大于 1 秒时，开始加速
    },
};

/**
 * 根据键名获取对应的阈值对象
 * @param {string} key - 延迟模式的键名 ('NORMAL', 'LOW', 'ULTRALOW')
 * @returns {object | null}
 */
function getThresold(key) {
    if (typeof key !== 'string') {
        return null;
    }
    return key in thresholds ? thresholds[key] : null;
}

// 当页面导航完成后执行核心逻辑
loadPage(() => {
    const player = getPlayer(); // 获取播放器
    if (!player) {
        return; // 如果没有播放器，则不执行任何操作
    }
    const stats = player.getVideoStats() || {};
    // 如果不是直播(live)、可回放直播(dvr)或首播(lp)，则退出
    if (stats.live !== 'live' && stats.live !== 'dvr' && stats.live !== 'lp') {
        return;
    }
    const availableRates = player.getAvailablePlaybackRates() || [];
    // 如果播放器不支持 1.25 倍速，则无法通过加速来追赶延迟，直接退出
    if (!availableRates.includes(1.25)) {
        return;
    }
    const video = document.querySelector('video'); // 获取 video 元素
    if (!video) {
        return;
    }

    // 开始加速播放的函数
    const startAcceleration = () => {
        const rate = player.getPlaybackRate();
        // 如果当前播放速率不是 1.0（例如用户手动设置了其他速率），则不干预
        if (rate !== 1.0) {
            return;
        }
        const stats = player.getVideoStats() || {};
        const latency = getLiveLatency(player);

        // 如果是可回放直播(dvr)或首播(lp)，且延迟超过2分钟（120秒）
        // 则假定是用户自己拖动了进度条，此时不进行自动调整
        if (stats.live !== 'live' && latency > 120) {
            return;
        }

        const threshold = getThresold(stats.latency_class); // 根据直播的延迟等级获取阈值
        if (!threshold) {
            return;
        }

        // 对首播(lp)进行特殊处理
        if (stats.live === 'lp') {
            // 首播本身会存在约 11 秒的固有延迟，因此将判断阈值放宽到 15 秒
            threshold.latency = 15;
        }

        const buffer = getBufferHealth(player);
        // 当缓冲区和延迟都超过设定的阈值时，执行加速
        if (buffer > threshold.buffer && latency > threshold.latency) {
            player.setPlaybackRate(1.25); // 将播放速度设为 1.25 倍
            setTimeout(stopAcceleration, 50); // 50毫秒后检查是否需要停止加速
        }
    };

    // 停止加速播放的函数
    const stopAcceleration = () => {
        const rate = player.getPlaybackRate();
        // 如果播放速率不是 1.25 倍（可能已被其他逻辑或用户改变），则退出
        if (rate !== 1.25) {
            return;
        }
        const stats = player.getVideoStats() || {};
        const buffer = getBufferHealth(player);
        const threshold = getThresold(stats.latency_class);
        
        // 如果获取不到阈值，或者缓冲区已经低于目标值，则停止加速
        if (!threshold || buffer < threshold.buffer) {
            player.setPlaybackRate(1.0); // 恢复正常播放速度
        }
        else {
            // 如果条件仍然满足加速，则 50 毫秒后再次检查
            setTimeout(stopAcceleration, 50);
        }
    };

    // 当视频开始播放时（例如从暂停恢复），触发一次延迟检查
    video.addEventListener('playing', startAcceleration);
    // 每隔 60 秒，定时检查一次延迟，作为一种保险机制
    const timer = setInterval(startAcceleration, 60 * 1000);

    // 清理函数：用于移除事件监听和定时器，防止内存泄漏
    const eventCleaner = () => {
        video.removeEventListener('playing', startAcceleration);
        clearInterval(timer);
    };
    // 当用户开始导航到新页面时，执行一次清理操作
    document.addEventListener('yt-navigate-start', eventCleaner, { once: true });
});

})();
