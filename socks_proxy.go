package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/schollz/progressbar/v3" // 导入进度条库
	"golang.org/x/net/proxy"
)

const (
	outputFileName      = "output.txt"
	defaultMaxWorkers   = 10
	httpClientTimeout   = 10 * time.Second
	socksDialTimeout    = 10 * time.Second
	socksTestTargetAddr = "google.com:80"
)

type ConfigResponse struct {
	AllowLan  bool   `json:"allow-lan"`
	SocksPort int    `json:"socks-port"`
	MixedPort int    `json:"mixed-port"`
	Port      int    `json:"port"`
}

type PatchPayload struct {
	AllowLan bool `json:"allow-lan"`
}

type Task struct {
	IP   string
	Port string
	City string
}

var (
	nameCounts = make(map[string]int)
	nameMutex  = &sync.Mutex{}
	outputFile *os.File
	outputLock = &sync.Mutex{}
	httpClient = &http.Client{
		Timeout: httpClientTimeout,
	}
)

func getUniqueName(baseName string) string {
	nameMutex.Lock()
	defer nameMutex.Unlock()
	count, exists := nameCounts[baseName]
	if !exists {
		nameCounts[baseName] = 0
		return baseName
	}
	count++
	nameCounts[baseName] = count
	return fmt.Sprintf("%s%d", baseName, count)
}

