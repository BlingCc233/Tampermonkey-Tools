package main

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
)

const (
	PartSize = 50 * 1024 * 1024
)

func splitFile(filePath string) error {
	// Convert to absolute path and get directory info
	absFilePath, err := filepath.Abs(filePath)
	if err != nil {
		return err
	}
	baseDir := filepath.Dir(absFilePath)

	// Get just the filename without path
	baseFileName := filepath.Base(absFilePath)
	fileName := strings.TrimSuffix(baseFileName, ".bin")
	if fileName == baseFileName {
		fileName = strings.TrimSuffix(fileName, ".")
	}

	file, err := os.Open(absFilePath)
	if err != nil {
		return err
	}
	defer file.Close()

	// Create split table in the same directory
	splitTablePath := filepath.Join(baseDir, fileName+".split")
	tableFile, err := os.Create(splitTablePath)
	if err != nil {
		return err
	}
	defer tableFile.Close()

	// Write only the base filename to split table
	writer := bufio.NewWriter(tableFile)
	writer.WriteString(baseFileName + "\n")

	buffer := make([]byte, PartSize)
	bytesRead := 0
	partNumber := 0

	for {
		n, err := file.Read(buffer[bytesRead:])
		if err != nil && err != io.EOF {
			return err
		}
		if n == 0 {
			if bytesRead > 0 {
				partNumber++
				partFileName := fmt.Sprintf("%s_part_%03d", fileName, partNumber)
				if err := writePartFile(baseDir, partFileName, buffer[:bytesRead], writer); err != nil {
					return err
				}
			}
			break
		}

		bytesRead += n
		if bytesRead == PartSize {
			partNumber++
			partFileName := fmt.Sprintf("%s_part_%03d", fileName, partNumber)
			if err := writePartFile(baseDir, partFileName, buffer[:bytesRead], writer); err != nil {
				return err
			}
			bytesRead = 0
		}
	}

	writer.Flush()
	return nil
}

func writePartFile(baseDir, partFileName string, data []byte, writer *bufio.Writer) error {
	fullPath := filepath.Join(baseDir, partFileName)
	partFile, err := os.Create(fullPath)
	if err != nil {
		return err
	}
	defer partFile.Close()

	partWriter := bufio.NewWriter(partFile)
	if _, err := partWriter.Write(data); err != nil {
		return err
	}
	partWriter.Flush()

	// Write only the part filename without path to split table
	writer.WriteString(partFileName + "\n")
	return nil
}

func mergeFiles(splitTablePath string) error {
	// Get the directory of the split table
	absTablePath, err := filepath.Abs(splitTablePath)
	if err != nil {
		return err
	}
	baseDir := filepath.Dir(absTablePath)

	tableFile, err := os.Open(absTablePath)
	if err != nil {
		return err
	}
	defer tableFile.Close()

	scanner := bufio.NewScanner(tableFile)
	if !scanner.Scan() {
		return fmt.Errorf("failed to read split table")
	}
	originalFileName := scanner.Text()

	// Create original file in the same directory as split table
	originalPath := filepath.Join(baseDir, originalFileName)
	originalFile, err := os.Create(originalPath)
	if err != nil {
		return err
	}
	defer originalFile.Close()

	for scanner.Scan() {
		partFileName := scanner.Text()
		// Open part file from the same directory as split table
		partPath := filepath.Join(baseDir, partFileName)
		partFile, err := os.Open(partPath)
		if err != nil {
			return err
		}

		_, err = io.Copy(originalFile, partFile)
		partFile.Close()
		if err != nil {
			return err
		}
	}

	if scanner.Err() != nil {
		return scanner.Err()
	}

	return nil
}

func main() {
	if len(os.Args) < 3 {
		log.Fatal("Usage: go run main.go -s|-m <target-file>")
	}

	mode := os.Args[1]
	targetFile := os.Args[2]

	switch mode {
	case "-s":
		err := splitFile(targetFile)
		if err != nil {
			log.Fatalf("Error splitting file: %v", err)
		}
		fmt.Printf("File '%s' has been split successfully.\n", targetFile)

	case "-m":
		err := mergeFiles(targetFile)
		if err != nil {
			log.Fatalf("Error merging files: %v", err)
		}
		fmt.Printf("Files from '%s' have been merged successfully.\n", targetFile)

	default:
		log.Fatal("Invalid mode. Use -s for split or -m for merge.")
	}
}
