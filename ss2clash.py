#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from urllib.parse import urlparse, unquote
import yaml  # 需要安装 PyYAML: pip install PyYAML

def parse_socks_link(line_number, link_string):
    """
    解析单条SOCKS链接字符串并转换为Clash代理字典。
    """
    try:
        parsed_url = urlparse(link_string)

        if parsed_url.scheme not in ['socks', 'socks5']:
            print(f"警告: 第 {line_number} 行: 无效的协议 '{parsed_url.scheme}' 于链接: {link_string}。已跳过。", file=sys.stderr)
            return None

        if not parsed_url.hostname or not parsed_url.port:
            print(f"警告: 第 {line_number} 行: 链接中缺少主机名或端口: {link_string}。已跳过。", file=sys.stderr)
            return None

        # 从 fragment 获取代理名称，如果为空则自动生成
        proxy_name = unquote(parsed_url.fragment) if parsed_url.fragment else f"SOCKS_{parsed_url.hostname}_{parsed_url.port}"

        clash_proxy = {
            'name': proxy_name,
            'type': 'socks5',  # Clash 中 SOCKS 代理统一为 socks5 类型
            'server': parsed_url.hostname,
            'port': parsed_url.port,
            'udp': True  # SOCKS5 代理通常建议开启 UDP转发
        }

        # 处理认证信息
        # urllib.parse 会自动解码 netloc 中的 username 和 password
        # 格式 user:pass@host -> username='user', password='pass'
        # 格式 user@host (或如示例中的 credential@host) -> username='user', password=None
        # 格式 :pass@host -> username='', password='pass'
        
        username = parsed_url.username
        password = parsed_url.password


        
        return clash_proxy

    except Exception as e:
        print(f"警告: 第 {line_number} 行: 解析链接 '{link_string}' 时发生错误: {e}。已跳过。", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="将TXT文件中的SOCKS链接转换为Clash YAML配置。")
    parser.add_argument("input_file", help="包含SOCKS链接的TXT文件路径 (每行一个链接)。")
    parser.add_argument("-o", "--output-file", help="保存生成的Clash YAML文件的路径。如果未提供，则打印到标准输出。")

    args = parser.parse_args()

    proxies_list = []
    proxy_names = [] # 用于检查重名

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):  # 跳过空行和注释行
                    continue
                
                proxy_config = parse_socks_link(i + 1, line)
                if proxy_config:
                    # 处理潜在的重名节点
                    original_name = proxy_config['name']
                    name_to_check = original_name
                    count = 1
                    while name_to_check in proxy_names:
                        count += 1
                        name_to_check = f"{original_name}_{count}"
                    
                    if name_to_check != original_name:
                        print(f"警告: 第 {i+1} 行: 代理名称 '{original_name}' 重复。已重命名为 '{name_to_check}'。", file=sys.stderr)
                        proxy_config['name'] = name_to_check
                    
                    proxies_list.append(proxy_config)
                    proxy_names.append(proxy_config['name'])

    except FileNotFoundError:
        print(f"错误: 输入文件 '{args.input_file}' 未找到。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取或处理文件 '{args.input_file}' 时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

    if not proxies_list:
        print("输入文件中未找到有效的SOCKS链接。未生成Clash配置。", file=sys.stderr)
        sys.exit(0)

    # 基础Clash配置结构
    clash_config = {
        'mixed-port': 7893,  # 混合端口，可同时处理 HTTP 和 SOCKS5 请求
        'allow-lan': True,   # 允许来自局域网的连接
        'bind-address': '*', # 监听所有网络接口的连接
        'mode': 'rule',      # 可选: rule, global, direct
        'log-level': 'info', # 可选: silent, error, warning, info, debug
        'external-controller': '0.0.0.0:9090', # Clash API 和 Web UI 的监听地址
        # 'external-ui': 'path/to/dashboard', # 可指定本地 Dashboard 路径，或使用 CDN
        'external-ui': "https://cdn.jsdelivr.net/gh/MetaCubeX/yacd-gh-pages@gh-pages", # YACD Dashboard CDN
        # 'secret': '', # API 访问密钥 (可选)
        
        'dns': {
            'enable': True,
            'listen': '0.0.0.0:5353', # DNS 监听地址，使用非标准端口避免与系统DNS冲突
            'default-nameserver': [   # 用于解析国内域名或直连域名
                '223.5.5.5',      # AliDNS
                '119.29.29.29',   # DNSPod
                '114.114.114.114' # 114DNS
            ],
            'nameserver': [           # 主要的境外DNS服务器，推荐 DoH/DoT
                'https://doh.pub/dns-query',
                'https://dns.alidns.com/dns-query' # AliDNS DoH
            ],
            'fallback': [             # 当 nameserver 解析失败或超时时使用的备用DNS
                'tls://1.1.1.1:853',  # Cloudflare DoT
                'tls://8.8.4.4:853'   # Google DoT
            ],
            'fallback-filter': {      # fallback DNS 使用策略
                'geoip': True,
                'geoip-code': 'CN',   # 如果解析结果IP地理位置为中国，则不使用 fallback DNS
                # 'ipcidr': ['240.0.0.0/4'] # 过滤特定IP段不使用 fallback (可选)
            },
            'enhanced-mode': 'fake-ip', # 可选: fake-ip, redir-host
            'fake-ip-range': '198.18.0.1/16', # Fake IP 地址池
            'ipv6': False, # 是否启用 IPv6 DNS 解析 (如果网络不支持IPv6，建议关闭)
        },

        'proxies': proxies_list,

        'proxy-groups': [
            {
                'name': 'PROXY_SELECT',  # 主要的代理选择组
                'type': 'select',        # 手动选择代理
                'proxies': proxy_names + ['DIRECT'] # 包含所有导入的代理和直连选项
            },
            # 可以根据需要添加更多代理组，例如 URL-Test 自动测速组
            # {
            #     'name': 'AUTO_SPEED_TEST',
            #     'type': 'url-test',
            #     'proxies': proxy_names, # 仅对导入的代理进行测速
            #     'url': 'http://www.gstatic.com/generate_204', # 测速URL
            #     'interval': 300 # 测速间隔 (秒)
            # }
        ],

        'rules': [ # 规则顺序非常重要
            'DOMAIN-SUFFIX,internal.lan,DIRECT', # 局域网域名
            'DOMAIN-SUFFIX,localhost,DIRECT',    # 本地主机
            'IP-CIDR,127.0.0.0/8,DIRECT',        # 本地回环地址
            'IP-CIDR,10.0.0.0/8,DIRECT',         # A类私有地址
            'IP-CIDR,172.16.0.0/12,DIRECT',      # B类私有地址
            'IP-CIDR,192.168.0.0/16,DIRECT',     # C类私有地址
            'IP-CIDR,198.18.0.0/16,DIRECT',      # Fake IP 地址段直连
            'GEOIP,CN,DIRECT',                   # 中国大陆IP直连
            'MATCH,PROXY_SELECT'                 # 其他所有流量走 PROXY_SELECT 组
        ]
    }

    try:
        # 配置 yaml.dump 以获得更美观的输出
        # sort_keys=False 保持字典的插入顺序 (Python 3.7+)
        # allow_unicode=True 支持中文等非ASCII字符
        # default_flow_style=False 使用块状样式而不是流式样式
        # indent=2 设置缩进
        yaml_output = yaml.dump(clash_config, 
                                sort_keys=False, 
                                allow_unicode=True, 
                                default_flow_style=False, 
                                indent=2,
                                width=1000) # 较大的宽度避免不必要的换行
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(yaml_output)
            print(f"Clash 配置已成功写入到 '{args.output_file}'")
        else:
            # 在YAML字符串前添加一个空行，使其与可能的警告信息分开
            if any(line.startswith("警告:") for line in sys.stderr.getvalue().splitlines()):
                 print("\n---\n") # 分隔符
            print(yaml_output)

    except Exception as e:
        print(f"错误: 生成或写入YAML时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # 捕获stderr用于检查是否有警告信息打印
    import io
    old_stderr = sys.stderr
    sys.stderr = captured_stderr = io.StringIO()
    
    main()
    
    # 恢复stderr并将捕获的内容打印到实际的stderr
    sys.stderr = old_stderr
    captured_output = captured_stderr.getvalue()
    if captured_output:
        print(captured_output, file=sys.stderr, end='') # end='' 避免重复换行
    captured_stderr.close()
