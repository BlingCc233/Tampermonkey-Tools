#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from urllib.parse import urlparse, unquote

def parse_socks_link_for_surge(line_number, link_string):
    """
    解析单条SOCKS链接字符串并转换为Surge代理行字符串和代理名称。
    返回 (proxy_name, proxy_line_string) 或 None。
    """
    try:
        parsed_url = urlparse(link_string)

        if parsed_url.scheme not in ['socks', 'socks5']:
            print(f"警告: 第 {line_number} 行: 无效的协议 '{parsed_url.scheme}' 于链接: {link_string}。已跳过。", file=sys.stderr)
            return None, None

        if not parsed_url.hostname or not parsed_url.port:
            print(f"警告: 第 {line_number} 行: 链接中缺少主机名或端口: {link_string}。已跳过。", file=sys.stderr)
            return None, None

        proxy_name_unescaped = unquote(parsed_url.fragment) if parsed_url.fragment else f"SOCKS_{parsed_url.hostname}_{parsed_url.port}"
        # Surge 代理名称中不应包含某些特殊字符，这里简单替换空格为下划线，可以根据需要扩展
        proxy_name = proxy_name_unescaped.replace(" ", "_")


        # Surge SOCKS5 代理行格式:
        # ProxyName = socks5, server, port, username=user, password=pass, udp-relay=true
        # ProxyName = socks5, server, port, udp-relay=true (无认证)
        
        proxy_line_parts = [
            f"{proxy_name} = socks5",
            parsed_url.hostname,
            str(parsed_url.port)
        ]

        username = parsed_url.username
        password = parsed_url.password

        auth_added = False
        if username and password:
            proxy_line_parts.append(f"username={username}")
            proxy_line_parts.append(f"password={password}")
            auth_added = True
        elif username: # 如 socks://Og%3D%3D@...
            proxy_line_parts.append(f"password={username}") # 假设单个凭证是密码
            auth_added = True
        elif password:
            proxy_line_parts.append(f"password={password}")
            auth_added = True
        
        proxy_line_parts.append("udp-relay=true") # 默认启用 UDP 转发

        return proxy_name, ", ".join(proxy_line_parts)

    except Exception as e:
        print(f"警告: 第 {line_number} 行: 解析链接 '{link_string}' 时发生错误: {e}。已跳过。", file=sys.stderr)
        return None, None

def main():
    parser = argparse.ArgumentParser(description="将TXT文件中的SOCKS链接转换为Surge .conf配置。")
    parser.add_argument("input_file", help="包含SOCKS链接的TXT文件路径 (每行一个链接)。")
    parser.add_argument("-o", "--output-file", help="保存生成的Surge .conf文件的路径。如果未提供，则打印到标准输出。")

    args = parser.parse_args()

    proxy_lines = []
    proxy_names_for_group = [] # 用于[Proxy Group]

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                name, proxy_str = parse_socks_link_for_surge(i + 1, line)
                if name and proxy_str:
                    # 处理潜在的重名节点
                    original_name = name
                    name_to_check = original_name
                    count = 1
                    while name_to_check in proxy_names_for_group:
                        count += 1
                        name_to_check = f"{original_name}_{count}"
                    
                    if name_to_check != original_name:
                        print(f"警告: 第 {i+1} 行: 代理名称 '{original_name}' 重复。已重命名为 '{name_to_check}'。", file=sys.stderr)
                        # 需要重新生成 proxy_str 因为名称变了
                        _, proxy_str = parse_socks_link_for_surge(i + 1, line.replace(f"#{original_name}", f"#{name_to_check}", 1) if original_name in line else line)
                        if not proxy_str: # 如果重解析失败，跳过
                            print(f"警告: 第 {i+1} 行: 重命名后重新解析代理失败。已跳过。", file=sys.stderr)
                            continue
                        name = name_to_check # 更新名称

                    proxy_lines.append(proxy_str)
                    proxy_names_for_group.append(name)


    except FileNotFoundError:
        print(f"错误: 输入文件 '{args.input_file}' 未找到。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取或处理文件 '{args.input_file}' 时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

    if not proxy_lines:
        print("输入文件中未找到有效的SOCKS链接。未生成Surge配置。", file=sys.stderr)
        sys.exit(0)

    # 构建Surge配置文本
    config_parts = []

    # [General]
    config_parts.append("[General]")
    config_parts.append("loglevel = notify")
    config_parts.append("dns-server = system, 223.5.5.5, 119.29.29.29, 1.1.1.1") # 添加 system DNS 和一些公共DNS
    config_parts.append("skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com")
    config_parts.append("bypass-tun = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12")
    config_parts.append("external-controller-access = admin@0.0.0.0:6170") # 示例，按需修改密码和端口
    config_parts.append("show-error-page-for-reject = true")
    config_parts.append("http-listen = 0.0.0.0:6152") # HTTP代理端口
    config_parts.append("socks5-listen = 0.0.0.0:6153") # SOCKS5代理端口
    config_parts.append("always-real-ip = *.apple.com, *.icloud.com") # 示例
    config_parts.append("") # 空行分隔

    # [Replica] (可选，如果需要同步设备间的配置)
    # config_parts.append("[Replica]")
    # config_parts.append("device_id = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx") # 替换为你的设备ID
    # config_parts.append("icloud_container_enabled = true")
    # config_parts.append("")

    # [Proxy]
    config_parts.append("[Proxy]")
    config_parts.extend(proxy_lines)
    config_parts.append("") # 空行分隔

    # [Proxy Group]
    config_parts.append("[Proxy Group]")
    select_group_proxies = ", ".join(proxy_names_for_group + ["DIRECT"])
    config_parts.append(f"PROXY_SELECT = select, {select_group_proxies}")
    # 可以添加一个 URL-Test 组作为示例
    # url_test_proxies = ", ".join(proxy_names_for_group)
    # if url_test_proxies: # 确保有代理才创建
    #     config_parts.append(f"AUTO_SPEED_TEST = url-test, {url_test_proxies}, url = http://www.gstatic.com/generate_204, interval = 300, tolerance = 100")
    config_parts.append("") # 空行分隔

    # [Rule]
    config_parts.append("[Rule]")
    config_parts.append("# Localhost & LAN")
    config_parts.append("DOMAIN-SUFFIX,local,DIRECT")
    config_parts.append("IP-CIDR,127.0.0.1/32,DIRECT") # 更精确的 localhost
    config_parts.append("IP-CIDR,192.168.0.0/16,DIRECT")
    config_parts.append("IP-CIDR,10.0.0.0/8,DIRECT")
    config_parts.append("IP-CIDR,172.16.0.0/12,DIRECT")
    config_parts.append("# Common China GeoIP Rule")
    config_parts.append("GEOIP,CN,DIRECT")
    config_parts.append("# Common Ad Block (example, needs a ruleset)")
    config_parts.append("# RULE-SET,https://raw.githubusercontent.com/DivineEngine/Profiles/master/Surge/Ruleset/Guard/Advertising.list,REJECT")
    config_parts.append("# Final Rule")
    config_parts.append("FINAL,PROXY_SELECT") # 默认走选择的代理
    config_parts.append("")

    surge_config_output = "\n".join(config_parts)

    try:
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(surge_config_output)
            print(f"Surge 配置已成功写入到 '{args.output_file}'")
        else:
            if any(line.startswith("警告:") for line in sys.stderr.getvalue().splitlines()):
                 print("\n---\n")
            print(surge_config_output)

    except Exception as e:
        print(f"错误: 生成或写入Surge配置文件时发生错误: {e}", file=sys.stderr)
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