// processRow 现在接收一个 progressbar.ProgressBar 指针
func processRow(task Task, wg *sync.WaitGroup, bar *progressbar.ProgressBar) {
	defer func() {
		if bar != nil { // 安全检查，尽管在这里它总会被传递
			bar.Add(1) // 每处理完一个任务，进度条增加1
		}
		wg.Done()
	}()

	log.Printf("处理: IP=%s, Port=%s, City=%s\n", task.IP, task.Port, task.City)

	configsURL := fmt.Sprintf("http://%s:%s/configs", task.IP, task.Port)
	req, err := http.NewRequest("GET", configsURL, nil)
	if err != nil {
		log.Printf("错误: 无法创建GET请求 %s: %v\n", configsURL, err)
		return
	}

	resp, err := httpClient.Do(req)
	if err != nil {
		log.Printf("错误: GET %s 失败: %v\n", configsURL, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		log.Printf("错误: GET %s 返回状态码 %d, Body: %s\n", configsURL, resp.StatusCode, string(bodyBytes))
		return
	}

	var configData ConfigResponse
	if err := json.NewDecoder(resp.Body).Decode(&configData); err != nil {
		log.Printf("错误: 解析 %s 的JSON响应失败: %v\n", configsURL, err)
		return
	}

	log.Printf("信息: %s:%s - 初始 allow-lan: %v, socks-port: %d, mixed-port: %d\n", task.IP, task.Port, configData.AllowLan, configData.SocksPort, configData.MixedPort)

	if !configData.AllowLan {
		log.Printf("信息: %s:%s - allow-lan 为 false, 尝试 PATCH...\n", task.IP, task.Port)
		patchPayload := PatchPayload{AllowLan: true}
		payloadBytes, err := json.Marshal(patchPayload)
		if err != nil {
			log.Printf("错误: 序列化PATCH payload失败 %s: %v\n", configsURL, err)
			return
		}

		patchReq, err := http.NewRequest("PATCH", configsURL, bytes.NewBuffer(payloadBytes))
		if err != nil {
			log.Printf("错误: 无法创建PATCH请求 %s: %v\n", configsURL, err)
			return
		}
		patchReq.Header.Set("Content-Type", "application/json")

		patchResp, err := httpClient.Do(patchReq)
		if err != nil {
			log.Printf("错误: PATCH %s 失败: %v\n", configsURL, err)
			return
		}
		defer patchResp.Body.Close()

		if patchResp.StatusCode != http.StatusOK && patchResp.StatusCode != http.StatusNoContent && patchResp.StatusCode != http.StatusAccepted {
			bodyBytes, _ := io.ReadAll(patchResp.Body)
			log.Printf("错误: PATCH %s 返回状态码 %d, Body: %s\n", configsURL, patchResp.StatusCode, string(bodyBytes))
			return
		}
		log.Printf("信息: %s:%s - PATCH 成功, allow-lan 设置为 true\n", task.IP, task.Port)
		configData.AllowLan = true
	}

	socks5Port := configData.SocksPort
	if socks5Port == 0 {
		socks5Port = configData.MixedPort
	}

	if socks5Port == 0 {
		log.Printf("错误: %s:%s - 未找到有效的SOCKS端口 (socks-port: %d, mixed-port: %d)\n", task.IP, task.Port, configData.SocksPort, configData.MixedPort)
		return
	}

	log.Printf("信息: %s:%s - 使用SOCKS端口: %d\n", task.IP, task.Port, socks5Port)

	socksAddr := fmt.Sprintf("%s:%d", task.IP, socks5Port)
	dialer, err := proxy.SOCKS5("tcp", socksAddr, nil, &net.Dialer{
		Timeout:   socksDialTimeout,
		KeepAlive: 0,
	})
	if err != nil {
		log.Printf("错误: %s:%s - 创建SOCKS5拨号器失败 (%s): %v\n", task.IP, task.Port, socksAddr, err)
		return
	}

	conn, err := dialer.Dial("tcp", socksTestTargetAddr)
	if err != nil {
		log.Printf("错误: %s:%s - SOCKS5连接测试失败 (%s via %s): %v\n", task.IP, task.Port, socksTestTargetAddr, socksAddr, err)
		return
	}
	conn.Close()
	log.Printf("成功: %s:%s - SOCKS5连接测试成功 (%s via %s)\n", task.IP, task.Port, socksTestTargetAddr, socksAddr)

	uniqueCityName := getUniqueName(task.City)
	encodedCityName := url.PathEscape(uniqueCityName)
	outputLine := fmt.Sprintf("socks://Og%%3D%%3D@%s:%d#%s\n", task.IP, socks5Port, encodedCityName)

	outputLock.Lock()
	defer outputLock.Unlock()
	if _, err := outputFile.WriteString(outputLine); err != nil {
		log.Printf("错误: 写入output文件失败: %v\n", err)
	} else {
		log.Printf("写入: %s", outputLine)
	}
}

// countCsvDataRows 计算CSV文件中的数据行数（不包括表头）
// 它只计算那些可以被csv.Reader成功解析的行。
func countCsvDataRows(filePath string, header []string, ipIdx, portIdx, cityIdx int) (int, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return 0, fmt.Errorf("无法打开CSV文件进行计数 %s: %w", filePath, err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	_, err = reader.Read() // 读取并跳过表头
	if err != nil {
		if err == io.EOF {
			return 0, nil // 文件为空或只有表头
		}
		return 0, fmt.Errorf("读取CSV表头失败（计数时）: %w", err)
	}

	rowCount := 0
	lineNumber := 1 // 从数据行开始计数
	for {
		lineNumber++
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			// 如果某行解析错误，我们选择跳过它，不计入总数，
			// 因为主处理循环可能也会跳过它或因错误停止。
			// 或者，你可以选择记录一个警告并继续计数，取决于你希望进度条如何表现。
			log.Printf("警告: 计数CSV行时，第 %d 行解析错误: %v。此行将不计入进度条总数。\n", lineNumber, err)
			continue
		}

		// 应用与主处理循环中相同的基本验证逻辑
		if len(record) <= ipIdx || len(record) <= portIdx || len(record) <= cityIdx {
			// log.Printf("警告: 计数CSV行时，第 %d 行数据列数不足, 跳过计数\n", lineNumber)
			continue
		}

		ip := strings.TrimSpace(record[ipIdx])
		port := strings.TrimSpace(record[portIdx])
		city := strings.TrimSpace(record[cityIdx])

		if ip == "" || port == "" || city == "" {
			// log.Printf("警告: 计数CSV行时，第 %d 行数据不完整, 跳过计数\n", lineNumber)
			continue
		}
		rowCount++
	}
	return rowCount, nil
}

// getCsvHeaderAndIndices 读取CSV头部并返回列名到索引的映射
func getCsvHeaderAndIndices(reader *csv.Reader) ([]string, int, int, int, error) {
	header, err := reader.Read() // 读取表头
	if err != nil {
		if err == io.EOF {
			return nil, -1, -1, -1, fmt.Errorf("CSV文件为空")
		}
		return nil, -1, -1, -1, fmt.Errorf("读取CSV表头失败: %w", err)
	}

	ipIdx, portIdx, cityIdx := -1, -1, -1
	for i, colName := range header {
		trimmedName := strings.TrimSpace(strings.ToLower(colName))
		switch trimmedName {
		case "ip":
			ipIdx = i
		case "port":
			portIdx = i
		case "city":
			cityIdx = i
		}
	}

	if ipIdx == -1 || portIdx == -1 || cityIdx == -1 {
		return header, -1, -1, -1, fmt.Errorf("CSV文件中必须包含 'ip', 'port', 和 'city' 列. 找到: ipIdx=%d, portIdx=%d, cityIdx=%d", ipIdx, portIdx, cityIdx)
	}
	return header, ipIdx, portIdx, cityIdx, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Printf("用法: %s <csv_file_path> [max_workers]\n", os.Args[0])
		os.Exit(1)
	}
	csvFilePath := os.Args[1]

	maxWorkers := defaultMaxWorkers
	if len(os.Args) > 2 {
		mw, err := strconv.Atoi(os.Args[2])
		if err == nil && mw > 0 {
			maxWorkers = mw
		} else {
			log.Printf("警告: 无效的并发数 '%s', 使用默认值 %d\n", os.Args[2], defaultMaxWorkers)
		}
	}
	log.Printf("使用最大并发数: %d\n", maxWorkers)

	// 预先读取表头以获取索引，用于精确计数
	// 注意：这里我们打开文件一次获取表头，然后countCsvDataRows会再次打开。
	// 也可以传递reader给countCsvDataRows，但需要重置。简单起见，分开打开。
	tempCsvFileForHeader, err := os.Open(csvFilePath)
	if err != nil {
		log.Fatalf("错误: 无法打开CSV文件 %s 以读取表头: %v\n", csvFilePath, err)
	}
	tempReaderForHeader := csv.NewReader(tempCsvFileForHeader)
	headerForCount, ipIdxForCount, portIdxForCount, cityIdxForCount, err := getCsvHeaderAndIndices(tempReaderForHeader)
	tempCsvFileForHeader.Close() // 关闭临时文件
	if err != nil {
		log.Fatalf("错误: 解析CSV表头失败（用于计数）: %v\n", err)
	}
	
	// 计算将要处理的总任务数 (数据行数)
	totalTasks, err := countCsvDataRows(csvFilePath, headerForCount, ipIdxForCount, portIdxForCount, cityIdxForCount)
	if err != nil {
		log.Fatalf("错误: 计算CSV行数失败: %v\n", err)
	}
	if totalTasks == 0 {
		log.Println("信息: CSV文件中没有可处理的数据行。")
		return
	}
	log.Printf("信息: CSV文件 '%s' 中找到 %d 个可处理的数据行。\n", csvFilePath, totalTasks)

	// 初始化进度条
	// 将进度条输出到 os.Stderr，这样日志可以正常输出到 os.Stderr 而不会被覆盖太多
	// （log默认也输出到Stderr）
	bar := progressbar.NewOptions(totalTasks,
		progressbar.OptionSetDescription("处理CSV行..."),
		progressbar.OptionSetWriter(os.Stderr), // 确保进度条和日志输出到相同的地方，但progressbar会处理重绘
		progressbar.OptionShowCount(),
		progressbar.OptionShowIts(), // items per second
		progressbar.OptionSetElapsedTime(true),
		progressbar.OptionSetPredictTime(true),
		progressbar.OptionClearOnFinish(), // 完成后清除进度条
		progressbar.OptionEnableColorCodes(true),
		progressbar.OptionSetTheme(progressbar.Theme{
			Saucer:        "=",
			SaucerHead:    ">",
			SaucerPadding: " ",
			BarStart:      "[",
			BarEnd:        "]",
		}),
	)

	// 打开CSV文件进行实际处理
	csvFile, err := os.Open(csvFilePath)
	if err != nil {
		log.Fatalf("错误: 无法打开CSV文件 %s: %v\n", csvFilePath, err)
	}
	defer csvFile.Close()

	// 创建或打开输出文件
	outputFile, err = os.OpenFile(outputFileName, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("错误: 无法打开或创建输出文件 %s: %v\n", outputFileName, err)
	}
	defer outputFile.Close()

	reader := csv.NewReader(csvFile)
	// 读取表头并获取列索引 (这次用于实际处理)
	_, ipIdx, portIdx, cityIdx, err := getCsvHeaderAndIndices(reader)
	if err != nil {
		log.Fatalf("错误: %v\n", err)
	}

	var wg sync.WaitGroup
	taskQueue := make(chan Task, maxWorkers)

	for i := 0; i < maxWorkers; i++ {
		go func() {
			for task := range taskQueue {
				processRow(task, &wg, bar) // 将bar传递给processRow
			}
		}()
	}

	lineNumber := 1 // 行号从表头之后开始
	for {
		lineNumber++
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("错误: 读取CSV文件第 %d 行失败: %v, 跳过\n", lineNumber, err)
			// 注意：如果在这里跳过，并且countCsvDataRows也因为这个错误跳过了计数，
			// 那么进度条的总数和实际尝试的任务数仍然可能匹配。
			// 如果countCsvDataRows没有跳过，但这里跳过了，进度条可能不会达到100%。
			// 当前的countCsvDataRows会尝试跳过错误行，所以应该还好。
			continue
		}

		if len(record) <= ipIdx || len(record) <= portIdx || len(record) <= cityIdx {
			log.Printf("错误: 第 %d 行数据列数不足, 跳过 (IP列索引: %d, Port列索引: %d, City列索引: %d, 记录列数: %d)\n", lineNumber, ipIdx, portIdx, cityIdx, len(record))
			continue
		}

		ip := strings.TrimSpace(record[ipIdx])
		portStr := strings.TrimSpace(record[portIdx])
		city := strings.TrimSpace(record[cityIdx])

		if ip == "" || portStr == "" || city == "" {
			log.Printf("警告: 第 %d 行数据不完整 (IP: '%s', Port: '%s', City: '%s'), 跳过\n", lineNumber, ip, portStr, city)
			continue
		}

		// 此时，我们认为这是一个有效的任务，会计入wg
		wg.Add(1)
		taskQueue <- Task{IP: ip, Port: portStr, City: city}
	}

	close(taskQueue)
	wg.Wait()

	// 手动完成进度条，以防万一有任务被跳过，但wg.Add没有相应减少
	// （虽然在此设计中，wg.Add仅对有效任务调用，所以bar.Finish()可能非必需，
	//  但OptionClearOnFinish通常会在wg.Wait()后，所有bar.Add(1)完成后自动处理）
	// bar.Finish() // OptionClearOnFinish 应该能处理好，所以这行可以省略

	log.Println("所有任务处理完毕.")
}
