#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import json # 用于生成 JSON 配置
from urllib.parse import urlparse, unquote

def parse_socks_link_for_singbox(line_number, link_string):
    """
    解析单条SOCKS链接字符串并转换为Sing-box出站字典。
    """
    try:
        parsed_url = urlparse(link_string)

        if parsed_url.scheme not in ['socks', 'socks5']:
            print(f"警告: 第 {line_number} 行: 无效的协议 '{parsed_url.scheme}' 于链接: {link_string}。已跳过。", file=sys.stderr)
            return None

        if not parsed_url.hostname or not parsed_url.port:
            print(f"警告: 第 {line_number} 行: 链接中缺少主机名或端口: {link_string}。已跳过。", file=sys.stderr)
            return None

        # 从 fragment 获取代理标签 (tag)，如果为空则自动生成
        proxy_tag = unquote(parsed_url.fragment) if parsed_url.fragment else f"SOCKS_{parsed_url.hostname}_{parsed_url.port}"

        singbox_outbound = {
            'tag': proxy_tag,
            'type': 'socks', # Sing-box 中 SOCKS 代理类型为 'socks' (通常指SOCKS5)
            'server': parsed_url.hostname,
            'server_port': parsed_url.port,
            # Sing-box 的 'socks' 类型出站默认支持 UDP (如果服务器支持)
            # 'udp_over_tcp': False, # 可以显式设置，但通常不需要
        }

        username = parsed_url.username
        password = parsed_url.password

        if username and password:
            singbox_outbound['username'] = username
            singbox_outbound['password'] = password
        elif username: # 如 socks://Og%3D%3D@...
            singbox_outbound['password'] = username
        elif password:
            singbox_outbound['password'] = password
        
        return singbox_outbound

    except Exception as e:
        print(f"警告: 第 {line_number} 行: 解析链接 '{link_string}' 时发生错误: {e}。已跳过。", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="将TXT文件中的SOCKS链接转换为Sing-box JSON配置。")
    parser.add_argument("input_file", help="包含SOCKS链接的TXT文件路径 (每行一个链接)。")
    parser.add_argument("-o", "--output-file", help="保存生成的Sing-box JSON文件的路径。如果未提供，则打印到标准输出。")

    args = parser.parse_args()

    proxies_list = []
    proxy_tags = [] # 用于检查重名

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                proxy_config = parse_socks_link_for_singbox(i + 1, line)
                if proxy_config:
                    original_tag = proxy_config['tag']
                    tag_to_check = original_tag
                    count = 1
                    while tag_to_check in proxy_tags:
                        count += 1
                        tag_to_check = f"{original_tag}_{count}"
                    
                    if tag_to_check != original_tag:
                        print(f"警告: 第 {i+1} 行: 代理标签 '{original_tag}' 重复。已重命名为 '{tag_to_check}'。", file=sys.stderr)
                        proxy_config['tag'] = tag_to_check
                    
                    proxies_list.append(proxy_config)
                    proxy_tags.append(proxy_config['tag'])

    except FileNotFoundError:
        print(f"错误: 输入文件 '{args.input_file}' 未找到。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取或处理文件 '{args.input_file}' 时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

    if not proxies_list:
        print("输入文件中未找到有效的SOCKS链接。未生成Sing-box配置。", file=sys.stderr)
        sys.exit(0)

    # 基础Sing-box配置结构
    singbox_config = {
        "log": {
            "level": "info",
            "timestamp": True
        },
        "dns": {
            "servers": [
                {"address": "223.5.5.5", "tag": "dns_alidns"},      # AliDNS
                {"address": "119.29.29.29", "tag": "dns_dnspod"},  # DNSPod
                {"address": "https://doh.pub/dns-query", "tag": "dns_doh_pub"}, # DoH
                {"address": "tls://1.1.1.1:853", "tag": "dns_cloudflare_dot"} # Cloudflare DoT
            ],
            "strategy": "prefer_ipv4", # 可选: prefer_ipv4, prefer_ipv6, ipv4_only, ipv6_only
            "independent_cache": True,
        },
        "inbounds": [
            {
                "type": "mixed", # 混合入站，可同时处理 HTTP 和 SOCKS
                "tag": "mixed-in",
                "listen": "0.0.0.0",
                "listen_port": 7893, # 与Clash示例保持一致的端口
                "sniff": True # 启用流量嗅探
            }
        ],
        "outbounds": proxies_list + [ # 添加转换后的SOCKS代理
            {
                "tag": "PROXY_SELECT",
                "type": "selector",
                "outbounds": proxy_tags + ["direct"], # 包含所有导入的代理标签和 "direct"
                "default": proxy_tags[0] if proxy_tags else "direct" # 设置一个默认出站
            },
            {
                "tag": "direct", # 内建直连出站
                "type": "direct"
            },
            {
                "tag": "block", # 内建阻止连接出站
                "type": "block"
            }
        ],
        "route": {
            "rules": [
                {
                    "protocol": ["dns"], # DNS查询直接由Sing-box处理
                    "outbound": "dns_alidns" # 或者你配置的任何DNS tag
                },
                {
                    "ip_cidr": [ # 常见私有地址段
                        "127.0.0.0/8",
                        "10.0.0.0/8",
                        "172.16.0.0/12",
                        "192.168.0.0/16",
                        "fc00::/7" # IPv6 ULA
                    ],
                    "outbound": "direct"
                },
                {
                    "geoip": ["cn", "private"], # 中国大陆IP和私有IP直连
                    "outbound": "direct"
                },
                {
                    "geosite": ["cn"], # 中国大陆常用域名直连
                    "outbound": "direct"
                }
                # 可以根据需要添加更多规则
            ],
            "final": "PROXY_SELECT", # 默认规则，匹配所有其他流量
            "auto_detect_interface": True
        }
    }

    try:
        json_output = json.dumps(singbox_config, indent=2, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(json_output)
            print(f"Sing-box 配置已成功写入到 '{args.output_file}'")
        else:
            if any(line.startswith("警告:") for line in sys.stderr.getvalue().splitlines()):
                 print("\n---\n")
            print(json_output)

    except Exception as e:
        print(f"错误: 生成或写入JSON时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    import io
    old_stderr = sys.stderr
    sys.stderr = captured_stderr = io.StringIO()
    
    main()
    
    sys.stderr = old_stderr
    captured_output = captured_stderr.getvalue()
    if captured_output:
        print(captured_output, file=sys.stderr, end='')
    captured_stderr.close()
